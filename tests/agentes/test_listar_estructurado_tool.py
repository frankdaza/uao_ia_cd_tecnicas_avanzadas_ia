"""Pruebas de la tool LangChain ``listar_estructurado``."""

from __future__ import annotations

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.agentes.herramientas.listar_estructurado_tool import (
    crear_listar_estructurado_tool,
)
from src.rag.runtime.recuperador_listados import RecuperadorListados


def test_tool_invoke_con_recuperador_inyectado() -> None:
    cliente = QdrantClient(location=":memory:")
    col = "col_tool_list"
    cliente.create_collection(
        collection_name=col,
        vectors_config=VectorParams(size=2, distance=Distance.COSINE),
    )
    cliente.upsert(
        collection_name=col,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.1, 0.2],
                payload={
                    "tipo_pagina": "ficha_medico",
                    "especialidad": ["Pediatria"],
                    "sedes": [],
                    "nombre_medico": "Dr Inyectado",
                    "source_url": "https://x.test",
                    "archivo": "z.md",
                },
            ),
        ],
    )
    rec = RecuperadorListados(cliente, col)
    tool = crear_listar_estructurado_tool(recuperador=rec)
    salida = tool.invoke(
        {"tipo_pagina": "ficha_medico", "especialidad": "Pediatria", "limite": 10},
    )
    assert salida["conteo"] == 1
    assert salida["items"][0]["nombre"] == "Dr Inyectado"


def test_listar_sin_filtro_hace_scroll_acotado() -> None:
    """Sin filtros de payload se deduplica por scroll global acotado (no conteo fijo en cero)."""
    cliente = QdrantClient(location=":memory:")
    col = "col_sin_filtro"
    cliente.create_collection(
        collection_name=col,
        vectors_config=VectorParams(size=2, distance=Distance.COSINE),
    )
    cliente.upsert(
        collection_name=col,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.1, 0.2],
                payload={
                    "tipo_pagina": "ficha_medico",
                    "nombre_medico": "Dr A",
                    "source_url": "https://a.test",
                    "archivo": "a.md",
                },
            ),
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.2, 0.3],
                payload={
                    "tipo_pagina": "servicio",
                    "titulo": "Servicio B",
                    "source_url": "https://b.test",
                    "archivo": "b.md",
                },
            ),
        ],
    )
    rec = RecuperadorListados(cliente, col)
    res = rec.listar({}, limite=10)
    assert res.conteo == 2
    assert len(res.items) == 2
    assert res.filtros_aplicados.get("sin_filtro_payload") is True
