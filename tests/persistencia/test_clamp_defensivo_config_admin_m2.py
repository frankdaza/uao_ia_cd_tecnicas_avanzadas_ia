"""Lectura defensiva (clamp + warning) de parametros RAG persistidos en config_admin_m2."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from src.api.configuracion import Configuracion
from src.api.servicios.agente_m2_config import ServicioAgenteM2Config
from src.persistencia.modelos import ConfigAdminM2


def _fila_con_valor(**kwargs: object) -> ConfigAdminM2:
    base = ConfigAdminM2(
        id=1,
        version=1,
        updated_at=datetime.now(UTC),
    )
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


@pytest.mark.parametrize(
    ("campo_attr", "valor_bd", "esperado"),
    [
        ("rag_top_k", 999, 50),
        ("rag_top_k", 0, 1),
        ("rag_score_minimo", -0.5, 0.0),
        ("rag_score_minimo", 2.0, 1.0),
        ("rag_top_k_inicial", 500, 200),
        ("rag_mmr_lambda", 9.0, 1.0),
        ("rag_mmr_lambda", -1.0, 0.0),
        ("rag_reranker_top_n_entrada", 100, 50),
        ("rag_reranker_batch_size", 9999, 256),
        ("historial_turnos_max", 5000, 200),
        ("historial_dias_max", 900, 365),
    ],
)
def test_clamp_valor_fuera_de_rango_registra_warning(
    caplog: pytest.LogCaptureFixture,
    campo_attr: str,
    valor_bd: float | int,
    esperado: float | int,
) -> None:
    caplog.set_level("WARNING")
    fila = _fila_con_valor(**{campo_attr: valor_bd})
    sesion = AsyncMock(spec=AsyncSession)
    cfg = Configuracion()
    svc = ServicioAgenteM2Config(sesion, cfg=cfg)

    if campo_attr == "rag_top_k":
        assert svc.rag_top_k_efectivo(fila) == int(esperado)
    elif campo_attr == "rag_score_minimo":
        assert abs(svc.rag_score_minimo_efectivo(fila) - float(esperado)) < 1e-9
    elif campo_attr == "rag_top_k_inicial":
        assert svc.rag_top_k_inicial_efectivo(fila) == int(esperado)
    elif campo_attr == "rag_mmr_lambda":
        assert abs(svc.rag_mmr_lambda_efectivo(fila) - float(esperado)) < 1e-9
    elif campo_attr == "rag_reranker_top_n_entrada":
        assert svc.rag_reranker_top_n_entrada_efectivo(fila) == int(esperado)
    elif campo_attr == "rag_reranker_batch_size":
        assert svc.rag_reranker_batch_size_efectivo(fila) == int(esperado)
    elif campo_attr == "historial_turnos_max":
        assert svc.historial_turnos_max_efectivo(fila) == int(esperado)
    elif campo_attr == "historial_dias_max":
        assert svc.historial_dias_max_efectivo(fila) == int(esperado)
    else:
        raise AssertionError(campo_attr)

    assert "fuera de rango" in caplog.text
