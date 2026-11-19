from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import (
    ApplicationDetailOut,
    ApplicationOut,
    DetailOut,
)
from app.services import bundle


async def output(db: AsyncSession, application):
    application, details = await bundle(db, application)

    data = ApplicationOut.model_validate(application).model_dump()
    data["details"] = [
        DetailOut.model_validate(detail)
        for detail in details
    ]

    return ApplicationDetailOut(**data)