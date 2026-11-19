from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models import RegistrationApplicationHistory
from app.schemas import HistoryOut
from app.services import (
    check_access,
    get_application,
)


router = APIRouter()


# =========================================================
# GET APPLICATION HISTORY
# GET /{application_id}/history
# =========================================================

@router.get(
    "/{application_id}/history",
    response_model=list[HistoryOut],
)
async def history(
    application_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    application = await get_application(db, application_id)

    await check_access(application, user)

    result = await db.execute(
        select(RegistrationApplicationHistory)
        .where(
            RegistrationApplicationHistory.application_id
            == application_id
        )
        .order_by(
            RegistrationApplicationHistory.aph_action_at.desc(),
            RegistrationApplicationHistory.history_id.desc(),
        )
    )

    return result.scalars().all()