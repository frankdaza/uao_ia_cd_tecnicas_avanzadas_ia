"""Pruebas de scroll y filtros de payload (Qdrant :memory:)."""

from __future__ import annotations

import uuid

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.rag.runtime.recuperador_listados import RecuperadorListados, _construir_filtro


def _coleccion_vacia(cliente: QdrantClient, nombre: str) -> None:
    if cliente.collection_exists(nombre):
        cliente.delete_collection(nombre)
    cliente.create_collection(
        collection_name=nombre,
        vectors_config=VectorParams(size=2, distance=Distance.COSINE),
    )


@pytest.fixture
def cliente_memoria() -> QdrantClient:
    c = QdrantClient(location=":memory:")
    return c


def test_construir_filtro_none_si_vacio() -> None:
    assert _construir_filtro({}) is None


def test_conteo_simple(cliente_memoria: QdrantClient) -> None:
    col = "col_listado_a"
    _coleccion_vacia(cliente_memoria, col)
    puntos: list[PointStruct] = []
    for i in range(3):
        puntos.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.1, float(i) * 0.01],
                payload={
                    "tipo_pagina": "ficha_medico",
                    "especialidad": ["Pediatria"],
                    "sedes": ["Sede Valle del Lili"],
                    "nombre_medico": f"Medico {i}",
                    "source_url": f"https://ejemplo.test/{i}",
                    "archivo": f"a{i}.md",
                },
            )
        )
    cliente_memoria.upsert(collection_name=col, points=puntos)
    rec = RecuperadorListados(cliente_memoria, col)
    res = rec.listar(
        {"tipo_pagina": "ficha_medico", "especialidad": "Pediatria"}, limite=10
    )
    assert res.conteo == 3
    assert not res.muestra_truncada


def test_listado_por_sede(cliente_memoria: QdrantClient) -> None:
    col = "col_listado_b"
    _coleccion_vacia(cliente_memoria, col)
    cliente_memoria.upsert(
        collection_name=col,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.2, 0.2],
                payload={
                    "tipo_pagina": "ficha_medico",
                    "especialidad": ["Pediatria"],
                    "sedes": ["Sede Alfaguara"],
                    "nombre_medico": "Solo Alfaguara",
                    "source_url": "https://ejemplo.test/alfa",
                    "archivo": "b.md",
                },
            ),
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.3, 0.3],
                payload={
                    "tipo_pagina": "ficha_medico",
                    "especialidad": ["Pediatria"],
                    "sedes": ["Sede Valle del Lili"],
                    "nombre_medico": "Solo Lili",
                    "source_url": "https://ejemplo.test/lili",
                    "archivo": "c.md",
                },
            ),
        ],
    )
    rec = RecuperadorListados(cliente_memoria, col)
    res = rec.listar(
        {
            "tipo_pagina": "ficha_medico",
            "especialidad": "Pediatria",
            "sedes": ["Sede Valle del Lili"],
        },
        limite=10,
    )
    assert res.conteo == 1
    assert res.items[0].nombre == "Solo Lili"


def test_sin_matches(cliente_memoria: QdrantClient) -> None:
    col = "col_listado_c"
    _coleccion_vacia(cliente_memoria, col)
    cliente_memoria.upsert(
        collection_name=col,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.4, 0.4],
                payload={
                    "tipo_pagina": "servicio",
                    "especialidad": ["Oncologia"],
                    "sedes": [],
                    "nombre_medico": None,
                    "titulo": "Servicio X",
                    "source_url": "",
                    "archivo": "s.md",
                },
            ),
        ],
    )
    rec = RecuperadorListados(cliente_memoria, col)
    res = rec.listar({"tipo_pagina": "ficha_medico"}, limite=10)
    assert res.conteo == 0
    assert res.items == []


def test_muestra_truncada(cliente_memoria: QdrantClient) -> None:
    col = "col_listado_d"
    _coleccion_vacia(cliente_memoria, col)
    pts = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.5, i * 0.001],
            payload={
                "tipo_pagina": "ficha_medico",
                "especialidad": ["Cardiologia"],
                "sedes": [],
                "nombre_medico": f"C{i}",
                "source_url": f"https://ejemplo.test/c{i}",
                "archivo": f"d{i}.md",
            },
        )
        for i in range(5)
    ]
    cliente_memoria.upsert(collection_name=col, points=pts)
    rec = RecuperadorListados(cliente_memoria, col)
    res = rec.listar(
        {"tipo_pagina": "ficha_medico", "especialidad": "Cardiologia"}, limite=2
    )
    assert res.conteo == 5
    assert res.muestra_truncada
    assert len(res.items) == 2


def test_listado_por_tipo_pagina_sede(cliente_memoria: QdrantClient) -> None:
    """Catalogo institucional: solo chunks con tipo_pagina=sede (paginas sedes-*.md)."""
    col = "col_listado_sede"
    _coleccion_vacia(cliente_memoria, col)
    cliente_memoria.upsert(
        collection_name=col,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.6, 0.1],
                payload={
                    "tipo_pagina": "sede",
                    "especialidad": [],
                    "sedes": [],
                    "nombre_medico": None,
                    "titulo": "Sede Principal",
                    "source_url": "https://ejemplo.test/sedes/principal",
                    "archivo": "valledellili-org/sedes-sede-principal.md",
                },
            ),
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.6, 0.2],
                payload={
                    "tipo_pagina": "sede",
                    "especialidad": [],
                    "sedes": [],
                    "nombre_medico": None,
                    "titulo": "Sede Limonar",
                    "source_url": "https://ejemplo.test/sedes/limonar",
                    "archivo": "valledellili-org/sedes-sede-limonar.md",
                },
            ),
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.7, 0.1],
                payload={
                    "tipo_pagina": "otro",
                    "especialidad": [],
                    "sedes": ["Sede Limonar"],
                    "nombre_medico": None,
                    "titulo": "Nota con mencion de sede",
                    "source_url": "https://ejemplo.test/nota/1",
                    "archivo": "valledellili-org/nota.md",
                },
            ),
        ],
    )
    rec = RecuperadorListados(cliente_memoria, col)
    res = rec.listar({"tipo_pagina": "sede"}, limite=20)
    assert res.conteo == 2
    archivos = {it.archivo for it in res.items}
    assert "valledellili-org/sedes-sede-principal.md" in archivos
    assert "valledellili-org/sedes-sede-limonar.md" in archivos
    assert all("sedes-sede" in (it.archivo or "") for it in res.items)
