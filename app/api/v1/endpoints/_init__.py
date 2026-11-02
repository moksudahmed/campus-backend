from fastapi import APIRouter

from app.routers.registration.student_applications import router as student_router
from app.routers.registration.application_details import router as details_router
from app.routers.registration.application_history import router as history_router
from app.routers.registration.registrar_reviews import router as registrar_router

router = APIRouter(
    prefix="/api/v1/registration-applications",
    tags=["Subject Registration"],
)

router.include_router(student_router)
router.include_router(details_router)
router.include_router(history_router)
router.include_router(registrar_router)