"""Dependencies para autenticação e autorização."""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db
from core.models import User, Personal
from core.enums import UserRole
from auth.firebase_auth import verify_firebase_token
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency: Extrai e valida Firebase token, retorna User do DB.

    Header esperado: Authorization: Bearer <firebase_id_token>

    Raises:
        HTTPException 401: Token ausente ou inválido
        HTTPException 404: User não encontrado no DB
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extrai token do header "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Esquema de autenticação inválido (use Bearer)",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de Authorization header inválido",
        )

    # MODO DEBUG: Aceita tokens mock para desenvolvimento
    if settings.DEBUG and token.startswith("dev-mock-"):
        logger.debug(f"Modo DEBUG: aceitando token mock '{token}'")

        # Mapeia tokens mock para firebase_uid mockados (carregados do .env)
        mock_token_map = {
            settings.DEV_ADMIN_TOKEN: settings.DEV_ADMIN_UID,
            settings.DEV_PERSONAL_TOKEN: settings.DEV_PERSONAL_UID,
        }

        firebase_uid = mock_token_map.get(token)
        if not firebase_uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token mock desconhecido",
            )
    else:
        # PRODUÇÃO: Valida token com Firebase
        try:
            decoded_token = verify_firebase_token(token)
            firebase_uid = decoded_token["uid"]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    # Busca User no DB
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com firebase_uid={firebase_uid} não encontrado no banco de dados",
        )

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory: restringe acesso a rotas por role.

    Uso:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])

    Args:
        allowed_roles: Roles permitidas

    Returns:
        Dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Role necessária: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


async def get_personal_id(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> int:
    """
    Dependency: Retorna personal_id do usuário logado (TENANT ID).

    - Se role = PERSONAL: retorna seu próprio personal_id
    - Se role = ADMIN: pode passar ?personal_id=X para impersonar (opcional)
    - Se role = ALUNO: raise 403

    Raises:
        HTTPException 403: Se não for personal/admin
        HTTPException 404: Se personal não encontrado

    Returns:
        int: personal_id (tenant)
    """
    if current_user.role == UserRole.ADMIN:
        # Admin pode impersonar (para debug/suporte)
        # Por enquanto, retorna None para indicar "ver todos"
        # OU implementar query param impersonation
        logger.info(f"Admin {current_user.id} acessando com privilégios totais")
        return None  # None = acesso total para admin

    elif current_user.role == UserRole.PERSONAL:
        # Busca Personal vinculado ao user
        personal = db.query(Personal).filter(Personal.user_id == current_user.id).first()
        if not personal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Personal não encontrado para este usuário",
            )
        return personal.id

    else:
        # Aluno não pode acessar recursos de personal
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas personals podem acessar este recurso.",
        )


def apply_tenant_filter(query, model, personal_id: Optional[int]):
    """
    Helper: Aplica filtro de tenant em queries.

    Se personal_id for None (admin), não filtra.
    Caso contrário, filtra por personal_id.

    Args:
        query: SQLAlchemy query
        model: Modelo ORM (deve ter atributo personal_id)
        personal_id: ID do tenant ou None para admin

    Returns:
        Query filtrada
    """
    if personal_id is None:
        # Admin vê tudo
        return query

    # Filtra por tenant
    return query.filter(model.personal_id == personal_id)
