from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, result_final_exam, student_record, course_enrollment, frontend
import uvicorn
from datetime import datetime, timedelta
#app = FastAPI()
app = FastAPI(
    title="Student Porstal RESTAPI",
    description="API for handling password reset requests",
    version="1.0.0"
)

# Set up CORS
# Add CORS middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://campus.metrouni.ac.bd/"],  # React frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(frontend.router, prefix="/frontend", tags=["Frontend"])
app.include_router(result_final_exam.router, prefix="/api/v1/result", tags=["result"])
app.include_router(student_record.router, prefix="/api/v1/student-record", tags=["student-record"])
app.include_router(course_enrollment.router, prefix="/api/v1/course", tags=["course"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Password Reset API",
        "version": "1.0.0",
        "endpoints": {
            "forgot_password": "POST /api/forgot-password",
            "verify_token": "GET /api/verify-token",
            "reset_password": "POST /api/reset-password",
            "reset_page": "GET /reset-password?token=xxx",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }

@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
# ------------------------------
# For Local Testing
# ------------------------------
# ============= STARTUP EVENT =============

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("🚀 Password Reset API - FastAPI")
    print("=" * 60)
    print("📍 API Endpoints:")
    print("   POST   /api/forgot-password")
    print("   GET    /api/verify-token?token=xxx")
    print("   POST   /api/reset-password")
    print("   GET    /reset-password?token=xxx")
    print("   GET    /health")
    print("   GET    /docs (Swagger UI)")
    print("   GET    /redoc (ReDoc)")
    print("=" * 60)
    print(f"🌐 Server running on: http://localhost:8000")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
