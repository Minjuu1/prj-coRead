from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from api import users_router, documents_router, threads_router
from api.pipeline import router as pipeline_router

app = FastAPI(
    title="CoRead API",
    description="Multi-Agent Reading Discussion System API",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:5174",  # Vite fallback port
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(threads_router, prefix="/api")
app.include_router(pipeline_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "CoRead API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    from services.pdf_parser import pdf_parser_service
    from services.firebase_service import firebase_service

    grobid_healthy = await pdf_parser_service.check_health()

    return {
        "status": "healthy",
        "services": {
            "grobid": "available" if grobid_healthy else "unavailable",
            "storage": "firebase" if firebase_service.is_using_firebase else "in-memory"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
