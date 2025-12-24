"""Enums para o sistema."""
import enum


class UserRole(str, enum.Enum):
    """Roles de usuários no sistema."""
    ADMIN = "admin"
    PERSONAL = "personal"
    ALUNO = "aluno"


class AgendamentoStatus(str, enum.Enum):
    """Status de agendamentos."""
    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    REALIZADO = "realizado"


class PagamentoTipo(str, enum.Enum):
    """Tipos de pagamento."""
    RECEBIDO = "recebido"
    A_RECEBER = "a_receber"
