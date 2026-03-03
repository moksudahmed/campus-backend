from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.option import Option


class OptionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------
    # GET ALL
    # -------------------------
    async def get_all(
        self,
        group: Optional[str] = None
    ) -> List[Option]:

        query = select(Option)

        if group:
            query = query.where(Option.option_group == group)

        result = await self.db.execute(query)
        return result.scalars().all()

    # -------------------------
    # GET BY ID
    # -------------------------
    async def get_by_id(self, option_id: int) -> Optional[Option]:
        result = await self.db.execute(
            select(Option).where(
                Option.optionID == option_id
            )
        )
        return result.scalar_one_or_none()

    # -------------------------
    # GET BY NAME (Very Useful)
    # -------------------------
    async def get_by_name(self, option_name: str) -> Optional[Option]:
        result = await self.db.execute(
            select(Option).where(
                Option.option_name == option_name
            )
        )
        return result.scalar_one_or_none()

    # -------------------------
    # UPDATE
    # -------------------------
   