"""
Modelos SQLAlchemy — prontos para PostgreSQL / Supabase.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum as SQLEnum, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PerfilUsuario(str, Enum):
    ADMIN = "admin"
    OPERADOR = "operador"
    SUPERVISOR = "supervisor"
    VISUALIZADOR = "visualizador"


class StatusDevolucao(str, Enum):
    """Mantido para compatibilidade com cards operacionais."""

    PENDENTE = "pendente"
    EM_CONFERENCIA = "em_conferencia"
    FINALIZADA = "finalizada"
    AGUARDANDO_COLETA = "aguardando_coleta"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    perfil: Mapped[PerfilUsuario] = mapped_column(
        SQLEnum(PerfilUsuario, native_enum=False, length=20),
        default=PerfilUsuario.OPERADOR,
        nullable=False,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    empresa_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Motivo(Base):
    __tablename__ = "motivos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    descricao: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


class DadoSAP(Base):
    __tablename__ = "dados_sap"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nf_nfd: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    data_emissao_nf: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cod_cliente: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    cliente: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bairro: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vendedor: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    valor_nf: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    arquivo_origem: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    data_importacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Devolucao(Base):
    __tablename__ = "devolucoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_lancamento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    usuario: Mapped[str] = mapped_column(String(120), nullable=False)
    usuario_ultima_edicao: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    data_devolucao: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_emissao_nf: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nf_nfd: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    cod_cliente: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    cliente: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vendedor: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    valor_nf: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bairro: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    motivo_devolucao: Mapped[str] = mapped_column(String(200), nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
