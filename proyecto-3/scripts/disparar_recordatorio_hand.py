#!/usr/bin/env python3
"""Disparo manual del recordatorio postoperatorio UC6 (adaptador TASK-124)."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.configuracion import obtener_configuracion  # noqa: E402
from src.hand.recordatorio_postoperatorio import (  # noqa: E402
    ejecutar_recordatorio_postop,
    ruta_auditoria_hand,
)


def _enviar_telegram(token: str, chat_id: str, texto: str) -> None:
    cuerpo = urllib.parse.urlencode({"chat_id": chat_id, "text": texto}).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    solicitud = urllib.request.Request(url, data=cuerpo, method="POST")
    with urllib.request.urlopen(solicitud, timeout=30) as respuesta:
        datos = json.loads(respuesta.read().decode("utf-8"))
    if not datos.get("ok"):
        raise RuntimeError(f"Telegram sendMessage fallo: {datos}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Disparar recordatorio postoperatorio (Hand taam_lili_hand / UC6)"
    )
    parser.add_argument(
        "--solo-simular",
        action="store_true",
        help="No llama a Telegram; solo lista sesiones y escribe auditoria",
    )
    args = parser.parse_args()

    cfg = obtener_configuracion()
    raiz = cfg.openfang_home_absoluto()

    if args.solo_simular:

        def enviar(_chat_id: str, _texto: str) -> None:
            return None

    else:
        token = cfg.exigir_telegram_bot_token()

        def enviar(chat_id: str, texto: str) -> None:
            _enviar_telegram(token, chat_id, texto)

    try:
        resultado = ejecutar_recordatorio_postop(
            enviar=enviar,
            raiz_openfang=raiz,
            registrar_auditoria=True,
        )
    except urllib.error.URLError as exc:
        print(f"ERROR envio Telegram: {exc}", file=sys.stderr)
        return 1

    audit = ruta_auditoria_hand(raiz)
    print(f"enviados={resultado.enviados} motivo={resultado.motivo!r}")
    for detalle in resultado.detalles:
        print(f"  {detalle}")
    print(f"auditoria: {audit}")
    return 0 if resultado.enviados > 0 or resultado.motivo == "sin_sesiones_activas" else 2


if __name__ == "__main__":
    raise SystemExit(main())
