from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.papers import router as papers_router
from api.threads import router as threads_router
from api.chat import router as chat_router

app = FastAPI(title="CoRead API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers_router, prefix="/papers", tags=["papers"])
app.include_router(threads_router, prefix="/threads", tags=["threads"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])


@app.get("/health")
def health():
    return {"status": "ok"}
