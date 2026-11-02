from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import (
    auth,
    result_final_exam,
    student_record,
    course_enrollment,
    frontend,
    admin,
    admin_user,
    verification,
    option
)

from datetime import datetime


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Student Portal REST API",
    description="API for Student Portal",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    
    allow_origins= ["*"], #["https://campus.metrouni.ac.bd/"],  # React frontend origin
    allow_credentials=True,

    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],

    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["auth"],
)

app.include_router(
    frontend.router,
    prefix="/frontend",
    tags=["Frontend"],
)

app.include_router(
    result_final_exam.router,
    prefix="/api/v1/result",
    tags=["result"],
)

app.include_router(
    student_record.router,
    prefix="/api/v1/student-record",
    tags=["student-record"],
)

app.include_router(
    course_enrollment.router,
    prefix="/api/v1/course",
    tags=["course"],
)

app.include_router(
    verification.router,
    prefix="/api/v1/verification",
    tags=["verification"],
)

app.include_router(
    admin_user.router,
    prefix="/api/v1/admin-user",
    tags=["admin-user"],
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["admin"],
)

app.include_router(
    option.router,
    prefix="/api/v1/option",
    tags=["option"],
)

# ============================================================
# ROOT
# ============================================================

@app.get("/", tags=["Root"])
async def root():

    return {
        "message": "Student Portal REST API",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "docs": "GET /docs",
            "redoc": "GET /redoc",
        },
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health", tags=["System"])
async def health():

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():

    print("=" * 60)
    print("🚀 Student Portal REST API")
    print("=" * 60)

    print("📍 Server: http://0.0.0.0:2096")

    print("📍 GET /")
    print("📍 GET /health")
    print("📍 GET /docs")
    print("📍 GET /redoc")

    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=2096,
        reload=True,
    )