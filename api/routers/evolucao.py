"""Router de acompanhamento de evolução/desempenho dos alunos."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

from core.database import get_db
from core.models import RegistroEvolucao, Aluno
from auth.dependencies import get_current_user, require_role, get_personal_id, apply_tenant_filter

router = APIRouter(prefix="/evolucao", tags=["evolucao"])


# Schemas Pydantic
class RegistroEvolucaoBase(BaseModel):
    """Schema base de registro de evolução."""
    data_registro: date
    presente: bool = Field(default=True, description="Aluno estava presente?")
    nivel_treino: Optional[int] = Field(None, ge=1, le=5, description="Nível/intensidade do treino (1-5)")
    observacoes: Optional[str] = None


class RegistroEvolucaoCreate(RegistroEvolucaoBase):
    """Schema para criar registro."""
    pass


class RegistroEvolucaoUpdate(BaseModel):
    """Schema para atualizar registro."""
    data_registro: Optional[date] = None
    presente: Optional[bool] = None
    nivel_treino: Optional[int] = Field(None, ge=1, le=5)
    observacoes: Optional[str] = None


class RegistroEvolucaoResponse(RegistroEvolucaoBase):
    """Schema de resposta."""
    id: int
    aluno_id: int
    aluno_nome: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True


class RegistroListResponse(BaseModel):
    """Schema de resposta da listagem."""
    total: int
    registros: List[RegistroEvolucaoResponse]


class EstatisticasEvolucaoResponse(BaseModel):
    """Estatísticas de evolução do aluno."""
    total_registros: int
    total_presencas: int
    taxa_presenca: float  # percentual
    nivel_medio: Optional[float]
    ultimo_registro: Optional[date]


@router.get("/aluno/{aluno_id}", response_model=RegistroListResponse)
def listar_registros_aluno(
    aluno_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Lista registros de evolução de um aluno.

    **TENANT ISOLATION:** Valida que o aluno pertence ao personal.
    """
    # Valida que aluno pertence ao personal
    aluno_query = db.query(Aluno).filter(Aluno.id == aluno_id)
    aluno_query = apply_tenant_filter(aluno_query, Aluno, personal_id)
    aluno = aluno_query.first()

    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado ou não pertence a este personal"
        )

    # Query registros
    query = db.query(RegistroEvolucao).filter(RegistroEvolucao.aluno_id == aluno_id)

    # Filtros de data
    if data_inicio:
        query = query.filter(RegistroEvolucao.data_registro >= data_inicio)
    if data_fim:
        query = query.filter(RegistroEvolucao.data_registro <= data_fim)

    # Total
    total = query.count()

    # Paginação e ordenação (mais recentes primeiro)
    registros = query.order_by(RegistroEvolucao.data_registro.desc()).offset(skip).limit(limit).all()

    # Adiciona nome do aluno
    registros_com_nome = []
    for reg in registros:
        registros_com_nome.append(RegistroEvolucaoResponse(
            id=reg.id,
            aluno_id=reg.aluno_id,
            aluno_nome=aluno.nome,
            data_registro=reg.data_registro,
            presente=reg.peso_kg is not None,  # Temporário: usando peso_kg como flag de presença
            nivel_treino=int(reg.medidas.get("nivel_treino")) if reg.medidas and "nivel_treino" in reg.medidas else None,
            observacoes=reg.observacoes,
            criado_em=reg.criado_em,
        ))

    return RegistroListResponse(total=total, registros=registros_com_nome)


@router.get("/aluno/{aluno_id}/stats", response_model=EstatisticasEvolucaoResponse)
def estatisticas_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Retorna estatísticas de evolução do aluno.

    **TENANT ISOLATION:** Valida que o aluno pertence ao personal.
    """
    # Valida que aluno pertence ao personal
    aluno_query = db.query(Aluno).filter(Aluno.id == aluno_id)
    aluno_query = apply_tenant_filter(aluno_query, Aluno, personal_id)
    aluno = aluno_query.first()

    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado ou não pertence a este personal"
        )

    # Query registros
    query = db.query(RegistroEvolucao).filter(RegistroEvolucao.aluno_id == aluno_id)

    total_registros = query.count()

    if total_registros == 0:
        return EstatisticasEvolucaoResponse(
            total_registros=0,
            total_presencas=0,
            taxa_presenca=0.0,
            nivel_medio=None,
            ultimo_registro=None,
        )

    # Total de presenças (usando peso_kg como flag temporária)
    total_presencas = query.filter(RegistroEvolucao.peso_kg.isnot(None)).count()
    taxa_presenca = (total_presencas / total_registros * 100) if total_registros > 0 else 0.0

    # Nível médio (extraindo de medidas JSON)
    registros_com_nivel = query.filter(RegistroEvolucao.medidas.isnot(None)).all()
    niveis = []
    for reg in registros_com_nivel:
        if reg.medidas and "nivel_treino" in reg.medidas:
            niveis.append(int(reg.medidas["nivel_treino"]))

    nivel_medio = sum(niveis) / len(niveis) if niveis else None

    # Último registro
    ultimo = query.order_by(RegistroEvolucao.data_registro.desc()).first()
    ultimo_registro = ultimo.data_registro if ultimo else None

    return EstatisticasEvolucaoResponse(
        total_registros=total_registros,
        total_presencas=total_presencas,
        taxa_presenca=round(taxa_presenca, 1),
        nivel_medio=round(nivel_medio, 1) if nivel_medio else None,
        ultimo_registro=ultimo_registro,
    )


@router.post("/aluno/{aluno_id}", response_model=RegistroEvolucaoResponse, status_code=status.HTTP_201_CREATED)
def criar_registro(
    aluno_id: int,
    registro_data: RegistroEvolucaoCreate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Cria novo registro de evolução para um aluno.

    **TENANT ISOLATION:** Valida que o aluno pertence ao personal.
    """
    # Valida que aluno pertence ao personal
    aluno_query = db.query(Aluno).filter(Aluno.id == aluno_id)
    aluno_query = apply_tenant_filter(aluno_query, Aluno, personal_id)
    aluno = aluno_query.first()

    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado ou não pertence a este personal"
        )

    # Cria registro (adaptando ao modelo existente)
    medidas_json = {}
    if registro_data.nivel_treino:
        medidas_json["nivel_treino"] = registro_data.nivel_treino

    registro = RegistroEvolucao(
        aluno_id=aluno_id,
        data_registro=registro_data.data_registro,
        peso_kg=1.0 if registro_data.presente else None,  # Hack: usando peso_kg como flag de presença
        medidas=medidas_json if medidas_json else None,
        observacoes=registro_data.observacoes,
    )

    db.add(registro)
    db.commit()
    db.refresh(registro)

    return RegistroEvolucaoResponse(
        id=registro.id,
        aluno_id=registro.aluno_id,
        aluno_nome=aluno.nome,
        data_registro=registro.data_registro,
        presente=registro_data.presente,
        nivel_treino=registro_data.nivel_treino,
        observacoes=registro.observacoes,
        criado_em=registro.criado_em,
    )


@router.delete("/{registro_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Deleta registro de evolução.

    **TENANT ISOLATION:** Valida que o registro pertence a um aluno do personal.
    """
    # Busca registro
    registro = db.query(RegistroEvolucao).filter(RegistroEvolucao.id == registro_id).first()

    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado"
        )

    # Valida que aluno pertence ao personal
    aluno_query = db.query(Aluno).filter(Aluno.id == registro.aluno_id)
    aluno_query = apply_tenant_filter(aluno_query, Aluno, personal_id)
    aluno = aluno_query.first()

    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado ou não pertence a este personal"
        )

    db.delete(registro)
    db.commit()

    return None
