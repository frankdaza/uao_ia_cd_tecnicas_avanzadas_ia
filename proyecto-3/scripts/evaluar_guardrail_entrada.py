#!/usr/bin/env python3
"""Evalua guardrail de escalacion clinica ante mensaje entrante (TASK-126)."""

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
from src.guardrails.escalacion_clinica import (  # noqa: E402
    debe_escalar,
    evaluar_entrada_usuario,
    leer_kv_escalacion,
    ruta_auditoria_escalacion,
)
from src.hand.requerir_evidencia import session_id_desde_chat_id  # noqa: E402


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
        description="Evaluar palabras de alarma y opcionalmente escalar (KV + Telegram)"
    )
    parser.add_argument("--texto", required=True, help="Mensaje del paciente a evaluar")
    parser.add_argument(
        "--session-id",
        help="session_id OpenFang (ej. telegram:12345); alternativa a --chat-id",
    )
    parser.add_argument(
        "--chat-id",
        help="chat_id Telegram numerico; se convierte a session_id telegram:{id}",
    )
    parser.add_argument(
        "--solo-simular",
        action="store_true",
        help="No envia a Telegram; solo KV y auditoria si escala",
    )
    args = parser.parse_args()

    if args.session_id:
        session_id = args.session_id
        chat_id = session_id.removeprefix("telegram:") if session_id.startswith("telegram:") else None
    elif args.chat_id:
        chat_id = args.chat_id.strip()
        session_id = session_id_desde_chat_id(chat_id)
    else:
        print("ERROR: indique --session-id o --chat-id", file=sys.stderr)
        return 2

    if not chat_id:
        print("ERROR: session_id debe ser telegram:{chat_id}", file=sys.stderr)
        return 2

    print(f"debe_escalar={debe_escalar(args.texto)}")
    if not debe_escalar(args.texto):
        return 0

    cfg = obtener_configuracion()
    raiz = cfg.openfang_home_absoluto()

    if args.solo_simular:

        def enviar(_chat_id: str, _texto: str) -> None:
            return None

    else:
        token = cfg.exigir_telegram_bot_token()

        def enviar(cid: str, texto: str) -> None:
            _enviar_telegram(token, cid, texto)

    try:
        resultado = evaluar_entrada_usuario(
            session_id,
            args.texto,
            enviar=enviar,
            raiz_openfang=raiz,
        )
    except urllib.error.URLError as exc:
        print(f"ERROR envio Telegram: {exc}", file=sys.stderr)
        return 1

    kv = leer_kv_escalacion(raiz, chat_id)
    print(f"escalo={resultado.escalo} motivo={resultado.motivo!r} frase={resultado.frase_detectada!r}")
    print(f"kv escalado={kv.get('escalado')}")
    print(f"auditoria: {ruta_auditoria_escalacion(raiz)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
