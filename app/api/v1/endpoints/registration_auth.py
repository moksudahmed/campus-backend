
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_token
from app.db.session import get_db
from app.models.user import User as UserModel


async def get_current_user(
    token_record=Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the user associated with the authenticated token.

    Your create_access_token() uses student_id as user_id,
    so tokenable_id is used to identify the user.
    """

    if not token_record or not token_record.tokenable_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    student_id = str(token_record.tokenable_id)

    result = await db.execute(
        select(UserModel).where(
            UserModel.student_id == student_id
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user was not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive.",
        )

    return user


async def require_student2(
    user: UserModel = Depends(get_current_user),
):
    if (user.usr_role or "").strip().lower() != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access is required.",
        )

    return user

async def require_student(
    user: UserModel = Depends(get_current_user),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive.",
        )

    return user

async def require_registrar(
    user: UserModel = Depends(get_current_user),
):
    """
    Allow authorized registration reviewers.
    """

    allowed_roles = {
        "registrar",
        "admin",
        "super-admin",
    }

    user_role = (user.usr_role or "").strip().lower()

    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registrar access is required.",
        )

    return user


# Keep the existing endpoint type annotation convenient.
CurrentUser = UserModel
