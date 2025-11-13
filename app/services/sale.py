# services/sale.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime
from app.models import (
    Sale, SaleProduct, Product,
    inventory_log, transaction as transaction_model,
    JournalItems
)

from app.models.journal_entries import JournalEntry
from app.models.ledger import Ledger
from app.models.subsidiary_account import SubsidiaryAccount

from app.schemas.sale import SaleCreate
from app.schemas.payment import PaymentCreate
from app.schemas.journal_entries import LedgerWithEntryRequest
from app.schemas.journal_items import JournalItems as JournalItemSchema


class SaleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_sale(self, sale_data: SaleCreate, payment_data: PaymentCreate) -> Sale:
        try:
            sub_account_id = await self.get_subsidiary_account(sale_data.client_id)

            # Step 1: Create Sale record
            db_sale = Sale(
                user_id=sale_data.user_id,
                client_id=sale_data.client_id,
                total=sale_data.total,
                discount=sale_data.discount,
                business_id=sale_data.business_id,
                payment_status=sale_data.payment_status
            )
            self.db.add(db_sale)

            # Step 2: Bulk fetch products
            product_ids = [item.product_id for item in sale_data.sale_products]
            result = await self.db.execute(select(Product).where(Product.id.in_(product_ids)))
            products_map = {p.id: p for p in result.scalars().all()}

            sale_products = []
            inventory_logs = []

            for item in sale_data.sale_products:
                product = products_map.get(item.product_id)
                if not product:
                    raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
                if product.stock < item.quantity:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for product ID {item.product_id}")

                sale_products.append(SaleProduct(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_per_unit=item.price_per_unit,
                    total_price=item.total_price,
                    sale=db_sale
                ))

                product.stock -= item.quantity

                inventory_logs.append(inventory_log.InventoryLog(
                    product_id=item.product_id,
                    action_type='DEDUCT',
                    quantity=item.quantity,
                    user_id=sale_data.user_id
                ))

            self.db.add_all(sale_products + inventory_logs)

            # Step 3: Create Transaction
            self.db.add(transaction_model.Transaction(
                account_id=3,  # SALES_REVENUE_ID
                amount=sale_data.total,
                transaction_date=func.now(),
                description='Sale of products',
                user_id=sale_data.user_id,
                business_id=sale_data.business_id or 1,
                reference_type='sale',
                type="DEBIT",
                reference_id=db_sale.id
            ))

            # Step 4: Create Journal Entry
            journal_items = self._build_journal_items(
                payment_method=payment_data.payment_method,
                total=sale_data.total,
                amount_paid=payment_data.amount,
                sub_account_id=sub_account_id
            )

            journal_data = LedgerWithEntryRequest(
                ref_no=f"SALE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                account_type="revenue",
                company="ABC Ltd.",
                description="Sale Entry",
                user_id=sale_data.user_id,
                journal_items=journal_items
            )

            await self.create_ledger_with_entry(journal_data)

            await self.db.commit()
            await self.db.refresh(db_sale)
            return db_sale

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sale creation failed: {str(e)}"
            )


    def _build_journal_items(self, payment_method: str, total: float, amount_paid: float, sub_account_id: int) -> list[dict]:
        if payment_method == 'cash':
            if amount_paid >= total:
                return [
                    {"narration": "Cash", "debitcredit": "DEBIT", "amount": total, "account_id": 1, "subsidiary_account_id": sub_account_id},
                    {"narration": "To Sale", "debitcredit": "CREDIT", "amount": total, "account_id": 3, "subsidiary_account_id": sub_account_id}
                ]
            else:
                return [
                    {"narration": "Cash", "debitcredit": "DEBIT", "amount": amount_paid, "account_id": 1, "subsidiary_account_id": sub_account_id},
                    {"narration": "Accounts Receivable", "debitcredit": "DEBIT", "amount": total - amount_paid, "account_id": 2, "subsidiary_account_id": sub_account_id},
                    {"narration": "To Sale", "debitcredit": "CREDIT", "amount": total, "account_id": 3, "subsidiary_account_id": sub_account_id}
                ]
        elif payment_method == 'credit':
            return [
                {"narration": "Credit", "debitcredit": "DEBIT", "amount": total, "account_id": 2, "subsidiary_account_id": sub_account_id},
                {"narration": "To Sale", "debitcredit": "CREDIT", "amount": total, "account_id": 3, "subsidiary_account_id": sub_account_id}
            ]
        elif payment_method == 'bank_transfer':
            return [
                {"narration": "Bank", "debitcredit": "DEBIT", "amount": total, "account_id": 4, "subsidiary_account_id": sub_account_id},
                {"narration": "To Sale", "debitcredit": "CREDIT", "amount": total, "account_id": 3, "subsidiary_account_id": sub_account_id}
            ]
        else:
            return [
                {"narration": "Accounts Receivable", "debitcredit": "DEBIT", "amount": total, "account_id": 2, "subsidiary_account_id": sub_account_id},
                {"narration": "To Sale", "debitcredit": "CREDIT", "amount": total, "account_id": 3, "subsidiary_account_id": sub_account_id}
            ]

    async def create_ledger_with_entry(self, entry_data: LedgerWithEntryRequest):
        # Validate debit/credit balance
        debit_total = sum(item.amount for item in entry_data.journal_items if item.debitcredit == 'DEBIT')
        credit_total = sum(item.amount for item in entry_data.journal_items if item.debitcredit == 'CREDIT')

        if abs(debit_total - credit_total) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debits and credits must be balanced"
            )

        # Create Journal Entry
        db_entry = JournalEntry(
            ref_no=entry_data.ref_no,
            account_type=entry_data.account_type.value.lower(),
            company=entry_data.company,
            description=entry_data.description,
           # transaction_date=func.now(),
            user_id=entry_data.user_id
        )
        self.db.add(db_entry)
        await self.db.flush()

        # Create Journal Items and Ledgers
        for journal in entry_data.journal_items:
            db_item = JournalItems(
                narration=journal.narration,
                debitcredit=journal.debitcredit,
                amount=journal.amount,
                account_id=journal.account_id,
                journal_entry_id=db_entry.id,
                subsidiary_account_id=journal.subsidiary_account_id
            )
            self.db.add(db_item)
            await self.db.flush()

            current_balance = await self.get_account_balance(journal.account_id)
            amount = Decimal(journal.amount)
            new_balance = (
                current_balance + amount if journal.debitcredit == 'DEBIT'
                else current_balance - amount
            )

            ledger_entry = Ledger(
                account_id=journal.account_id,
                journal_item_id=db_item.id,
                entry_date= func.now(), #entry_data.transaction_date,
                amount=journal.amount,
                balance=new_balance,
                type=journal.debitcredit
            )
            self.db.add(ledger_entry)

        await self.db.flush()

    async def get_account_balance(self, account_id: int) -> Decimal:
        result = await self.db.execute(
            select(Ledger).where(Ledger.account_id == account_id).order_by(Ledger.id.desc())
        )
        last_entry = result.scalars().first()
        return last_entry.balance if last_entry else Decimal("0.0")

    async def get_subsidiary_account(self, client_id: int) -> int:
        result = await self.db.execute(
            select(SubsidiaryAccount).where(SubsidiaryAccount.client_id == client_id)
        )
        account = result.scalars().first()
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subsidiary account not found for client_id {client_id}"
            )
        return account.subsidiary_account_id

#    async def get_account_type(self,payment_method:str)->int:

