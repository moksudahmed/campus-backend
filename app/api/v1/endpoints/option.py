# app/services/ad_option_service.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.OptionService import OptionService
from app.core.security import verify_token


router = APIRouter()

# HTTP Bearer authentication
security = HTTPBearer()


# --------------------------------------------------------------------------
# Verify current authenticated token
# --------------------------------------------------------------------------
async def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials

    return await verify_token(
        db=db,
        token=token,
    )


# --------------------------------------------------------------------------
# Get current academic term and year
# --------------------------------------------------------------------------
@router.get("/current-term")
async def get_current_term(
    db: AsyncSession = Depends(get_db),
    token_record=Depends(get_current_token),
):
    """
    Return the currently configured academic year and term.

    Authentication:
        Authorization: Bearer <access_token>

    Response:
        {
            "year": 2026,
            "term": 1
        }
    """

    service = OptionService(db)

    option_year = await service.get_by_name("current_year")
    option_term = await service.get_by_name("current_term")

    if not option_year:
        raise HTTPException(
            status_code=404,
            detail="Current academic year is not configured.",
        )

    if not option_term:
        raise HTTPException(
            status_code=404,
            detail="Current academic term is not configured.",
        )

    try:
        current_year = int(option_year.option_value)
        current_term = int(option_term.option_value)

    except (TypeError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Invalid current year or term configuration.",
        )

    return {
        "year": current_year,
        "term": current_term,
    }

