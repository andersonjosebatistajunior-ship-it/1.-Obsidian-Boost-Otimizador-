"""
Ponto de Entrada do Obsidian Boost PRIME.
Gerencia privilégios UAC de Administrador, Mutex de instância única,
captura de exceções e ícone na bandeja do sistema (pystray).
DISCORD E APLICATIVOS DE VOZ FUNCIONAM 100% LIVRES.
"""

import os
import sys
import time
import traceback
import threading
import ctypes
from typing import Optional
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item, Menu

from win32_prime import (
    get_resource_path,
    flush_standby_list,
    enable_privilege,
    play_gamer_sound,
)
from optimizer_prime import GameOptimizerPrime
from ui_prime import ObsidianBoostPrimeUI
import license_manager

APPDATA_DIR = os.path.join(os.getenv("APPDATA", ""), "ObsidianBoost")
os.makedirs(APPDATA_DIR, exist_ok=True)
LOCAL_CRASH_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_crash.log")
APPDATA_CRASH_LOG = os.path.join(APPDATA_DIR, "prime_crash.log")

MUTEX_NAME = "Global\\ObsidianBoost_Prime_SingleInstance_Mutex"
ERROR_ALREADY_EXISTS = 183


def setup_global_exception_handler():
    def excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        log_entry = f"\n{'='*60}\n{timestamp} CRASH REPORT - OBSIDIAN BOOST PRIME\n{'='*60}\n{err_msg}\n"

        for log_path in [LOCAL_CRASH_LOG, APPDATA_CRASH_LOG]:
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(log_entry)
            except Exception:
                pass

        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Ocorreu um erro no Obsidian Boost PRIME.\n\nDetalhes gravados em:\n{APPDATA_CRASH_LOG}\n\nErro: {exc_value}",
                "Obsidian Boost PRIME — Erro",
                0x10
            )
        except Exception:
            pass

    sys.excepthook = excepthook

    if hasattr(threading, "excepthook"):
        threading.excepthook = lambda args: excepthook(args.exc_type, args.exc_value, args.exc_traceback)


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate_to_admin():
    if is_admin():
        return True

    try:
        if getattr(sys, "frozen", False):
            executable = sys.executable
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        else:
            executable = sys.executable
            script = os.path.abspath(__file__)
            params = f'"{script}" ' + " ".join([f'"{arg}"' for arg in sys.argv[1:]])

        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        if ret > 32:
            sys.exit(0)
        return False
    except Exception:
        return False


def set_high_dpi_awareness():
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def load_tray_icon_image() -> Image.Image:
    ico_path = get_resource_path("app.ico")
    if os.path.exists(ico_path):
        try:
            return Image.open(ico_path)
        except Exception:
            pass
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([2, 2, 62, 62], radius=12, fill=(20, 21, 30), outline=(220, 38, 38), width=3)
    points = [(36, 6), (16, 34), (32, 34), (26, 58), (48, 28), (34, 28)]
    draw.polygon(points, fill=(239, 68, 68))
    return img


class ObsidianBoostPrimeApp:

    def __init__(self):
        self.engine: Optional[GameOptimizerPrime] = None
        self.ui: Optional[ObsidianBoostPrimeUI] = None
        self.tray_icon: Optional[pystray.Icon] = None
        self.mutex_handle = None

    def acquire_single_instance(self) -> bool:
        kernel32 = ctypes.windll.kernel32
        self.mutex_handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        last_error = kernel32.GetLastError()
        if last_error == ERROR_ALREADY_EXISTS:
            try:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "O Obsidian Boost PRIME já está em execução na bandeja do sistema.",
                    "Obsidian Boost PRIME",
                    0x40
                )
            except Exception:
                pass
            return False
        return True

    def run(self):
        setup_global_exception_handler()

        if not is_admin():
            if "--no-uac" not in sys.argv:
                elevate_to_admin()
                return

        enable_privilege("SeProfileSingleProcessPrivilege")
        enable_privilege("SeIncreaseQuotaPrivilege")

        # Normaliza a rede com privilégios de Administrador para zerar perda de pacotes e estabilizar o ping
        try:
            from win32_prime import restore_default_network
            restore_default_network()
        except Exception:
            pass

        if not self.acquire_single_instance():
            return

        set_high_dpi_awareness()

        self.engine = GameOptimizerPrime()
        self.ui = ObsidianBoostPrimeUI(engine=self.engine, on_minimize_tray=self.on_minimized_to_tray)

        self.setup_system_tray()

        try:
            self.ui.mainloop()
        finally:
            self.shutdown()

    def setup_system_tray(self):
        tray_image = load_tray_icon_image()

        def action_show(icon, item):
            if self.ui:
                self.ui.after(0, self.ui.restore_from_tray)

        def action_flush_ram(icon, item):
            def task():
                flush_standby_list()
                play_gamer_sound("clean")
                if self.ui:
                    self.ui.after(0, lambda: self.ui.log_message("✓ Standby List liberada via Bandeja!"))
            threading.Thread(target=task, daemon=True).start()

        def action_clean_shaders(icon, item):
            def task():
                if self.engine:
                    c, mb = self.engine.clean_shaders_and_ram()
                    if self.ui:
                        self.ui.after(0, lambda: self.ui.log_message(f"✓ Shaders limpos via Bandeja ({c} arqs / {mb} MB)!"))
            threading.Thread(target=task, daemon=True).start()

        def action_optimize_net(icon, item):
            def task():
                if self.engine:
                    ok, msg = self.engine.optimize_network()
                    if self.ui:
                        self.ui.after(0, lambda: self.ui.log_message(f"✓ {msg}"))
            threading.Thread(target=task, daemon=True).start()

        def action_exit(icon, item):
            self.shutdown()

        menu = Menu(
            item("⚡ Obsidian Boost PRIME", None, enabled=False),
            Menu.SEPARATOR,
            item("🖥️ Abrir Interface", action_show, default=True),
            item("🧹 Limpar Shaders & RAM", action_clean_shaders),
            item("🌐 Otimizar Rede (TCP/IP)", action_optimize_net),
            item("⚡ Purgar Standby List", action_flush_ram),
            Menu.SEPARATOR,
            item("❌ Sair do Obsidian Boost PRIME", action_exit),
        )

        self.tray_icon = pystray.Icon(
            name="ObsidianBoostPrime",
            icon=tray_image,
            title="Obsidian Boost PRIME — Gamer Engine",
            menu=menu
        )

        try:
            self.tray_icon.run_detached()
        except Exception:
            t = threading.Thread(target=self.tray_icon.run, daemon=True)
            t.start()

    def on_minimized_to_tray(self):
        try:
            if self.tray_icon and hasattr(self.tray_icon, "notify"):
                self.tray_icon.notify(
                    "Obsidian Boost PRIME ativo na bandeja. Discord rodando 100% livre.",
                    "Obsidian Boost PRIME"
                )
        except Exception:
            pass

    def shutdown(self):
        if self.engine:
            try:
                self.engine.stop_monitoring()
            except Exception:
                pass

        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass

        if self.ui:
            try:
                self.ui.quit()
                self.ui.destroy()
            except Exception:
                pass

        if self.mutex_handle:
            try:
                ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
                self.mutex_handle = None
            except Exception:
                pass

        sys.exit(0)


def main():
    app = ObsidianBoostPrimeApp()
    app.run()


if __name__ == "__main__":
    main()
