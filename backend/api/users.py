from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.firebase_service import firebase_service

router = APIRouter(prefix="/users", tags=["users"])


class LoginRequest(BaseModel):
    userId: str


class UserResponse(BaseModel):
    userId: str
    createdAt: str
    documents: list[str]


@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest):
    """
    Login with user ID. Creates a new user if ID doesn't exist.
    """
    if not request.userId or not request.userId.strip():
        raise HTTPException(status_code=400, detail="User ID is required")

    user = firebase_service.get_or_create_user(request.userId.strip())
    return UserResponse(**user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Get user information.
    """
    user = firebase_service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)
