"""Tests del mensaje de confirmacion al emparejar Telegram."""

from src.api.servicios.emparejamiento import _mensaje_confirmacion_emparejamiento


def test_mensaje_confirmacion_incluye_datos_del_caso() -> None:
    mensaje = _mensaje_confirmacion_emparejamiento(
        nombre_paciente="Maria Lopez",
        nombre_procedimiento="Colecistectomia laparoscopica",
        cirujano_nombre="Dr. Juan Perez",
    )
    assert "Maria Lopez" in mensaje
    assert "Lili" in mensaje
    assert "Fundación Valle del Lili" in mensaje
    assert "Colecistectomia laparoscopica" in mensaje
    assert "Dr. Juan Perez" in mensaje
    assert "vinculado correctamente" in mensaje.lower()
    assert "Escríbeme cuando" in mensaje


def test_mensaje_confirmacion_usa_fallbacks() -> None:
    mensaje = _mensaje_confirmacion_emparejamiento(
        nombre_paciente="paciente",
        nombre_procedimiento="tu procedimiento",
        cirujano_nombre="tu equipo tratante",
    )
    assert "paciente" in mensaje
    assert "tu procedimiento" in mensaje
    assert "tu equipo tratante" in mensaje
