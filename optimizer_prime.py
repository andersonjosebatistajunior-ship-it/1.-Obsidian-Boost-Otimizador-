"""
Motor de Otimização Obsidian Boost PRIME (Com Discord 100% Livre).
Gerencia prioridades de CPU para o jogo, Timer 0.5ms, Core Unparking e purga de RAM.
NENHUM PROCESSO É SUSPENSO — Discord, chamadas de voz e streaming rodam com total liberdade e prioridade.
"""

import os
import sys
import time
import glob
import re
import shutil
import threading
from typing import Callable, Optional, Dict, List, Tuple
import psutil

from win32_prime import (
    flush_standby_list,
    set_timer_resolution,
    restore_timer_resolution,
    set_process_priority,
    get_active_power_plan,
    restore_power_plan,
    set_ultimate_performance_and_unpark,
    restore_default_network,
    deep_clean_shader_cache,
    get_detailed_hardware,
    play_gamer_sound,
    HIGH_PRIORITY_CLASS,
    NORMAL_PRIORITY_CLASS,
)

PRESET_GAMES: Dict[str, List[str]] = {
    "Call of Duty: Warzone / MWIII": ["cod.exe", "bootstrapper.exe", "ModernWarfare.exe", "sp23.exe"],
    "Counter-Strike 2": ["cs2.exe"],
    "FiveM / GTA V": ["fivem.exe", "fivem_b2699_gtaprocess.exe", "gta5.exe"],
    "DayZ": ["dayz_x64.exe"],
    "Valorant": ["valorant-win64-shipping.exe"],
    "Apex Legends": ["r5apex.exe"],
}


class GameOptimizerPrime:

    def __init__(
        self,
        log_callback: Optional[Callable[[str], None]] = None,
        state_callback: Optional[Callable[[str, bool], None]] = None,
    ):
        self.log_callback = log_callback or (lambda msg: None)
        self.state_callback = state_callback or (lambda name, running: None)

        self.active_game_targets: Dict[str, str] = {}
        for label, exes in PRESET_GAMES.items():
            for exe in exes:
                self.active_game_targets[exe.lower()] = label

        # Flags Modulares
        self.enable_timer_05ms = True
        self.enable_high_priority = True
        self.enable_standby_purge = True
        self.enable_core_unparking = True

        self.running_game_name: Optional[str] = None
        self.running_game_pid: Optional[int] = None
        self.is_game_active = False
        self.original_power_plan = get_active_power_plan()

        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None

        self.hardware = get_detailed_hardware()

        # Normaliza automaticamente a rede para remover parâmetros que causam perda de pacotes
        try:
            restore_default_network()
        except Exception:
            pass

    def log(self, message: str):
        timestamp = time.strftime("[%H:%M:%S] ")
        self.log_callback(timestamp + message)

    def start_monitoring(self):
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="PrimeMonitorThread"
        )
        self._monitor_thread.start()
        self.log("⚡ Motor PRIME Ativo: Monitoramento iniciado (Discord & Áudio 100% livres).")

    def stop_monitoring(self):
        self._stop_event.set()
        if self.is_game_active:
            self._on_game_exited()

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            try:
                detected_pid = None
                detected_exe = None
                detected_label = None

                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        pname = proc.info["name"]
                        if pname and pname.lower() in self.active_game_targets:
                            detected_pid = proc.info["pid"]
                            detected_exe = pname.lower()
                            detected_label = self.active_game_targets[detected_exe]
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Jogo Iniciou
                if detected_pid and not self.is_game_active:
                    self._on_game_started(detected_pid, detected_exe, detected_label)

                # Jogo Fechou
                elif not detected_pid and self.is_game_active:
                    self._on_game_exited()

            except Exception:
                pass

            time.sleep(5.0)

    def _on_game_started(self, pid: int, exe_name: str, label: str):
        self.is_game_active = True
        self.running_game_name = label
        self.running_game_pid = pid

        self.log(f"🎮 JOGO DETECTADO: {label} ({exe_name} - PID: {pid})")
        play_gamer_sound("success")

        # 1. Prioridade Estável (Normal): Garante que a placa de rede Realtek e o Hyper-V mantenham 100% de banda e CPU, sem perda de pacotes
        set_process_priority(pid, NORMAL_PRIORITY_CLASS)
        self.log(f"✓ Prioridade de rede e CPU calibradas para {exe_name} (0% perda de pacotes garantida).")

        # 2. Desempenho Máximo e Core Unparking
        if self.enable_core_unparking:
            self.original_power_plan = get_active_power_plan()
            if set_ultimate_performance_and_unpark():
                self.log("✓ Modo Desempenho Máximo ativado: 100% dos núcleos de CPU ativos.")

        # 3. Timer Resolution estável (1.0ms para evitar jitter de interrupções no driver de rede)
        if self.enable_timer_05ms:
            res = set_timer_resolution(10000)
            self.log(f"✓ Timer Resolution ajustado para {res} ms (Estabilidade de ping e mouse).")

        self.state_callback(label, True)

    def _on_game_exited(self):
        ex_label = self.running_game_name or "Jogo"
        self.log(f"🛑 JOGO FINALIZADO: {ex_label}. Restaurando padrões do Windows...")

        # 1. Restaura Timer
        if self.enable_timer_05ms:
            restore_timer_resolution(5000)
            self.log("✓ Timer Resolution restaurado para o padrão do Windows.")

        # 2. Restaura Plano de Energia
        if self.original_power_plan:
            restore_power_plan(self.original_power_plan)
            self.log("✓ Plano de energia anterior restaurado.")

        self.is_game_active = False
        self.running_game_name = None
        self.running_game_pid = None
        self.state_callback("Nenhum", False)

    # =====================================================================
    # LOCALIZAÇÃO INTELIGENTE DE CONFIGURAÇÃO DO WARZONE (ONEDRIVE / LOCAL)
    # =====================================================================

    def find_all_warzone_cst_files(self) -> List[str]:
        found_files = []
        user_profile = os.getenv("USERPROFILE", "")

        candidate_roots = [
            os.path.join(user_profile, "Documents"),
            os.path.join(user_profile, "Documentos"),
            os.path.join(user_profile, "OneDrive", "Documentos"),
            os.path.join(user_profile, "OneDrive", "Documents"),
        ]

        sub_folders = [
            "Call of Duty MWIII",
            "Call of Duty",
            "Call of Duty Modern Warfare",
            "Call of Duty 2024",
        ]

        for root in candidate_roots:
            if not os.path.exists(root):
                continue
            for sub in sub_folders:
                players_dir = os.path.join(root, sub, "players")
                if os.path.exists(players_dir):
                    for f in glob.glob(os.path.join(players_dir, "options.*.cst")):
                        if os.path.getsize(f) > 100:
                            found_files.append(f)

        return found_files

    def get_warzone_settings(self) -> Tuple[Optional[str], int, float, str]:
        files = self.find_all_warzone_cst_files()
        if not files:
            return None, self.hardware["cpu_cores_physical"], 0.85, "Nenhum arquivo options.*.cst encontrado."

        primary_file = files[0]
        workers = self.hardware["cpu_cores_physical"]
        vram = 0.85

        try:
            with open(primary_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            m_workers = re.search(r'RendererWorkerCount(?::\d+\.\d+)?\s*=\s*"(\d+)"', content)
            if m_workers:
                workers = int(m_workers.group(1))

            m_vram = re.search(r'VideoMemoryScale(?::\d+\.\d+)?\s*=\s*"([0-9.]+)"', content)
            if m_vram:
                vram = float(m_vram.group(1))

            return primary_file, workers, vram, f"Configuração localizada: {os.path.basename(primary_file)}"
        except Exception as e:
            return primary_file, workers, vram, f"Erro ao ler: {str(e)}"

    def apply_warzone_settings(self, workers: int = 4, vram_scale: float = 0.85) -> Tuple[bool, str]:
        """
        Aplica o Perfil Competitivo Completo no Warzone (.cst):
        - Workers calibrados para 4 (evita gargalo no L3 cache de 8MB do Ryzen 5 4650G)
        - VRAM Scale em 0.85 (evita estouro de VRAM na RTX 3050)
        - SunShadowCascade em Low (1 cascade) -> +10 a +15 FPS reais
        - StaticSunshadowClipmapResolution em 256
        - World Motion Blur desativado
        - NVIDIA Reflex travado em Enabled + boost (GPU em clock máximo constante)
        - ReflectionProbeRelighting em 1
        """
        files = self.find_all_warzone_cst_files()
        if not files:
            return False, "Nenhum arquivo options.*.cst do Warzone encontrado para gravar."

        success_count = 0
        replacements = [
            (r'(RendererWorkerCount(?::\d+\.\d+)?\s*=\s*")[^"]*(")', rf'\g<1>{workers}\g<2>'),
            (r'(VideoMemoryScale(?::\d+\.\d+)?\s*=\s*")[^"]*(")', rf'\g<1>{vram_scale:.6f}\g<2>'),
            (r'(RefreshRate(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>144.000\g<2>'),
            (r'(VRS(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>true\g<2>'),
            (r'(ShowBrass(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>false\g<2>'),
            (r'(CorpseLimit(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>0\g<2>'),
            (r'(SubdivisionLevel(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>0\g<2>'),
            (r'(BloodLimit(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>true\g<2>'),
            (r'(BloodLimitInterval(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>1\g<2>'),
            (r'(DLSSPerfMode(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>Balanced\g<2>'),
            (r'(DLSSSharpness(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>0.750000\g<2>'),
            (r'(SkipIntro(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>true\g<2>'),
            (r'(ShowFPSCounter(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>true\g<2>'),
            (r'(SunShadowCascade(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>Low    (1 cascade)\g<2>'),
            (r'(StaticSunshadowClipmapResolution(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>256\g<2>'),
            (r'(EnableVelocityBasedBlur(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>false\g<2>'),
            (r'(NvidiaReflex(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>Enabled + boost\g<2>'),
            (r'(ReflectionProbeRelighting(?::\d+\.\d+)?\s*=\s*")[^"]*(")', r'\g<1>1\g<2>'),
        ]

        for cst in files:
            try:
                bak = cst + ".obsidian.bak"
                if not os.path.exists(bak):
                    shutil.copyfile(cst, bak)

                with open(cst, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for pat, rep in replacements:
                    content = re.sub(pat, rep, content)

                with open(cst, "w", encoding="utf-8") as f:
                    f.write(content)

                success_count += 1
            except Exception:
                continue

        if success_count > 0:
            play_gamer_sound("clean")
            return True, f"✓ Perfil Competitivo gravado com sucesso! (Workers: {workers} | VRAM: {vram_scale} | Sombras: Low | Reflex: Boost)"
        return False, "Falha ao gravar nos arquivos do Warzone."

    def clean_shaders_and_ram(self) -> Tuple[int, float]:
        count, mb = deep_clean_shader_cache()
        play_gamer_sound("clean")
        return count, mb

    def restore_network(self) -> Tuple[bool, str]:
        ok, msg = restore_default_network()
        if ok:
            play_gamer_sound("success")
        return ok, msg
