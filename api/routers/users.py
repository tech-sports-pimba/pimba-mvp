"""Router de usuários."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from core.models import User
from core.enums import UserRole
from auth.dependencies import get_current_user

router = APIRouter()


# Schemas
class UserResponse(BaseModel):
    """Response com dados do usuário."""
    id: int
    firebase_uid: str
    email: str
    nome: str
    role: UserRole
    ativo: bool

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Retorna dados do usuário autenticado.

    Requer: Authorization header com Firebase token válido.
    """
    return current_user
