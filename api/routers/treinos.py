"""Router de Fichas de Treino e Exercícios."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from core.database import get_db
from core.models import FichaTreino, Exercicio, Aluno
from api.schemas.treinos import (
    FichaTreinoCreate,
    FichaTreinoUpdate,
    FichaTreinoResponse,
    FichaTreinoListResponse,
    ExercicioCreate,
    ExercicioUpdate,
    ExercicioResponse,
    ReordenarExerciciosRequest,
)
from auth.dependencies import get_personal_id, apply_tenant_filter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============= FICHAS DE TREINO =============

@router.get("/", response_model=FichaTreinoListResponse)
def listar_fichas(
    aluno_id: Optional[int] = None,
    ativa: Optional[bool] = None,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Lista fichas de treino do personal.

    Filtros opcionais:
    - aluno_id: Filtra por aluno específico
    - ativa: Filtra por fichas ativas/inativas
    """
    query = db.query(FichaTreino)

    # Aplica filtro de tenant
    query = apply_tenant_filter(query, FichaTreino, personal_id)

    # Filtros opcionais
    if aluno_id is not None:
        query = query.filter(FichaTreino.aluno_id == aluno_id)

    if ativa is not None:
        query = query.filter(FichaTreino.ativa == ativa)

    # Ordena por mais recente
    query = query.order_by(FichaTreino.criado_em.desc())

    fichas = query.all()

    return {"total": len(fichas), "fichas": fichas}


@router.get("/{ficha_id}", response_model=FichaTreinoResponse)
def buscar_ficha(
    ficha_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """Busca ficha de treino por ID."""
    query = db.query(FichaTreino).filter(FichaTreino.id == ficha_id)
    query = apply_tenant_filter(query, FichaTreino, personal_id)

    ficha = query.first()

    if not ficha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ficha de treino não encontrada",
        )

    return ficha


@router.post("/", response_model=FichaTreinoResponse, status_code=status.HTTP_201_CREATED)
def criar_ficha(
    dados: FichaTreinoCreate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Cria nova ficha de treino.

    Pode incluir exercícios na criação ou adicionar depois.
    """
    # Valida aluno (se fornecido)
    if dados.aluno_id:
        aluno = db.query(Aluno).filter(Aluno.id == dados.aluno_id).first()
        if not aluno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado",
            )

        # Valida tenant do aluno
        if personal_id and aluno.personal_id != personal_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Aluno não pertence a este personal",
            )

        # Define personal_id baseado no aluno
        ficha_personal_id = aluno.personal_id
    else:
        # Template genérico
        if not personal_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Personal ID necessário para criar template",
            )
        ficha_personal_id = personal_id

    # Cria ficha
    ficha = FichaTreino(
        personal_id=ficha_personal_id,
        aluno_id=dados.aluno_id,
        nome=dados.nome,
        descricao=dados.descricao,
        ativa=dados.ativa,
    )
    db.add(ficha)
    db.flush()

    # Adiciona exercícios (se fornecidos)
    if dados.exercicios:
        for exercicio_data in dados.exercicios:
            exercicio = Exercicio(
                ficha_treino_id=ficha.id,
                nome=exercicio_data.nome,
                descricao=exercicio_data.descricao,
                duracao_segundos=exercicio_data.duracao_segundos,
                descanso_segundos=exercicio_data.descanso_segundos,
                ordem=exercicio_data.ordem,
            )
            db.add(exercicio)

    db.commit()
    db.refresh(ficha)

    logger.info(f"Ficha de treino criada: {ficha.id} (personal={ficha_personal_id})")

    return ficha


@router.put("/{ficha_id}", response_model=FichaTreinoResponse)
def atualizar_ficha(
    ficha_id: int,
    dados: FichaTreinoUpdate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """Atualiza ficha de treino."""
    query = db.query(FichaTreino).filter(FichaTreino.id == ficha_id)
    query = apply_tenant_filter(query, FichaTreino, personal_id)

    ficha = query.first()

    if not ficha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ficha de treino não encontrada",
        )

    # Atualiza campos fornecidos
    update_data = dados.model_dump(exclude_unset=True)

    # Valida aluno_id se fornecido
    if "aluno_id" in update_data and update_data["aluno_id"]:
        aluno = db.query(Aluno).filter(Aluno.id == update_data["aluno_id"]).first()
        if not aluno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado",
            )
        if personal_id and aluno.personal_id != personal_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Aluno não pertence a este personal",
            )

    for key, value in update_data.items():
        setattr(ficha, key, value)

    db.commit()
    db.refresh(ficha)

    return ficha


@router.delete("/{ficha_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_ficha(
    ficha_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """Deleta ficha de treino e seus exercícios."""
    query = db.query(FichaTreino).filter(FichaTreino.id == ficha_id)
    query = apply_tenant_filter(query, FichaTreino, personal_id)

    ficha = query.first()

    if not ficha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ficha de treino não encontrada",
        )

    # Deleta exercícios associados (cascade deve fazer isso, mas garante)
    db.query(Exercicio).filter(Exercicio.ficha_treino_id == ficha_id).delete()

    db.delete(ficha)
    db.commit()

    logger.info(f"Ficha de treino deletada: {ficha_id}")


# ============= EXERCÍCIOS =============

@router.post("/{ficha_id}/exercicios", response_model=ExercicioResponse, status_code=status.HTTP_201_CREATED)
def adicionar_exercicio(
    ficha_id: int,
    dados: ExercicioCreate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """Adiciona exercício a uma ficha de treino."""
    # Valida ficha
    query = db.query(FichaTreino).filter(FichaTreino.id == ficha_id)
    query = apply_tenant_filter(query, FichaTreino, personal_id)

    ficha = query.first()

    if not ficha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ficha de treino não encontrada",
        )

    # Cria exercício
    exercicio = Exercicio(
        ficha_treino_id=ficha_id,
        nome=dados.nome,
        descricao=dados.descricao,
        duracao_segundos=dados.duracao_segundos,
        descanso_segundos=dados.descanso_segundos,
        ordem=dados.ordem,
    )
    db.add(exercicio)
    db.commit()
    db.refresh(exercicio)

    return exercicio


@router.put("/exercicios/{exercicio_id}", response_model=ExercicioResponse)
def atualizar_exercicio(
    exercicio_id: int,
    dados: ExercicioUpdate,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """Atualiza exercício."""
    exercicio = db.query(Exercicio).filter(Exercicio.id == exercicio_id).first()

    if not exercicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercício não encontrado",
        )

    # Valida tenant através da ficha
    ficha = db.query(FichaTreino).filter(FichaTreino.id == exercicio.ficha_treino_id).first()
    if personal_id and ficha.personal_id != personal_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Exercício não pertence a este personal",
        )

    # Atualiza campos fornecidos
    update_data = dados.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(exercicio, key, value)

    db.commit()
    db.refresh(exercicio)

    return exercicio


@router.delete("/exercicios/{exercicio_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_exercicio(
    exercicio_id: int,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """Deleta exercício."""
    exercicio = db.query(Exercicio).filter(Exercicio.id == exercicio_id).first()

    if not exercicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercício não encontrado",
        )

    # Valida tenant através da ficha
    ficha = db.query(FichaTreino).filter(FichaTreino.id == exercicio.ficha_treino_id).first()
    if personal_id and ficha.personal_id != personal_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Exercício não pertence a este personal",
        )

    db.delete(exercicio)
    db.commit()


@router.put("/{ficha_id}/exercicios/reordenar", response_model=List[ExercicioResponse])
def reordenar_exercicios(
    ficha_id: int,
    dados: ReordenarExerciciosRequest,
    db: Session = Depends(get_db),
    personal_id: Optional[int] = Depends(get_personal_id),
):
    """
    Reordena exercícios de uma ficha.

    Recebe lista de IDs na nova ordem e atualiza campo 'ordem'.
    """
    # Valida ficha
    query = db.query(FichaTreino).filter(FichaTreino.id == ficha_id)
    query = apply_tenant_filter(query, FichaTreino, personal_id)

    ficha = query.first()

    if not ficha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ficha de treino não encontrada",
        )

    # Busca todos os exercícios da ficha
    exercicios = db.query(Exercicio).filter(Exercicio.ficha_treino_id == ficha_id).all()
    exercicios_map = {ex.id: ex for ex in exercicios}

    # Valida que todos os IDs existem e pertencem à ficha
    for ex_id in dados.exercicio_ids:
        if ex_id not in exercicios_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exercício {ex_id} não pertence a esta ficha",
            )

    # Atualiza ordem
    for nova_ordem, ex_id in enumerate(dados.exercicio_ids):
        exercicios_map[ex_id].ordem = nova_ordem

    db.commit()

    # Retorna exercícios reordenados
    return sorted(exercicios, key=lambda x: x.ordem)
