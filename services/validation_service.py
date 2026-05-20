"""Validações de negócio — cadastro de devoluções."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Optional


@dataclass
class ValidationResult:
    ok: bool
    message: str = ""


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def validar_cadastro_devolucao(
    data_devolucao: Optional[date],
    nf_nfd: str,
    motivo_devolucao: str,
    observacao: str,
    usuario: str,
    sap_encontrado: bool,
    nf_duplicada: bool,
    dados_sap_validos: bool,
) -> ValidationResult:
    if data_devolucao is None:
        return ValidationResult(False, "Informe a data da devolução.")

    nf = _texto(nf_nfd)
    if not nf:
        return ValidationResult(False, "Informe o número NF/NFD.")

    if not _texto(motivo_devolucao):
        return ValidationResult(False, "Selecione o motivo da devolução.")

    if not _texto(usuario):
        return ValidationResult(False, "Informe o responsável.")

    if not sap_encontrado:
        return ValidationResult(False, "Número NF não localizado na base SAP.")

    if not dados_sap_validos:
        return ValidationResult(False, "Dados SAP inválidos para esta NF/NFD.")

    if nf_duplicada:
        return ValidationResult(False, f"A NF/NFD «{nf}» já possui devolução cadastrada.")

    return ValidationResult(True, "Validação concluída.")


def validar_edicao_devolucao(
    data_devolucao: Optional[date],
    nf_nfd: str,
    motivo_devolucao: str,
    editor: str,
    sap_encontrado: bool,
    nf_duplicada: bool,
    dados_sap_validos: bool,
) -> ValidationResult:
    if data_devolucao is None:
        return ValidationResult(False, "Informe a data da devolução.")

    nf = _texto(nf_nfd)
    if not nf:
        return ValidationResult(False, "Informe o número NF/NFD.")

    if not _texto(motivo_devolucao):
        return ValidationResult(False, "Selecione o motivo da devolução.")

    if not _texto(editor):
        return ValidationResult(False, "Usuário da edição não identificado.")

    if not sap_encontrado:
        return ValidationResult(False, "Número NF não localizado na base SAP.")

    if not dados_sap_validos:
        return ValidationResult(False, "Dados SAP inválidos para esta NF/NFD.")

    if nf_duplicada:
        return ValidationResult(False, f"A NF/NFD «{nf}» já possui devolução cadastrada.")

    return ValidationResult(True, "Validação concluída.")
