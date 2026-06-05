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
import asyncio
import sys

from src.integracion.telegram.configuracion_webhook import (
    TelegramApiRespuestaError,
    TelegramWebhookConfiguracionError,
    TelegramWebhookValidacionError,
    registrar_webhook,
)


async def _ejecutar(url: str, drop_pending: bool) -> int:
    try:
        url_registrada = await registrar_webhook(
            url,
            drop_pending_updates=drop_pending,
        )
    except TelegramWebhookConfiguracionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except TelegramWebhookValidacionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except TelegramApiRespuestaError as exc:
        print(f"Telegram respondio error: {exc.datos}", file=sys.stderr)
        return 1

    print(f"Webhook registrado: {url_registrada}")
    return 0


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
    return asyncio.run(_ejecutar(args.url, args.drop_pending))


if __name__ == "__main__":
    raise SystemExit(main())
