"""Router de gestão de pagamentos com tenant isolation."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from core.database import get_db
from core.models import Pagamento, Aluno
from core.enums import PagamentoTipo
from auth.dependencies import get_current_user, require_role, get_personal_id, apply_tenant_filter

router = APIRouter(prefix="/pagamentos", tags=["pagamentos"])


# Schemas Pydantic
class PagamentoBase(BaseModel):
    """Schema base de pagamento."""
    valor: Decimal = Field(..., gt=0, description="Valor do pagamento (deve ser positivo)")
    data_pagamento: date
    tipo: PagamentoTipo
    aluno_id: Optional[int] = Field(None, description="ID do aluno (opcional)")
    descricao: Optional[str] = None


class PagamentoCreate(PagamentoBase):
    """Schema para criar pagamento."""
    pass


class PagamentoUpdate(BaseModel):
    """Schema para atualizar pagamento."""
    valor: Optional[Decimal] = Field(None, gt=0)
    data_pagamento: Optional[date] = None
    tipo: Optional[PagamentoTipo] = None
    aluno_id: Optional[int] = None
    descricao: Optional[str] = None


class PagamentoResponse(PagamentoBase):
    """Schema de resposta de pagamento."""
    id: int
    personal_id: int
    aluno_nome: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True


class PagamentoListResponse(BaseModel):
    """Schema de resposta da listagem."""
    total: int
    pagamentos: List[PagamentoResponse]


class ResumoFinanceiroResponse(BaseModel):
    """Schema de resumo financeiro."""
    total_recebido: Decimal
    total_a_receber: Decimal
    total_mes: Decimal
    quantidade_pagamentos: int


@router.get("/", response_model=PagamentoListResponse)
def listar_pagamentos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    tipo: Optional[PagamentoTipo] = Query(None, description="Filtrar por tipo"),
    aluno_id: Optional[int] = Query(None, description="Filtrar por aluno"),
    data_inicio: Optional[date] = Query(None, description="Data inicial"),
    data_fim: Optional[date] = Query(None, description="Data final"),
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Lista pagamentos do personal com paginação e filtros.

    **TENANT ISOLATION:** Apenas pagamentos do personal logado.
    """
    # Query base com filtro de tenant
    query = db.query(Pagamento)
    query = apply_tenant_filter(query, Pagamento, personal_id)

    # Filtros
    if tipo is not None:
        query = query.filter(Pagamento.tipo == tipo)

    if aluno_id is not None:
        query = query.filter(Pagamento.aluno_id == aluno_id)

    if data_inicio:
        query = query.filter(Pagamento.data_pagamento >= data_inicio)

    if data_fim:
        query = query.filter(Pagamento.data_pagamento <= data_fim)

    # Total de registros
    total = query.count()

    # Paginação e ordenação
    pagamentos = query.order_by(Pagamento.data_pagamento.desc()).offset(skip).limit(limit).all()

    # Adiciona nome do aluno
    pagamentos_com_aluno = []
    for pag in pagamentos:
        pag_dict = {
            "id": pag.id,
            "personal_id": pag.personal_id,
            "aluno_id": pag.aluno_id,
            "valor": pag.valor,
            "data_pagamento": pag.data_pagamento,
            "tipo": pag.tipo,
            "descricao": pag.descricao,
            "criado_em": pag.criado_em,
            "aluno_nome": None
        }

        if pag.aluno_id:
            aluno = db.query(Aluno).filter(Aluno.id == pag.aluno_id).first()
            if aluno:
                pag_dict["aluno_nome"] = aluno.nome

        pagamentos_com_aluno.append(PagamentoResponse(**pag_dict))

    return PagamentoListResponse(total=total, pagamentos=pagamentos_com_aluno)


@router.get("/resumo", response_model=ResumoFinanceiroResponse)
def resumo_financeiro(
    mes: Optional[int] = Query(None, ge=1, le=12, description="Mês (1-12)"),
    ano: Optional[int] = Query(None, ge=2000, le=2100, description="Ano"),
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Retorna resumo financeiro do personal.

    **TENANT ISOLATION:** Apenas dados do personal logado.
    """
    query = db.query(Pagamento)
    query = apply_tenant_filter(query, Pagamento, personal_id)

    # Se não especificar mês/ano, usa o mês atual
    if mes is None or ano is None:
        hoje = date.today()
        mes = mes or hoje.month
        ano = ano or hoje.year

    # Filtra por mês/ano
    query_mes = query.filter(
        extract('month', Pagamento.data_pagamento) == mes,
        extract('year', Pagamento.data_pagamento) == ano
    )

    # Total recebido (geral)
    total_recebido = query.filter(Pagamento.tipo == PagamentoTipo.RECEBIDO).with_entities(
        func.sum(Pagamento.valor)
    ).scalar() or Decimal(0)

    # Total a receber (geral)
    total_a_receber = query.filter(Pagamento.tipo == PagamentoTipo.A_RECEBER).with_entities(
        func.sum(Pagamento.valor)
    ).scalar() or Decimal(0)

    # Total do mês (apenas recebido)
    total_mes = query_mes.filter(Pagamento.tipo == PagamentoTipo.RECEBIDO).with_entities(
        func.sum(Pagamento.valor)
    ).scalar() or Decimal(0)

    # Quantidade de pagamentos no mês
    quantidade_pagamentos = query_mes.count()

    return ResumoFinanceiroResponse(
        total_recebido=total_recebido,
        total_a_receber=total_a_receber,
        total_mes=total_mes,
        quantidade_pagamentos=quantidade_pagamentos,
    )


@router.get("/{pagamento_id}", response_model=PagamentoResponse)
def obter_pagamento(
    pagamento_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Obtém pagamento por ID.

    **TENANT ISOLATION:** Valida que o pagamento pertence ao personal.
    """
    query = db.query(Pagamento).filter(Pagamento.id == pagamento_id)
    query = apply_tenant_filter(query, Pagamento, personal_id)

    pagamento = query.first()

    if not pagamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado ou não pertence a este personal"
        )

    # Adiciona nome do aluno
    aluno_nome = None
    if pagamento.aluno_id:
        aluno = db.query(Aluno).filter(Aluno.id == pagamento.aluno_id).first()
        if aluno:
            aluno_nome = aluno.nome

    return PagamentoResponse(
        id=pagamento.id,
        personal_id=pagamento.personal_id,
        aluno_id=pagamento.aluno_id,
        valor=pagamento.valor,
        data_pagamento=pagamento.data_pagamento,
        tipo=pagamento.tipo,
        descricao=pagamento.descricao,
        criado_em=pagamento.criado_em,
        aluno_nome=aluno_nome,
    )


@router.post("/", response_model=PagamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_pagamento(
    pagamento_data: PagamentoCreate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Cria novo pagamento.

    **TENANT ISOLATION:** Pagamento criado automaticamente para o personal logado.
    """
    # Valida aluno (se fornecido) pertence ao personal
    if pagamento_data.aluno_id:
        aluno_query = db.query(Aluno).filter(Aluno.id == pagamento_data.aluno_id)
        aluno_query = apply_tenant_filter(aluno_query, Aluno, personal_id)
        aluno = aluno_query.first()

        if not aluno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado ou não pertence a este personal"
            )

    # Cria pagamento com personal_id automaticamente
    pagamento = Pagamento(
        **pagamento_data.model_dump(),
        personal_id=personal_id,
    )

    db.add(pagamento)
    db.commit()
    db.refresh(pagamento)

    # Adiciona nome do aluno
    aluno_nome = None
    if pagamento.aluno_id:
        aluno = db.query(Aluno).filter(Aluno.id == pagamento.aluno_id).first()
        if aluno:
            aluno_nome = aluno.nome

    return PagamentoResponse(
        id=pagamento.id,
        personal_id=pagamento.personal_id,
        aluno_id=pagamento.aluno_id,
        valor=pagamento.valor,
        data_pagamento=pagamento.data_pagamento,
        tipo=pagamento.tipo,
        descricao=pagamento.descricao,
        criado_em=pagamento.criado_em,
        aluno_nome=aluno_nome,
    )


@router.put("/{pagamento_id}", response_model=PagamentoResponse)
def atualizar_pagamento(
    pagamento_id: int,
    pagamento_data: PagamentoUpdate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Atualiza pagamento existente.

    **TENANT ISOLATION:** Valida que o pagamento pertence ao personal.
    """
    # Busca pagamento com tenant filter
    query = db.query(Pagamento).filter(Pagamento.id == pagamento_id)
    query = apply_tenant_filter(query, Pagamento, personal_id)
    pagamento = query.first()

    if not pagamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado ou não pertence a este personal"
        )

    # Atualiza apenas campos fornecidos
    update_data = pagamento_data.model_dump(exclude_unset=True)

    # Valida aluno se for alterado
    if "aluno_id" in update_data and update_data["aluno_id"]:
        aluno_query = db.query(Aluno).filter(Aluno.id == update_data["aluno_id"])
        aluno_query = apply_tenant_filter(aluno_query, Aluno, personal_id)
        aluno = aluno_query.first()

        if not aluno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado ou não pertence a este personal"
            )

    # Aplica atualizações
    for campo, valor in update_data.items():
        setattr(pagamento, campo, valor)

    db.commit()
    db.refresh(pagamento)

    # Adiciona nome do aluno
    aluno_nome = None
    if pagamento.aluno_id:
        aluno = db.query(Aluno).filter(Aluno.id == pagamento.aluno_id).first()
        if aluno:
            aluno_nome = aluno.nome

    return PagamentoResponse(
        id=pagamento.id,
        personal_id=pagamento.personal_id,
        aluno_id=pagamento.aluno_id,
        valor=pagamento.valor,
        data_pagamento=pagamento.data_pagamento,
        tipo=pagamento.tipo,
        descricao=pagamento.descricao,
        criado_em=pagamento.criado_em,
        aluno_nome=aluno_nome,
    )


@router.delete("/{pagamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pagamento(
    pagamento_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Deleta pagamento por ID.

    **TENANT ISOLATION:** Valida que o pagamento pertence ao personal.
    """
    # Busca pagamento com tenant filter
    query = db.query(Pagamento).filter(Pagamento.id == pagamento_id)
    query = apply_tenant_filter(query, Pagamento, personal_id)
    pagamento = query.first()

    if not pagamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado ou não pertence a este personal"
        )

    db.delete(pagamento)
    db.commit()

    return None
