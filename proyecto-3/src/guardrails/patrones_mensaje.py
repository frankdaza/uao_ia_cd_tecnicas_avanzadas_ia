"""Patrones regex compartidos para validar mensajes clinicos (sin dependencias Hand)."""

from __future__ import annotations

import re

PATRON_DOSIS = re.compile(
    r"\d+\s*(?:mg|ml|mcg|gota[s]?|tableta[s]?)\b",
    re.IGNORECASE,
)
PATRON_FARMACO_CON_DOSIS = re.compile(
    r"\b(?:ibuprofeno|acetaminofen|paracetamol|naproxeno|tramadol)\b.*\d+",
    re.IGNORECASE,
)
