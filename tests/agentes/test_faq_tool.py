"""Tests de la tool determinista FAQ (JSON) sin LLM ni Qdrant."""

from __future__ import annotations

import pytest

from src.agentes.herramientas.faq_tool import (
    ArchivoFaqStructuredAusenteError,
    buscar_faq,
    crear_faq_tool,
    invalidar_cache_faqs,
)
from src.api.configuracion import obtener_configuracion


@pytest.fixture(autouse=True)
def _restaurar_cache_config_y_faq() -> None:
    """Cada prueba arranca sin cache de FAQs ni de settings colgada de otra prueba."""
    invalidar_cache_faqs()
    obtener_configuracion.cache_clear()
    yield
    invalidar_cache_faqs()
    obtener_configuracion.cache_clear()


def test_buscar_faq_caso_positivo_pbx() -> None:
    r = buscar_faq(
        "telefono llamar PBX linea contacto 602 331 9090 central",
    )
    assert r is not None
    assert r.id == "fvl-linea-pbx-general"


def test_buscar_faq_pregunta_meta_prompt_pbx() -> None:
    """Frase de ejemplo del meta-prompt del router (PBX) debe matchear la FAQ."""
    consulta = "¿Cual es el teléfono, o contacto, número de la linea PBX?"
    r = buscar_faq(consulta)
    assert r is not None
    assert r.id == "fvl-linea-pbx-general"


def test_buscar_faq_caso_positivo_siau_horario() -> None:
    r = buscar_faq(
        "horario SIAU PQRS atencion usuario lunes viernes jornada queja",
    )
    assert r is not None
    assert r.id == "fvl-siau-pqrs-horario"


def test_buscar_faq_caso_positivo_nit() -> None:
    r = buscar_faq(
        "NIT identificacion tributaria 890324177 razon social nombre legal institucion",
    )
    assert r is not None
    assert r.id == "fvl-nit-razon-social"


def test_buscar_faq_caso_positivo_direccion() -> None:
    r = buscar_faq(
        "direccion domicilio Cali Cra 98 18-49 ubicacion sede principal Valle del Cauca",
    )
    assert r is not None
    assert r.id == "fvl-direccion-domicilio-cali"


def test_buscar_faq_caso_positivo_correo_siau() -> None:
    r = buscar_faq("correo email siau PQRS escribir contacto electronico")
    assert r is not None
    assert r.id == "fvl-correo-siau"


def test_buscar_faq_caso_positivo_sitio_web() -> None:
    r = buscar_faq("pagina web sitio internet oficial valledellili URL enlace")
    assert r is not None
    assert r.id == "fvl-sitio-web-oficial"


def test_buscar_faq_caso_positivo_urgencias_pediatricas() -> None:
    r = buscar_faq(
        "urgencias pediatricas 24 horas emergencia nino todo el dia servicio emergencias",
    )
    assert r is not None
    assert r.id == "fvl-urgencias-pediatricas-continua"


@pytest.mark.parametrize(
    ("consulta", "faq_id"),
    [
        (
            "¿Cuál es el teléfono principal de la Fundación Valle del Lili?",
            "fvl-linea-pbx-general",
        ),
        (
            "¿En qué horario atiende el SIAU (PQRS) de la Fundación Valle del Lili?",
            "fvl-siau-pqrs-horario",
        ),
        (
            "¿Cuál es el NIT y la razón social de la Fundación Valle del Lili?",
            "fvl-nit-razon-social",
        ),
        (
            "¿Dónde queda la sede principal / el domicilio principal de la Fundación Valle del Lili en Cali?",
            "fvl-direccion-domicilio-cali",
        ),
        (
            "¿Dónde consulto resultados médicos o laboratorio como paciente?",
            "fvl-portal-paciente-resultados",
        ),
    ],
)
def test_buscar_faq_pregunta_natural_cercana_canonica(
    consulta: str, faq_id: str
) -> None:
    r = buscar_faq(consulta)
    assert r is not None
    assert r.id == faq_id


def test_buscar_faq_pregunta_natural_urgencias_con_tilde() -> None:
    """Forma cercana a la pregunta canónica con tilde en pediátricas."""
    r = buscar_faq(
        "¿Las urgencias pediátricas de la Fundación Valle del Lili atienden las 24 horas?",
    )
    assert r is not None
    assert r.id == "fvl-urgencias-pediatricas-continua"


@pytest.mark.parametrize(
    ("consulta", "faq_id"),
    [
        (
            "¿El servicio de emergencias para niños funciona todo el día y toda la noche?",
            "fvl-urgencias-pediatricas-continua",
        ),
        (
            "¿Hay atención médica pediátrica de urgencia disponible las 24 horas?",
            "fvl-urgencias-pediatricas-continua",
        ),
        (
            "¿Puedo llevar a un niño a urgencias en la madrugada o cualquier día del año?",
            "fvl-urgencias-pediatricas-continua",
        ),
        (
            "¿Cómo puedo ver los resultados de mis exámenes en línea?",
            "fvl-portal-paciente-resultados",
        ),
        (
            "¿En qué plataforma descargo mis pruebas de laboratorio?",
            "fvl-portal-paciente-resultados",
        ),
        (
            "¿A qué horas está abierto el servicio de atención al usuario?",
            "fvl-siau-pqrs-horario",
        ),
        (
            "¿Cuál es la jornada de atención para poner una queja o sugerencia (PQRS)?",
            "fvl-siau-pqrs-horario",
        ),
    ],
)
def test_buscar_faq_reformulaciones_capturas(consulta: str, faq_id: str) -> None:
    """Frases reales de usuarios que antes quedaban bajo umbral o sin match."""
    r = buscar_faq(consulta)
    assert r is not None
    assert r.id == faq_id


@pytest.mark.parametrize(
    "consulta",
    [
        "Tienes un email para PQRS?",
        "cuál es el email para las pqrs?",
        "cual es el email para las pqrs?",
        "cuál es el email para el SIAU?",
        "cual es el e-mail del SIAU?",
        "¿Cuál es el correo del SIAU (PQRS) de la Fundación Valle del Lili?",
        "mail del SIAU pqrs",
    ],
)
def test_buscar_faq_consultas_cortas_correo_siau(consulta: str) -> None:
    """Variaciones breves que antes quedaban bajo umbral sin equivalencia email/correo."""
    r = buscar_faq(consulta)
    assert r is not None
    assert r.id == "fvl-correo-siau"


def test_buscar_faq_caso_positivo_portal_resultados() -> None:
    r = buscar_faq(
        "ver resultados examenes en linea pruebas laboratorio plataforma descargo",
    )
    assert r is not None
    assert r.id == "fvl-portal-paciente-resultados"


def test_buscar_faq_negativos_consulta_medica_abierta() -> None:
    negativas = [
        "¿Debo tomar antibioticos si tengo fiebre persistente y dolor abdominal intenso?",
        "diagnostico diferencial de neumonia en paciente pediatrico",
        "criterios de intubacion en shock septico segun guias internacionales",
    ]
    for consulta in negativas:
        assert buscar_faq(consulta) is None


def test_buscar_faq_determinismo() -> None:
    consulta = "telefono PBX linea 602 331 9090 central contacto llamar"
    a = buscar_faq(consulta)
    b = buscar_faq(consulta)
    assert a is not None and b is not None
    assert a.model_dump() == b.model_dump()


def test_umbral_match_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Con umbral 1.0, el score efectivo (max keywords vs canónica) debe ser < 1.0."""
    monkeypatch.setenv("FAQ_UMBRAL_MATCH", "1.0")
    obtener_configuracion.cache_clear()
    invalidar_cache_faqs()
    # Tres de cuatro palabras clave PBX (falta "contacto"); ratio 0.75 < 1.0.
    r = buscar_faq("telefono PBX linea")
    assert r is None


def test_archivo_json_ausente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAQ_JSON_RELATIVO_RAIZ", "data/structured/no_existe_faqs.json")
    obtener_configuracion.cache_clear()
    invalidar_cache_faqs()
    with pytest.raises(ArchivoFaqStructuredAusenteError) as excinfo:
        buscar_faq("cualquier cosa")
    assert "No se encontró el archivo de FAQs estructuradas" in str(excinfo.value)


def test_structured_tool_invoke() -> None:
    tool = crear_faq_tool()
    assert tool.name == "faq_estructurada"
    salida = tool.invoke(
        {"consulta": "telefono PBX linea 602 331 9090 central contacto llamar"},
    )
    assert salida["encontrado"] is True
    assert salida["id"] == "fvl-linea-pbx-general"


def test_structured_tool_sin_coincidencia() -> None:
    tool = crear_faq_tool()
    salida = tool.invoke({"consulta": "protocolo de ventilacion mecanica en ARDS"})
    assert salida["encontrado"] is False
