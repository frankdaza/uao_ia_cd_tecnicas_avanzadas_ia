"""Repositorios async TAAM."""

from src.persistencia.repositorios.alertas_triage import RepositorioAlertasTriage
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram

__all__ = [
    "RepositorioAlertasTriage",
    "RepositorioCasosPostoperatorio",
    "RepositorioTiposProcedimiento",
    "RepositorioVinculosTelegram",
]
