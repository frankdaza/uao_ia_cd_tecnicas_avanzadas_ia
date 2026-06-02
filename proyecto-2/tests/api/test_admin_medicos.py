"""Pruebas del catalogo admin de medicos."""

from __future__ import annotations

import json
import uuid
from datetime import date

import pytest
from httpx import AsyncClient

from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from tests.api.conftest import PDF_FIXTURE_MINIMO


def _cuerpo_medico(
    *,
    codigo: str = "DOC-TEST-001",
    nombre: str = "Dra. Prueba Catalogo",
    especialidad: str | None = "Cirugia general",
) -> dict:
    cuerpo: dict = {
        "codigo_registro": codigo,
        "nombre_completo": nombre,
    }
    if especialidad is not None:
        cuerpo["especialidad"] = especialidad
    return cuerpo


@pytest.mark.asyncio
async def test_crear_medico_201(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json=_cuerpo_medico(),
    )
    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["codigo_registro"] == "DOC-TEST-001"
    assert cuerpo["nombre_completo"] == "Dra. Prueba Catalogo"
    assert cuerpo["especialidad"] == "Cirugia general"
    assert cuerpo["activo"] is True
    assert "created_at" in cuerpo
    assert "updated_at" in cuerpo


@pytest.mark.asyncio
async def test_listar_y_obtener_medico(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json=_cuerpo_medico(codigo="DOC-LIST-01", nombre="Dr. Listado"),
    )
    medico_id = crear.json()["id"]

    lista = await cliente_api.get(
        "/api/admin/medicos",
        headers=cabecera_admin,
        params={"limit": 10, "offset": 0},
    )
    uno = await cliente_api.get(
        f"/api/admin/medicos/{medico_id}",
        headers=cabecera_admin,
    )

    assert lista.status_code == 200
    datos = lista.json()
    assert datos["total"] >= 1
    assert len(datos["items"]) >= 1
    assert any(item["id"] == medico_id for item in datos["items"])

    assert uno.status_code == 200
    assert uno.json()["nombre_completo"] == "Dr. Listado"


@pytest.mark.asyncio
async def test_listar_filtro_activo(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json=_cuerpo_medico(codigo="DOC-INACT-01", nombre="Dr. Inactivo"),
    )
    medico_id = crear.json()["id"]
    borrar = await cliente_api.delete(
        f"/api/admin/medicos/{medico_id}",
        headers=cabecera_admin,
    )
    assert borrar.status_code == 204

    activos = await cliente_api.get(
        "/api/admin/medicos",
        headers=cabecera_admin,
        params={"activo": True},
    )
    inactivos = await cliente_api.get(
        "/api/admin/medicos",
        headers=cabecera_admin,
        params={"activo": False},
    )
    assert activos.status_code == 200
    assert inactivos.status_code == 200
    ids_activos = {item["id"] for item in activos.json()["items"]}
    ids_inactivos = {item["id"] for item in inactivos.json()["items"]}
    assert medico_id not in ids_activos
    assert medico_id in ids_inactivos


@pytest.mark.asyncio
async def test_patch_actualiza_campos_y_updated_at(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json=_cuerpo_medico(codigo="DOC-PATCH-01", nombre="Nombre original"),
    )
    medico_id = crear.json()["id"]
    updated_antes = crear.json()["updated_at"]

    parche = await cliente_api.patch(
        f"/api/admin/medicos/{medico_id}",
        headers=cabecera_admin,
        json={"nombre_completo": "Nombre actualizado"},
    )
    assert parche.status_code == 200
    cuerpo = parche.json()
    assert cuerpo["nombre_completo"] == "Nombre actualizado"
    assert cuerpo["updated_at"] >= updated_antes


@pytest.mark.asyncio
async def test_409_codigo_duplicado(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json=_cuerpo_medico(codigo="DOC-DUP", nombre="Uno"),
    )
    resp = await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json=_cuerpo_medico(codigo="DOC-DUP", nombre="Dos"),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_409_patch_codigo_duplicado(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json=_cuerpo_medico(codigo="DOC-A", nombre="Medico A"),
    )
    crear_b = await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json=_cuerpo_medico(codigo="DOC-B", nombre="Medico B"),
    )
    resp = await cliente_api.patch(
        f"/api/admin/medicos/{crear_b.json()['id']}",
        headers=cabecera_admin,
        json={"codigo_registro": "DOC-A"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_404_medico_inexistente(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/medicos/00000000-0000-0000-0000-000000000099",
        headers=cabecera_admin,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_409_caso_activo_con_cirujano(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
    app_api,
) -> None:
    codigo = "DOC-CASO-ACTIVO"
    crear = await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json=_cuerpo_medico(codigo=codigo, nombre="Dr. Con caso activo"),
    )
    medico_id = crear.json()["id"]

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_tipo = RepositorioTiposProcedimiento(sesion)
        tipo = await repo_tipo.crear(
            codigo=f"tipo-{uuid.uuid4().hex[:6]}",
            nombre="Tipo para caso medico",
            indexacion_estado="ok",
        )
        repo_casos = RepositorioCasosPostoperatorio(sesion)
        await repo_casos.crear(
            paciente_doc_id="PAC-MED-DEL",
            paciente_nombre="Paciente Medico Delete",
            tipo_procedimiento_id=tipo.id,
            cirujano_id=codigo,
            cirujano_nombre="Dr. Con caso activo",
            fecha_cirugia=date(2026, 5, 1),
            estado="activo",
        )
        await sesion.commit()

    resp = await cliente_api.delete(
        f"/api/admin/medicos/{medico_id}",
        headers=cabecera_admin,
    )
    assert resp.status_code == 409
    assert "caso" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_401_sin_cabecera(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.get("/api/admin/medicos")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_crear_procedimiento_multipart_no_afecta_medicos(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    """Smoke: rutas de medicos JSON independientes del catalogo multipart."""
    resp = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files={
            "metadata": (
                None,
                json.dumps({"codigo": "proc-iso", "nombre": "Proc aislado"}),
                "application/json",
            ),
            "archivo": ("protocolo.pdf", PDF_FIXTURE_MINIMO, "application/pdf"),
        },
    )
    assert resp.status_code == 201
