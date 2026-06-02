"""
Shim de compatibilidad: importar desde ``protocolo_ingesta``.

El modulo historico se mantiene para scripts y tests que aun referencian ``protocolo_pdf``.
"""

from src.ingesta.extractores.pdf import extraer_documentos_desde_pdf
from src.ingesta.protocolo_ingesta import (
    ResultadoIngesta,
    debe_omitir_ingesta,
    dividir_en_chunks,
    ejecutar_ingesta_en_sesion_nueva,
    eliminar_vectores_procedimiento,
    ingestar_chunks_en_qdrant,
    ingestar_pendientes,
    ingestar_tipo_procedimiento,
)

__all__ = [
    "ResultadoIngesta",
    "debe_omitir_ingesta",
    "dividir_en_chunks",
    "ejecutar_ingesta_en_sesion_nueva",
    "eliminar_vectores_procedimiento",
    "extraer_documentos_desde_pdf",
    "ingestar_chunks_en_qdrant",
    "ingestar_pendientes",
    "ingestar_tipo_procedimiento",
]
