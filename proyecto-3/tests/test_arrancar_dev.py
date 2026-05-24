"""Pruebas del script arrancar_dev.sh (negativo y contrato estatico)."""

from __future__ import annotations

import subprocess
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[1]
_SCRIPT = _RAIZ / "scripts" / "arrancar_dev.sh"


def test_falta_env_exit_1(tmp_path: Path) -> None:
    # Copia el script bajo tmp/ para que ROOT_DIR sea tmp (sin .env del repo).
    scripts_tmp = tmp_path / "scripts"
    scripts_tmp.mkdir()
    script_tmp = scripts_tmp / "arrancar_dev.sh"
    script_tmp.write_text(_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    script_tmp.chmod(0o755)

    resultado = subprocess.run(
        ["bash", str(script_tmp)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 1
    salida = (resultado.stderr + resultado.stdout).lower()
    assert "falta .env" in salida


def test_ayuda_menciona_sin_telegram() -> None:
    resultado = subprocess.run(
        ["bash", str(_SCRIPT), "--help"],
        cwd=_RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0
    assert "--sin-telegram" in resultado.stdout


def test_script_contiene_contrato_e2e() -> None:
    texto = _SCRIPT.read_text(encoding="utf-8")
    assert "trap limpiar INT TERM" in texto
    assert "--sin-telegram" in texto
    assert "/api/health" in texto
    assert "permitir-db-en-vivo" in texto
    assert "hand activate taam_lili_hand" in texto
    assert "verificar_telegram_bot.sh" in texto
    assert "INICIAMOS_DAEMON" in texto


def test_opcion_desconocida_exit_1() -> None:
    resultado = subprocess.run(
        ["bash", str(_SCRIPT), "--foo"],
        cwd=_RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 1
    assert "desconocida" in (resultado.stderr + resultado.stdout).lower()
