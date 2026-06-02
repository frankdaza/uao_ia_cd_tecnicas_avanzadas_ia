"""Validacion estatica del prompt Bot Lili (system.md y agent.toml)."""

from __future__ import annotations

from pathlib import Path

DISCLAIMER_MINIMO = "no reemplaza"
FRASES_OBLIGATORIAS = (
    "memory_recall",
    "SOLO",
    "no inventes",
    "Segun el material institucional",
    DISCLAIMER_MINIMO,
    "medico tratante",
    "No diagnostiques",
)
FRASES_PROHIBIDAS_INSTRUCCION = ()  # reservado para regresiones futuras

_MARCADOR_INICIO = 'system_prompt = """'
_MARCADOR_FIN = '"""'


def normalizar_prompt(texto: str) -> str:
    """Colapsa espacios para comparar system.md con agent.toml."""
    lineas = [ln.strip() for ln in texto.strip().splitlines()]
    return "\n".join(ln for ln in lineas if ln)


def validar_prompt_sistema(texto: str) -> list[str]:
    """Devuelve lista de faltantes; vacia si el prompt cumple reglas minimas."""
    faltantes: list[str] = []
    bajo = texto.lower()
    for frase in FRASES_OBLIGATORIAS:
        if frase.lower() not in bajo:
            faltantes.append(frase)
    if "vector store" not in bajo and "contexto recuperado" not in bajo:
        faltantes.append("contexto recuperado / Vector Store")
    return faltantes


def extraer_system_prompt_de_agent_toml(contenido: str) -> str:
    """Extrae el cuerpo de system_prompt de un agent.toml."""
    inicio = contenido.find(_MARCADOR_INICIO)
    if inicio < 0:
        msg = "No se encontro system_prompt en agent.toml"
        raise ValueError(msg)
    inicio += len(_MARCADOR_INICIO)
    fin = contenido.find(_MARCADOR_FIN, inicio)
    if fin < 0:
        msg = "system_prompt sin cierre triple comilla"
        raise ValueError(msg)
    return contenido[inicio:fin]


def reemplazar_system_prompt_en_agent_toml(contenido: str, nuevo_prompt: str) -> str:
    """Sustituye solo el bloque system_prompt, preservando el resto del TOML."""
    inicio = contenido.find(_MARCADOR_INICIO)
    if inicio < 0:
        msg = "No se encontro system_prompt en agent.toml"
        raise ValueError(msg)
    fin_bloque = contenido.find(_MARCADOR_FIN, inicio + len(_MARCADOR_INICIO))
    if fin_bloque < 0:
        msg = "system_prompt sin cierre triple comilla"
        raise ValueError(msg)
    fin_bloque += len(_MARCADOR_FIN)
    cuerpo = nuevo_prompt.replace('"""', '\\"""')
    return contenido[:inicio] + _MARCADOR_INICIO + cuerpo + _MARCADOR_FIN + contenido[fin_bloque:]


def rutas_prompt_proyecto(raiz: Path | None = None) -> tuple[Path, Path]:
    """Rutas canonicas system.md y agent.toml bajo proyecto-3."""
    base = raiz or Path(__file__).resolve().parents[2]
    system_md = base / "openfang" / "hands" / "taam_lili_hand" / "prompts" / "system.md"
    agent_toml = base / "openfang" / "agents" / "bot_lili_taam" / "agent.toml"
    return system_md, agent_toml


def leer_prompt_desde_system_md(ruta: Path) -> str:
    texto = ruta.read_text(encoding="utf-8")
    # Quitar titulo documental opcional "# System — ..."
    lineas = texto.splitlines()
    if lineas and lineas[0].startswith("# "):
        lineas = lineas[1:]
        while lineas and not lineas[0].strip():
            lineas = lineas[1:]
    return "\n".join(lineas).strip() + "\n"


def sincronizar_agent_toml_desde_system_md(
    raiz: Path | None = None,
    *,
    escribir: bool = True,
) -> tuple[str, Path]:
    """Lee system.md y opcionalmente actualiza agent.toml. Devuelve prompt y ruta agent."""
    system_md, agent_toml = rutas_prompt_proyecto(raiz)
    if not system_md.is_file():
        msg = f"Falta {system_md}"
        raise FileNotFoundError(msg)
    prompt = leer_prompt_desde_system_md(system_md)
    if escribir:
        contenido = agent_toml.read_text(encoding="utf-8")
        nuevo = reemplazar_system_prompt_en_agent_toml(contenido, prompt)
        agent_toml.write_text(nuevo, encoding="utf-8")
    return prompt, agent_toml
