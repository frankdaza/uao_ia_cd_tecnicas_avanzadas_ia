"""Fragmentacion de texto para memoria semantica OpenFang."""


def fragmentar(texto: str, tam: int = 1000, solape: int = 150) -> list[str]:
    """Divide ``texto`` en ventanas de ``tam`` caracteres con ``solape``."""
    if not texto:
        return []
    if tam <= 0:
        raise ValueError("tam debe ser positivo")
    if solape < 0 or solape >= tam:
        raise ValueError("solape debe estar en [0, tam)")

    inicio = 0
    salida: list[str] = []
    while inicio < len(texto):
        fin = min(len(texto), inicio + tam)
        salida.append(texto[inicio:fin])
        if fin >= len(texto):
            break
        inicio = fin - solape
    return salida
