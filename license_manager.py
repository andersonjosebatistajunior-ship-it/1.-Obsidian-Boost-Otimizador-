"""
Gerenciador de Licenças, HWID e Proteção Anti-Pirataria do Obsidian Boost.
Vincula chaves ao hardware exclusivo do computador (placa-mãe + processador).
"""

import os
import sys
import json
import base64
import hashlib
from datetime import datetime, timedelta
import winreg
import subprocess

XOR_KEY = 0x5A
LICENSE_DIR = os.path.join(os.getenv("APPDATA", ""), "ObsidianBoost")
LICENSE_PATH = os.path.join(LICENSE_DIR, "licenca.dat")


def _xor_cipher(data: bytes, key: int) -> bytes:
    return bytes([b ^ key for b in data])


def get_hwid() -> str:
    """Gera o identificador único e imutável (HWID) da máquina."""
    cpu_id = ""
    bios_id = ""
    guid = ""

    try:
        # MachineGuid do Windows
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography"
        ) as key:
            guid = winreg.QueryValueEx(key, "MachineGuid")[0]
    except Exception:
        guid = os.getenv("COMPUTERNAME", "UNKNOWN_PC")

    try:
        # Serial da BIOS / Placa-Mãe via wmic
        out = subprocess.check_output(
            ["wmic", "bios", "get", "serialnumber"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        lines = [l.strip() for l in out.strip().split("\n") if l.strip()]
        if len(lines) > 1:
            bios_id = lines[1]
    except Exception:
        bios_id = "BIOS_GENERIC"

    try:
        # ID do processador
        out = subprocess.check_output(
            ["wmic", "cpu", "get", "processorid"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        lines = [l.strip() for l in out.strip().split("\n") if l.strip()]
        if len(lines) > 1:
            cpu_id = lines[1]
    except Exception:
        cpu_id = "CPU_GENERIC"

    raw = f"{cpu_id}_{bios_id}_{guid}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16].upper()


def verify_license() -> tuple[bool, str, int, str]:
    """
    Verifica se a máquina possui uma licença válida ativa.
    Retorna: (is_valid, license_type, days_remaining, hwid)
    """
    hwid = get_hwid()

    if not os.path.exists(LICENSE_PATH):
        return False, "Sem Licença", 0, hwid

    try:
        with open(LICENSE_PATH, "r", encoding="utf-8") as f:
            b64_data = f.read().strip()

        decrypted = _xor_cipher(base64.b64decode(b64_data), XOR_KEY).decode("utf-8")
        data = json.loads(decrypted)

        # Checa se o HWID confere com esta máquina
        if data.get("hwid") != hwid:
            return False, "HWID Incompatível", 0, hwid

        key = data.get("chave", "").upper()
        tipo = data.get("tipo", "Vitalícia")

        # Vitalícia
        if (
            tipo == "Vitalícia"
            or "LIFE" in key
            or key.startswith("OBS-BOOST-LIFE-")
            or key.startswith("OBS-LIFE-")
        ):
            return True, "Vitalícia PRO", 9999, hwid

        # Mensal (30 Dias)
        exp_str = data.get("data_expiracao")
        if exp_str:
            exp_date = datetime.fromisoformat(exp_str)
            remaining = exp_date - datetime.now()
            if remaining.total_seconds() > 0:
                days = max(1, int(remaining.days) + 1)
                return True, f"Mensal ({days}d restantes)", days, hwid
            else:
                return False, "Licença Expirada", 0, hwid

    except Exception:
        pass

    return False, "Inválida", 0, hwid


def activate_key(key_input: str) -> tuple[bool, str]:
    """
    Valida e grava a chave digitada pelo cliente, vinculando ao HWID desta máquina.
    """
    key = key_input.strip().upper()
    if not key:
        return False, "Por favor, digite uma chave de licença válida."

    is_life = key.startswith("OBS-BOOST-LIFE-") or key.startswith("OBS-LIFE-")
    is_m30 = key.startswith("OBS-BOOST-M30-") or key.startswith("OBS-M30-")

    if not is_life and not is_m30:
        return False, "Formato de chave inválido! Chaves começam com OBS-BOOST-LIFE- ou OBS-BOOST-M30-."

    parts = key.split("-")
    if len(parts) < 4:
        return False, "Chave com tamanho incorreto. Verifique os dígitos."

    hwid = get_hwid()
    now = datetime.now()
    exp = (now + timedelta(days=30)) if is_m30 else None

    payload = {
        "chave": key,
        "tipo": "Vitalícia" if is_life else "Mensal (30 Dias)",
        "hwid": hwid,
        "data_ativacao": now.isoformat(),
        "data_expiracao": exp.isoformat() if exp else None,
    }

    try:
        os.makedirs(LICENSE_DIR, exist_ok=True)
        raw_json = json.dumps(payload).encode("utf-8")
        encrypted = _xor_cipher(raw_json, XOR_KEY)
        b64_str = base64.b64encode(encrypted).decode("utf-8")

        with open(LICENSE_PATH, "w", encoding="utf-8") as f:
            f.write(b64_str)

        msg = (
            "Licença VITALÍCIA ativada com sucesso! Acesso permanente liberado."
            if is_life
            else "Licença MENSAL (30 Dias) ativada com sucesso! Aproveite."
        )
        return True, msg
    except Exception as e:
        return False, f"Erro ao gravar licença: {str(e)}"
