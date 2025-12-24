"""Router de gestão de alunos com tenant isolation."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime

from core.database import get_db
from core.models import Aluno, Personal
from core.enums import UserRole
from auth.dependencies import get_current_user, require_role, get_personal_id, apply_tenant_filter

router = APIRouter(prefix="/alunos", tags=["alunos"])


# Schemas Pydantic
class AlunoBase(BaseModel):
    """Schema base de aluno."""
    nome: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    telefone: Optional[str] = Field(None, max_length=50)
    data_nascimento: Optional[date] = None
    objetivo: Optional[str] = None


class AlunoCreate(AlunoBase):
    """Schema para criar aluno."""
    pass


class AlunoUpdate(BaseModel):
    """Schema para atualizar aluno."""
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    telefone: Optional[str] = Field(None, max_length=50)
    data_nascimento: Optional[date] = None
    objetivo: Optional[str] = None
    ativo: Optional[bool] = None


class AlunoResponse(AlunoBase):
    """Schema de resposta de aluno."""
    id: int
    personal_id: int
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class AlunoListResponse(BaseModel):
    """Schema de resposta da listagem."""
    total: int
    alunos: List[AlunoResponse]


@router.get("/", response_model=AlunoListResponse)
def listar_alunos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    ativo: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    busca: Optional[str] = Query(None, description="Buscar por nome ou email"),
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Lista alunos do personal com paginação e filtros.

    **TENANT ISOLATION:** Apenas alunos do personal logado.
    """
    # Query base com filtro de tenant
    query = db.query(Aluno)
    query = apply_tenant_filter(query, Aluno, personal_id)

    # Filtro de status
    if ativo is not None:
        query = query.filter(Aluno.ativo == ativo)

    # Busca por nome ou email
    if busca:
        busca_pattern = f"%{busca}%"
        query = query.filter(
            (Aluno.nome.ilike(busca_pattern)) |
            (Aluno.email.ilike(busca_pattern))
        )

    # Total de registros
    total = query.count()

    # Paginação
    alunos = query.order_by(Aluno.criado_em.desc()).offset(skip).limit(limit).all()

    return AlunoListResponse(total=total, alunos=alunos)


@router.get("/stats")
def estatisticas_alunos(
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Retorna estatísticas dos alunos do personal.

    **TENANT ISOLATION:** Apenas dados do personal logado.
    """
    query = db.query(Aluno)
    query = apply_tenant_filter(query, Aluno, personal_id)

    total = query.count()
    ativos = query.filter(Aluno.ativo == True).count()
    inativos = query.filter(Aluno.ativo == False).count()

    # Novos alunos no mês atual
    primeiro_dia_mes = date.today().replace(day=1)
    novos_mes = query.filter(
        func.date(Aluno.criado_em) >= primeiro_dia_mes
    ).count()

    return {
        "total": total,
        "ativos": ativos,
        "inativos": inativos,
        "novos_mes": novos_mes,
    }


@router.get("/{aluno_id}", response_model=AlunoResponse)
def obter_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Obtém aluno por ID.

    **TENANT ISOLATION:** Valida que o aluno pertence ao personal.
    """
    query = db.query(Aluno).filter(Aluno.id == aluno_id)
    query = apply_tenant_filter(query, Aluno, personal_id)

    aluno = query.first()

    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado ou não pertence a este personal"
        )

    return aluno


@router.post("/", response_model=AlunoResponse, status_code=status.HTTP_201_CREATED)
def criar_aluno(
    aluno_data: AlunoCreate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Cria novo aluno.

    **TENANT ISOLATION:** Aluno criado automaticamente para o personal logado.
    """
    # Valida que o personal_id existe (apenas se não for admin)
    if personal_id is not None:
        personal = db.query(Personal).filter(Personal.id == personal_id).first()
        if not personal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Personal não encontrado"
            )
    else:
        # Admin precisa especificar personal_id (TODO: implementar no futuro)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin deve especificar personal_id"
        )

    # Verifica email duplicado (mesmo tenant)
    if aluno_data.email:
        query = db.query(Aluno).filter(Aluno.email == aluno_data.email)
        query = apply_tenant_filter(query, Aluno, personal_id)
        existe = query.first()

        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um aluno com este email cadastrado"
            )

    # Cria aluno com personal_id automaticamente
    aluno = Aluno(
        **aluno_data.model_dump(),
        personal_id=personal_id,
        ativo=True,
    )

    db.add(aluno)
    db.commit()
    db.refresh(aluno)

    return aluno


@router.put("/{aluno_id}", response_model=AlunoResponse)
def atualizar_aluno(
    aluno_id: int,
    aluno_data: AlunoUpdate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Atualiza aluno existente.

    **TENANT ISOLATION:** Valida que o aluno pertence ao personal.
    """
    # Busca aluno com tenant filter
    query = db.query(Aluno).filter(Aluno.id == aluno_id)
    query = apply_tenant_filter(query, Aluno, personal_id)
    aluno = query.first()

    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado ou não pertence a este personal"
        )

    # Atualiza apenas campos fornecidos
    update_data = aluno_data.model_dump(exclude_unset=True)

    # Verifica email duplicado se for alterado
    if "email" in update_data and update_data["email"] and update_data["email"] != aluno.email:
        query = db.query(Aluno).filter(Aluno.email == update_data["email"])
        query = apply_tenant_filter(query, Aluno, personal_id)
        existe = query.first()

        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um aluno com este email cadastrado"
            )

    # Aplica atualizações
    for campo, valor in update_data.items():
        setattr(aluno, campo, valor)

    db.commit()
    db.refresh(aluno)

    return aluno


@router.delete("/{aluno_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Deleta aluno por ID.

    **TENANT ISOLATION:** Valida que o aluno pertence ao personal.

    IMPORTANTE: Isso deleta permanentemente o aluno e todos os dados relacionados
    (agendamentos, treinos, registros de evolução, etc).
    """
    # Busca aluno com tenant filter
    query = db.query(Aluno).filter(Aluno.id == aluno_id)
    query = apply_tenant_filter(query, Aluno, personal_id)
    aluno = query.first()

    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado ou não pertence a este personal"
        )

    db.delete(aluno)
    db.commit()

    return None


@router.patch("/{aluno_id}/toggle-ativo", response_model=AlunoResponse)
def toggle_status_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Alterna status ativo/inativo do aluno.

    **TENANT ISOLATION:** Valida que o aluno pertence ao personal.
    """
    # Busca aluno com tenant filter
    query = db.query(Aluno).filter(Aluno.id == aluno_id)
    query = apply_tenant_filter(query, Aluno, personal_id)
    aluno = query.first()

    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado ou não pertence a este personal"
        )

    # Toggle status
    aluno.ativo = not aluno.ativo

    db.commit()
    db.refresh(aluno)

    return aluno
