"""Comprobaciones mínimas del entorno hasta que exista la suite real."""


def test_import_paquete_src() -> None:
    import src  # noqa: F401
