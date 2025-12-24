"""Router de agendamentos (calendário)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
from typing import Optional
from core.database import get_db
from core.models import Agendamento, Aluno
from core.enums import AgendamentoStatus
from auth.dependencies import get_personal_id, apply_tenant_filter

router = APIRouter()


# Schemas
class AgendamentoCreate(BaseModel):
    """Schema para criar agendamento."""
    aluno_id: int
    data_hora_inicio: datetime
    duracao_minutos: int = Field(default=60, ge=15, le=480)
    local: Optional[str] = None
    observacoes: Optional[str] = None


class AgendamentoUpdate(BaseModel):
    """Schema para atualizar agendamento."""
    aluno_id: Optional[int] = None
    data_hora_inicio: Optional[datetime] = None
    duracao_minutos: Optional[int] = Field(default=None, ge=15, le=480)
    local: Optional[str] = None
    observacoes: Optional[str] = None
    status: Optional[AgendamentoStatus] = None


class AgendamentoResponse(BaseModel):
    """Schema de resposta de agendamento."""
    id: int
    personal_id: int
    aluno_id: int
    aluno_nome: str
    data_hora_inicio: datetime
    data_hora_fim: datetime
    duracao_minutos: int
    local: Optional[str]
    observacoes: Optional[str]
    status: AgendamentoStatus
    criado_em: datetime

    class Config:
        from_attributes = True


class AgendamentoListResponse(BaseModel):
    """Schema de listagem de agendamentos."""
    total: int
    agendamentos: list[AgendamentoResponse]


class AgendamentoStatsResponse(BaseModel):
    """Schema de estatísticas de agendamentos."""
    total: int
    hoje: int
    semana: int
    mes: int
    proximos_7_dias: int


# Endpoints
@router.get("/", response_model=AgendamentoListResponse)
def listar_agendamentos(
    data_inicio: Optional[date] = Query(None, description="Data início (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data fim (YYYY-MM-DD)"),
    aluno_id: Optional[int] = Query(None, description="Filtrar por aluno"),
    status: Optional[AgendamentoStatus] = Query(None, description="Filtrar por status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Lista agendamentos com filtros.

    **TENANT ISOLATION:** Apenas agendamentos do personal logado.
    """
    # Query base com tenant isolation
    query = db.query(Agendamento).join(Aluno)
    query = apply_tenant_filter(query, Agendamento, personal_id)

    # Filtros
    if data_inicio:
        query = query.filter(Agendamento.data_hora_inicio >= datetime.combine(data_inicio, datetime.min.time()))

    if data_fim:
        query = query.filter(Agendamento.data_hora_inicio <= datetime.combine(data_fim, datetime.max.time()))

    if aluno_id:
        query = query.filter(Agendamento.aluno_id == aluno_id)

    if status:
        query = query.filter(Agendamento.status == status)

    # Total
    total = query.count()

    # Ordena por data/hora
    agendamentos = query.order_by(Agendamento.data_hora_inicio).offset(skip).limit(limit).all()

    # Monta response com nome do aluno
    response_data = []
    for ag in agendamentos:
        aluno = db.query(Aluno).filter(Aluno.id == ag.aluno_id).first()
        response_data.append(
            AgendamentoResponse(
                id=ag.id,
                personal_id=ag.personal_id,
                aluno_id=ag.aluno_id,
                aluno_nome=aluno.nome if aluno else "Desconhecido",
                data_hora_inicio=ag.data_hora_inicio,
                data_hora_fim=ag.data_hora_inicio + timedelta(minutes=ag.duracao_minutos),
                duracao_minutos=ag.duracao_minutos,
                local=ag.local,
                observacoes=ag.observacoes,
                status=ag.status,
                criado_em=ag.criado_em,
            )
        )

    return AgendamentoListResponse(total=total, agendamentos=response_data)


@router.get("/stats", response_model=AgendamentoStatsResponse)
def estatisticas_agendamentos(
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Retorna estatísticas de agendamentos.

    **TENANT ISOLATION:** Apenas agendamentos do personal logado.
    """
    # Query base
    query = db.query(Agendamento)
    query = apply_tenant_filter(query, Agendamento, personal_id)

    # Total
    total = query.count()

    # Hoje
    hoje = date.today()
    hoje_inicio = datetime.combine(hoje, datetime.min.time())
    hoje_fim = datetime.combine(hoje, datetime.max.time())
    total_hoje = query.filter(
        and_(
            Agendamento.data_hora_inicio >= hoje_inicio,
            Agendamento.data_hora_inicio <= hoje_fim,
        )
    ).count()

    # Semana (próximos 7 dias)
    proximos_7_dias_fim = datetime.combine(hoje + timedelta(days=7), datetime.max.time())
    total_proximos_7_dias = query.filter(
        and_(
            Agendamento.data_hora_inicio >= hoje_inicio,
            Agendamento.data_hora_inicio <= proximos_7_dias_fim,
        )
    ).count()

    # Semana atual (segunda a domingo)
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    total_semana = query.filter(
        and_(
            Agendamento.data_hora_inicio >= datetime.combine(inicio_semana, datetime.min.time()),
            Agendamento.data_hora_inicio <= datetime.combine(fim_semana, datetime.max.time()),
        )
    ).count()

    # Mês atual
    inicio_mes = date(hoje.year, hoje.month, 1)
    if hoje.month == 12:
        fim_mes = date(hoje.year + 1, 1, 1) - timedelta(days=1)
    else:
        fim_mes = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

    total_mes = query.filter(
        and_(
            Agendamento.data_hora_inicio >= datetime.combine(inicio_mes, datetime.min.time()),
            Agendamento.data_hora_inicio <= datetime.combine(fim_mes, datetime.max.time()),
        )
    ).count()

    return AgendamentoStatsResponse(
        total=total,
        hoje=total_hoje,
        semana=total_semana,
        mes=total_mes,
        proximos_7_dias=total_proximos_7_dias,
    )


@router.post("/", response_model=AgendamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_agendamento(
    dados: AgendamentoCreate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Cria novo agendamento.

    **TENANT ISOLATION:** Personal só pode criar agendamentos para seus alunos.
    """
    # Valida que aluno pertence ao personal
    aluno = db.query(Aluno).filter(Aluno.id == dados.aluno_id).first()

    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # Valida tenant
    if personal_id and aluno.personal_id != personal_id:
        raise HTTPException(status_code=403, detail="Aluno não pertence a este personal")

    # Cria agendamento
    agendamento = Agendamento(
        personal_id=aluno.personal_id,
        aluno_id=dados.aluno_id,
        data_hora_inicio=dados.data_hora_inicio,
        duracao_minutos=dados.duracao_minutos,
        local=dados.local,
        observacoes=dados.observacoes,
        status=AgendamentoStatus.AGENDADO,
    )

    db.add(agendamento)
    db.commit()
    db.refresh(agendamento)

    return AgendamentoResponse(
        id=agendamento.id,
        personal_id=agendamento.personal_id,
        aluno_id=agendamento.aluno_id,
        aluno_nome=aluno.nome,
        data_hora_inicio=agendamento.data_hora_inicio,
        data_hora_fim=agendamento.data_hora_inicio + timedelta(minutes=agendamento.duracao_minutos),
        duracao_minutos=agendamento.duracao_minutos,
        local=agendamento.local,
        observacoes=agendamento.observacoes,
        status=agendamento.status,
        criado_em=agendamento.criado_em,
    )


@router.get("/{agendamento_id}", response_model=AgendamentoResponse)
def obter_agendamento(
    agendamento_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Obtém detalhes de um agendamento.

    **TENANT ISOLATION:** Personal só pode ver seus agendamentos.
    """
    agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()

    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    # Valida tenant
    if personal_id and agendamento.personal_id != personal_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    aluno = db.query(Aluno).filter(Aluno.id == agendamento.aluno_id).first()

    return AgendamentoResponse(
        id=agendamento.id,
        personal_id=agendamento.personal_id,
        aluno_id=agendamento.aluno_id,
        aluno_nome=aluno.nome if aluno else "Desconhecido",
        data_hora_inicio=agendamento.data_hora_inicio,
        data_hora_fim=agendamento.data_hora_inicio + timedelta(minutes=agendamento.duracao_minutos),
        duracao_minutos=agendamento.duracao_minutos,
        local=agendamento.local,
        observacoes=agendamento.observacoes,
        status=agendamento.status,
        criado_em=agendamento.criado_em,
    )


@router.put("/{agendamento_id}", response_model=AgendamentoResponse)
def atualizar_agendamento(
    agendamento_id: int,
    dados: AgendamentoUpdate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Atualiza agendamento.

    **TENANT ISOLATION:** Personal só pode atualizar seus agendamentos.
    """
    agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()

    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    # Valida tenant
    if personal_id and agendamento.personal_id != personal_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Atualiza campos
    if dados.aluno_id is not None:
        # Valida novo aluno
        aluno = db.query(Aluno).filter(Aluno.id == dados.aluno_id).first()
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        if personal_id and aluno.personal_id != personal_id:
            raise HTTPException(status_code=403, detail="Aluno não pertence a este personal")
        agendamento.aluno_id = dados.aluno_id

    if dados.data_hora_inicio is not None:
        agendamento.data_hora_inicio = dados.data_hora_inicio

    if dados.duracao_minutos is not None:
        agendamento.duracao_minutos = dados.duracao_minutos

    if dados.local is not None:
        agendamento.local = dados.local

    if dados.observacoes is not None:
        agendamento.observacoes = dados.observacoes

    if dados.status is not None:
        agendamento.status = dados.status

    db.commit()
    db.refresh(agendamento)

    aluno = db.query(Aluno).filter(Aluno.id == agendamento.aluno_id).first()

    return AgendamentoResponse(
        id=agendamento.id,
        personal_id=agendamento.personal_id,
        aluno_id=agendamento.aluno_id,
        aluno_nome=aluno.nome if aluno else "Desconhecido",
        data_hora_inicio=agendamento.data_hora_inicio,
        data_hora_fim=agendamento.data_hora_inicio + timedelta(minutes=agendamento.duracao_minutos),
        duracao_minutos=agendamento.duracao_minutos,
        local=agendamento.local,
        observacoes=agendamento.observacoes,
        status=agendamento.status,
        criado_em=agendamento.criado_em,
    )


@router.delete("/{agendamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_agendamento(
    agendamento_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Deleta agendamento.

    **TENANT ISOLATION:** Personal só pode deletar seus agendamentos.
    """
    agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()

    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    # Valida tenant
    if personal_id and agendamento.personal_id != personal_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    db.delete(agendamento)
    db.commit()

    return None
