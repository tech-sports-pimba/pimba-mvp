"""Router de autenticação."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from core.database import get_db
from core.models import User, Personal
from core.enums import UserRole
from auth.firebase_auth import verify_firebase_token, create_firebase_user, get_firebase_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Schemas
class LoginRequest(BaseModel):
    """Request para login com Firebase token."""
    id_token: str


class LoginResponse(BaseModel):
    """Response do login com info do usuário."""
    user_id: int
    firebase_uid: str
    email: str
    nome: str
    role: UserRole
    personal_id: int | None = None


class RegisterPersonalRequest(BaseModel):
    """Request para criar novo personal (admin only)."""
    email: EmailStr
    password: str
    nome: str
    telefone: str | None = None
    especializacao: str | None = None


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Valida Firebase ID token e retorna informações do usuário.

    Fluxo:
    1. Cliente autentica com Firebase (client SDK)
    2. Cliente recebe id_token
    3. Cliente envia id_token para esta rota
    4. Servidor valida token com Firebase Admin SDK
    5. Servidor busca User no DB e retorna info
    """
    # Valida token com Firebase
    try:
        decoded_token = verify_firebase_token(request.id_token)
        firebase_uid = decoded_token["uid"]
        email = decoded_token.get("email")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {e}",
        )

    # Busca ou cria User no DB
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        # Auto-create user se não existir (primeira vez que loga)
        # Nota: Nome pode vir do token ou ser atualizado depois
        nome = decoded_token.get("name") or decoded_token.get("email", "").split("@")[0]
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            nome=nome,
            role=UserRole.ALUNO,  # Default: aluno. Admin promove para personal manualmente
            ativo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✅ Novo usuário auto-criado: {user.email}")

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    # Busca personal_id se for personal
    personal_id = None
    if user.role == UserRole.PERSONAL:
        personal = db.query(Personal).filter(Personal.user_id == user.id).first()
        if personal:
            personal_id = personal.id

    return LoginResponse(
        user_id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        nome=user.nome,
        role=user.role,
        personal_id=personal_id,
    )


@router.post("/register-personal", status_code=status.HTTP_201_CREATED)
def register_personal(
    request: RegisterPersonalRequest,
    db: Session = Depends(get_db),
    # Descomente quando auth estiver funcionando:
    # current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Cria novo personal trainer (admin only).

    Fluxo:
    1. Admin cria usuário no Firebase Auth
    2. Cria registro User no DB com role=PERSONAL
    3. Cria registro Personal vinculado

    Nota: Por enquanto sem proteção de role para facilitar desenvolvimento.
    Descomentar dependency quando Firebase estiver configurado.
    """
    # Verifica se email já existe no DB
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado",
        )

    # Cria usuário no Firebase Auth
    try:
        firebase_user = create_firebase_user(
            email=request.email,
            password=request.password,
            display_name=request.nome,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar usuário no Firebase: {e}",
        )

    # Cria User no DB
    user = User(
        firebase_uid=firebase_user["uid"],
        email=request.email,
        nome=request.nome,
        role=UserRole.PERSONAL,
        ativo=True,
    )
    db.add(user)
    db.flush()  # Garante que user.id esteja disponível

    # Cria Personal
    personal = Personal(
        user_id=user.id,
        telefone=request.telefone,
        especializacao=request.especializacao,
    )
    db.add(personal)
    db.commit()
    db.refresh(personal)

    logger.info(f"✅ Personal criado: {user.email} (personal_id={personal.id})")

    return {
        "message": "Personal criado com sucesso",
        "user_id": user.id,
        "personal_id": personal.id,
        "email": user.email,
    }
