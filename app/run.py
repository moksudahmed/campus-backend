from collections import defaultdict
import pandas as pd

# Dummy data from journal entries
journal_entries = [
    {"client": "Ahmed Bricks", "account": "Accounts Receivable", "debitcredit": "D", "amount": 124000},
    {"client": "Ahmed Bricks", "account": "Cash", "debitcredit": "D", "amount": 102000},
    {"client": "Arif Bricks", "account": "Accounts Receivable", "debitcredit": "D", "amount": 56000},
    {"client": "Arif Bricks", "account": "Cash", "debitcredit": "D", "amount": 56000},
    {"client": "Shanti Stone", "account": "Accounts Receivable", "debitcredit": "D", "amount": 0},
    {"client": "Shanti Stone", "account": "Cash", "debitcredit": "D", "amount": 0},
]

# Step 1: Calculate totals
client_totals = defaultdict(lambda: {"total_due": 0, "total_paid": 0})

for entry in journal_entries:
    client = entry["client"]
    account = entry["account"]
    debitcredit = entry["debitcredit"]
    amount = entry["amount"]

    if account == "Accounts Receivable" and debitcredit == "D":
        client_totals[client]["total_due"] += amount
    elif account == "Cash" and debitcredit == "D":
        client_totals[client]["total_paid"] += amount

# Step 2: Prepare final data
statement = []
for client, totals in client_totals.items():
    due = totals["total_due"]
    paid = totals["total_paid"]
    outstanding = due - paid
    statement.append({
        "Client Name": client,
        "Total Due": f"{due:,}",
        "Total Paid": f"{paid:,}",
        "Outstanding Due": f"{outstanding:,}"
    })

# Step 3: Show in table format
df = pd.DataFrame(statement)
print(df.to_markdown(index=False))
