"""Schemas Pydantic para Fichas de Treino e Exercícios."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============= Exercício =============

class ExercicioBase(BaseModel):
    """Dados base de um exercício."""
    nome: str = Field(..., min_length=1, max_length=200, description="Nome do exercício")
    descricao: Optional[str] = Field(None, description="Instruções, séries/reps, etc")
    duracao_segundos: int = Field(..., ge=0, description="Duração do exercício em segundos")
    descanso_segundos: int = Field(default=0, ge=0, description="Tempo de descanso após exercício")
    ordem: int = Field(..., ge=0, description="Posição na sequência do treino")


class ExercicioCreate(ExercicioBase):
    """Schema para criar exercício."""
    pass


class ExercicioUpdate(BaseModel):
    """Schema para atualizar exercício."""
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    descricao: Optional[str] = None
    duracao_segundos: Optional[int] = Field(None, ge=0)
    descanso_segundos: Optional[int] = Field(None, ge=0)
    ordem: Optional[int] = Field(None, ge=0)


class ExercicioResponse(ExercicioBase):
    """Schema de resposta com exercício completo."""
    id: int
    ficha_treino_id: int
    criado_em: datetime

    class Config:
        from_attributes = True


# ============= Ficha de Treino =============

class FichaTreinoBase(BaseModel):
    """Dados base de uma ficha de treino."""
    nome: str = Field(..., min_length=1, max_length=200, description="Nome da ficha")
    descricao: Optional[str] = Field(None, description="Descrição/objetivo da ficha")
    aluno_id: Optional[int] = Field(None, description="Aluno (null = template genérico)")
    ativa: bool = Field(default=True, description="Se a ficha está ativa")


class FichaTreinoCreate(FichaTreinoBase):
    """Schema para criar ficha de treino."""
    exercicios: Optional[List[ExercicioCreate]] = Field(
        default=[],
        description="Lista de exercícios (opcional na criação)"
    )


class FichaTreinoUpdate(BaseModel):
    """Schema para atualizar ficha de treino."""
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    descricao: Optional[str] = None
    aluno_id: Optional[int] = None
    ativa: Optional[bool] = None


class FichaTreinoResponse(FichaTreinoBase):
    """Schema de resposta com ficha completa."""
    id: int
    personal_id: int
    criado_em: datetime
    atualizado_em: datetime
    exercicios: List[ExercicioResponse] = []

    class Config:
        from_attributes = True


class FichaTreinoListResponse(BaseModel):
    """Schema de resposta para listagem de fichas."""
    total: int
    fichas: List[FichaTreinoResponse]


# ============= Reordenação de Exercícios =============

class ReordenarExerciciosRequest(BaseModel):
    """Schema para reordenar exercícios."""
    exercicio_ids: List[int] = Field(..., description="IDs dos exercícios na nova ordem")
