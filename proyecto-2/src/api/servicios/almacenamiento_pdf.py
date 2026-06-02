"""Shim de compatibilidad hacia ``almacenamiento_protocolo`` (PDF + Markdown)."""

from src.api.servicios.almacenamiento_protocolo import (  # noqa: F401
    ArchivoProtocoloInvalidoError,
    ArchivoProtocoloInvalidoError as PdfProtocoloInvalidoError,
    guardar_pdf_en_disco,
    guardar_protocolo_en_disco,
    hash_sha256,
    http_422_desde_error_pdf,
    http_422_desde_error_protocolo,
    leer_y_validar_archivo_protocolo,
    leer_y_validar_pdf,
    ruta_absoluta_por_formato,
    ruta_absoluta_protocolo,
    ruta_relativa_protocolo,
)
