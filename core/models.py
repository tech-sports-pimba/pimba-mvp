"""Modelos ORM SQLAlchemy."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Date, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
from core.database import Base
from core.enums import UserRole, AgendamentoStatus, PagamentoTipo


class User(Base):
    """Modelo base de usuário com autenticação Firebase."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.ALUNO)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    personal = relationship("Personal", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Personal(Base):
    """Modelo de Personal Trainer (TENANT)."""

    __tablename__ = "personals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    telefone = Column(String(50))
    especializacao = Column(String(255))  # Ex: "Funcional", "Musculação"
    bio = Column(Text)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="personal")
    alunos = relationship("Aluno", back_populates="personal", cascade="all, delete-orphan")
    agendamentos = relationship("Agendamento", back_populates="personal", cascade="all, delete-orphan")
    fichas_treino = relationship("FichaTreino", back_populates="personal", cascade="all, delete-orphan")
    pagamentos = relationship("Pagamento", back_populates="personal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Personal(id={self.id}, user_id={self.user_id})>"


class Aluno(Base):
    """Modelo de Aluno (vinculado a um Personal)."""

    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    personal_id = Column(Integer, ForeignKey("personals.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Para quando aluno tiver acesso
    nome = Column(String(255), nullable=False, index=True)
    email = Column(String(255))
    telefone = Column(String(50))
    data_nascimento = Column(Date)
    objetivo = Column(Text)
    local_padrao = Column(String(500))  # Endereço/local padrão de treino
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    personal = relationship("Personal", back_populates="alunos")
    user = relationship("User")
    agendamentos = relationship("Agendamento", back_populates="aluno")
    fichas_treino = relationship("FichaTreino", back_populates="aluno")
    registros_evolucao = relationship("RegistroEvolucao", back_populates="aluno", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Aluno(id={self.id}, nome='{self.nome}', personal_id={self.personal_id})>"


class Agendamento(Base):
    """Modelo de Agendamento de treino."""

    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    personal_id = Column(Integer, ForeignKey("personals.id"), nullable=False, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False, index=True)
    data_hora_inicio = Column(DateTime, nullable=False, index=True)
    duracao_minutos = Column(Integer, nullable=False, default=60)
    local = Column(String(255))  # Ex: "Academia X", "Casa do aluno", "Online"
    observacoes = Column(Text)
    status = Column(SQLEnum(AgendamentoStatus), nullable=False, default=AgendamentoStatus.AGENDADO)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    personal = relationship("Personal", back_populates="agendamentos")
    aluno = relationship("Aluno", back_populates="agendamentos")

    def __repr__(self):
        return f"<Agendamento(id={self.id}, personal_id={self.personal_id}, aluno_id={self.aluno_id}, data={self.data_hora_inicio})>"


class FichaTreino(Base):
    """Modelo de Ficha de Treino."""

    __tablename__ = "fichas_treino"

    id = Column(Integer, primary_key=True, index=True)
    personal_id = Column(Integer, ForeignKey("personals.id"), nullable=False, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=True, index=True)  # Nullable = template
    nome = Column(String(255), nullable=False)
    descricao = Column(Text)
    ativa = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    personal = relationship("Personal", back_populates="fichas_treino")
    aluno = relationship("Aluno", back_populates="fichas_treino")
    exercicios = relationship("Exercicio", back_populates="ficha_treino", cascade="all, delete-orphan", order_by="Exercicio.ordem")

    def __repr__(self):
        return f"<FichaTreino(id={self.id}, nome='{self.nome}', personal_id={self.personal_id})>"


class Exercicio(Base):
    """Modelo de Exercício dentro de uma Ficha de Treino."""

    __tablename__ = "exercicios"

    id = Column(Integer, primary_key=True, index=True)
    ficha_treino_id = Column(Integer, ForeignKey("fichas_treino.id"), nullable=False, index=True)
    ordem = Column(Integer, nullable=False)  # Posição na sequência
    nome = Column(String(255), nullable=False)
    descricao = Column(Text)  # Ex: "3x12", "40kg", instruções
    duracao_segundos = Column(Integer, default=0)  # Para timer
    descanso_segundos = Column(Integer, default=0)  # Timer de descanso
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    ficha_treino = relationship("FichaTreino", back_populates="exercicios")

    def __repr__(self):
        return f"<Exercicio(id={self.id}, nome='{self.nome}', ordem={self.ordem})>"


class Pagamento(Base):
    """Modelo de Pagamento (controle financeiro simples)."""

    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True, index=True)
    personal_id = Column(Integer, ForeignKey("personals.id"), nullable=False, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=True, index=True)
    valor = Column(Numeric(10, 2), nullable=False)
    data_pagamento = Column(Date, nullable=False, index=True)
    tipo = Column(SQLEnum(PagamentoTipo), nullable=False, default=PagamentoTipo.RECEBIDO)
    descricao = Column(Text)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    personal = relationship("Personal", back_populates="pagamentos")
    aluno = relationship("Aluno")

    def __repr__(self):
        return f"<Pagamento(id={self.id}, valor={self.valor}, personal_id={self.personal_id})>"


class RegistroEvolucao(Base):
    """Modelo de Registro de Evolução do Aluno."""

    __tablename__ = "registros_evolucao"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False, index=True)
    data_registro = Column(Date, nullable=False, index=True)
    peso_kg = Column(Numeric(5, 2))
    medidas = Column(JSON)  # Ex: {"cintura": 80, "braco_dir": 35}
    observacoes = Column(Text)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    aluno = relationship("Aluno", back_populates="registros_evolucao")

    def __repr__(self):
        return f"<RegistroEvolucao(id={self.id}, aluno_id={self.aluno_id}, data={self.data_registro})>"
