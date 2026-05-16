"""Shim de compatibilidad para el antiguo nombre ``src.qa``.

El código vive en ``src.laboratorio.qa_legacy``. Este módulo reexporta los
símbolos públicos mínimos y emite ``DeprecationWarning`` al importar.

**Retiro previsto del shim:** 2026-08-01 (importar desde
``src.laboratorio.qa_legacy`` antes de esa fecha).
"""

from __future__ import annotations

import warnings

warnings.warn(
    "El paquete src.qa esta deprecado; use src.laboratorio.qa_legacy. "
    "Este shim se retira el 2026-08-01 (ver README, seccion laboratorio).",
    DeprecationWarning,
    stacklevel=2,
)

from src.laboratorio.qa_legacy import (  # noqa: E402
    ClienteOllama,
    ConfiguracionLlm,
    DocumentoContexto,
    ModeloNoDisponibleError,
    MODELOS_OLLAMA_SOPORTADOS,
    MODELO_GEMMA_4_E2B,
    MODELO_GEMMA_4_E4B,
    MODELO_LLAMA_3_1_8B,
    OllamaNoAccesibleError,
)

__all__ = [
    "ClienteOllama",
    "ConfiguracionLlm",
    "DocumentoContexto",
    "ModeloNoDisponibleError",
    "MODELOS_OLLAMA_SOPORTADOS",
    "MODELO_GEMMA_4_E2B",
    "MODELO_GEMMA_4_E4B",
    "MODELO_LLAMA_3_1_8B",
    "OllamaNoAccesibleError",
]
