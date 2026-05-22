#!/usr/bin/env python3
"""
Registra el webhook de Telegram (setWebhook) hacia la API TAAM.

Uso:
    export TELEGRAM_BOT_TOKEN='...'
    export TELEGRAM_WEBHOOK_SECRET='...'
    uv run python -m scripts.configurar_webhook_telegram \\
        --url https://tu-dominio.example/api/integracion/telegram/webhook

Requiere URL publica HTTPS (ngrok, Cloudflare Tunnel, etc.). Telegram no acepta
localhost ni HTTP plano en produccion.
"""

from __future__ import annotations

import argparse
import sys

import httpx

from src.configuracion import obtener_configuracion


def main() -> int:
    parser = argparse.ArgumentParser(description="setWebhook para bot TAAM")
    parser.add_argument(
        "--url",
        required=True,
        help="URL publica del webhook (debe incluir /api/integracion/telegram/webhook)",
    )
    parser.add_argument(
        "--drop-pending",
        action="store_true",
        help="Pasa drop_pending_updates=true a Telegram",
    )
    args = parser.parse_args()

    cfg = obtener_configuracion()
    token = (cfg.telegram_bot_token or "").strip()
    secret = (cfg.telegram_webhook_secret or "").strip()
    if not token:
        print("Error: defina TELEGRAM_BOT_TOKEN en .env", file=sys.stderr)
        return 1
    if not secret:
        print("Error: defina TELEGRAM_WEBHOOK_SECRET en .env", file=sys.stderr)
        return 1

    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    payload: dict[str, str | bool] = {
        "url": args.url.strip(),
        "secret_token": secret,
    }
    if args.drop_pending:
        payload["drop_pending_updates"] = True

    with httpx.Client(timeout=30.0) as cliente:
        resp = cliente.post(api_url, json=payload)
        resp.raise_for_status()
        datos = resp.json()

    if not datos.get("ok"):
        print(f"Telegram respondio error: {datos}", file=sys.stderr)
        return 1

    print(f"Webhook registrado: {args.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
