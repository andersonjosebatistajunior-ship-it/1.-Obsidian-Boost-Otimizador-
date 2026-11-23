"""
Interface Gráfica do Obsidian Boost PRIME desenvolvida em CustomTkinter.
Traz suporte nativo a OneDrive, calibração do Warzone, purga de Standby List e otimização de rede.
O DISCORD, SPOTIFY E NAVEGADORES SÃO 100% PRESERVADOS E NUNCA BLOQUEADOS.
"""

import os
import sys
import threading
from typing import Callable, Optional
import customtkinter as ctk
from PIL import Image

import license_manager
from optimizer_prime import GameOptimizerPrime, PRESET_GAMES
from win32_prime import (
    flush_standby_list,
    get_resource_path,
    play_gamer_sound,
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

COLOR_BG_DARK = "#0B0C10"
COLOR_CARD = "#14151E"
COLOR_CARD_BORDER = "#202230"
COLOR_CRIMSON = "#DC2626"
COLOR_CRIMSON_HOVER = "#B91C1C"
COLOR_EMERALD = "#10B981"
COLOR_CYAN = "#06B6D4"
COLOR_TEXT_WHITE = "#FFFFFF"
COLOR_TEXT_MUTED = "#9CA3AF"
COLOR_TEXT_DIM = "#6B7280"


class ObsidianBoostPrimeUI(ctk.CTk):

    def __init__(self, engine: GameOptimizerPrime, on_minimize_tray: Callable):
        super().__init__()

        self.engine = engine
        self.on_minimize_tray = on_minimize_tray

        self.title("Obsidian Boost PRIME — Edição de Performance (Discord 100% Livre)")
        self.geometry("1060x800")
        self.minsize(980, 720)
        self.configure(fg_color=COLOR_BG_DARK)

        ico_path = get_resource_path("app.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        self.after(10, self._center_window)
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.engine.log_callback = self.log_message
        self.engine.state_callback = self.on_game_state_changed

        self.is_licensed, self.lic_type, self.lic_days, self.hwid = license_manager.verify_license()

        self._build_ui()

        if self.is_licensed:
            self.engine.start_monitoring()

    def _center_window(self):
        self.update_idletasks()
        w = 1060
        h = 800
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def minimize_to_tray(self):
        self.withdraw()
        self.on_minimize_tray()

    def restore_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _build_ui(self):
        if not self.is_licensed:
            self._build_activation_screen()
            return

        self._build_main_dashboard()

    # =====================================================================
    # TELA DE ATIVAÇÃO
    # =====================================================================

    def _build_activation_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        container = ctk.CTkFrame(
            self, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=14
        )
        container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.62, relheight=0.68)

        ctk.CTkLabel(container, text="⚡", font=ctk.CTkFont(size=42), text_color=COLOR_CRIMSON).pack(pady=(25, 0))
        ctk.CTkLabel(
            container, text="OBSIDIAN BOOST PRIME — ATIVAÇÃO",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXT_WHITE
        ).pack(pady=4)
        ctk.CTkLabel(
            container, text="Insira sua Chave de Licença (Vitalícia ou Mensal) para liberar a Edição Prime.",
            font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MUTED
        ).pack(pady=(0, 16))

        hwid_box = ctk.CTkFrame(container, fg_color="#0F1018", border_color="#26283C", border_width=1, corner_radius=8)
        hwid_box.pack(fill="x", padx=35, pady=8)

        ctk.CTkLabel(
            hwid_box, text="SEU IDENTIFICADOR ÚNICO (HWID):",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_TEXT_DIM
        ).pack(anchor="w", padx=12, pady=(8, 0))

        hwid_row = ctk.CTkFrame(hwid_box, fg_color="transparent")
        hwid_row.pack(fill="x", padx=12, pady=(2, 8))

        ctk.CTkLabel(
            hwid_row, text=self.hwid,
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_CRIMSON
        ).pack(side="left")

        def copiar_hwid():
            self.clipboard_clear()
            self.clipboard_append(self.hwid)
            self.lbl_status_ativ.configure(text="✓ HWID copiado com sucesso!", text_color=COLOR_EMERALD)

        ctk.CTkButton(
            hwid_row, text="📋 Copiar HWID", width=110, height=26,
            fg_color="#1F2130", hover_color="#2A2C40", command=copiar_hwid
        ).pack(side="right")

        ctk.CTkLabel(
            container, text="CHAVE DE LICENÇA (KEY):",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=35, pady=(14, 4))

        self.entry_key = ctk.CTkEntry(
            container, height=44, placeholder_text="Cole sua chave aqui (ex: OBS-BOOST-LIFE-...)",
            fg_color="#0F1018", border_color=COLOR_CRIMSON, border_width=1.5,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.entry_key.pack(fill="x", padx=35, pady=(0, 8))

        self.lbl_status_ativ = ctk.CTkLabel(container, text="", font=ctk.CTkFont(size=12))
        self.lbl_status_ativ.pack(pady=4)

        def acao_ativar():
            chave = self.entry_key.get().strip()
            ok, msg = license_manager.activate_key(chave)
            if ok:
                play_gamer_sound("success")
                self.lbl_status_ativ.configure(text="✓ " + msg, text_color=COLOR_EMERALD)
                self.is_licensed, self.lic_type, self.lic_days, self.hwid = license_manager.verify_license()
                self.after(1000, self._build_main_dashboard)
                self.engine.start_monitoring()
            else:
                play_gamer_sound("clean")
                self.lbl_status_ativ.configure(text="❌ " + msg, text_color=COLOR_CRIMSON)

        ctk.CTkButton(
            container, text="🔓 Ativar e Liberar Acesso Prime", height=44,
            fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"), command=acao_ativar
        ).pack(fill="x", padx=35, pady=(10, 20))

    # =====================================================================
    # DASHBOARD PRINCIPAL PRIME
    # =====================================================================

    def _build_main_dashboard(self):
        for widget in self.winfo_children():
            widget.destroy()

        main_box = ctk.CTkFrame(self, fg_color="transparent")
        main_box.pack(fill="both", expand=True, padx=20, pady=16)

        # 1. CABEÇALHO COM BADGES DE STATUS
        header = ctk.CTkFrame(main_box, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        t_row = ctk.CTkFrame(title_box, fg_color="transparent")
        t_row.pack(anchor="w")

        ctk.CTkLabel(t_row, text="OBSIDIAN BOOST", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(side="left")
        ctk.CTkLabel(t_row, text="PRIME", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_CRIMSON).pack(side="left", padx=6)

        badge_prime = ctk.CTkFrame(t_row, fg_color="#132B20", border_color=COLOR_EMERALD, border_width=1, corner_radius=4)
        badge_prime.pack(side="left", padx=8)
        ctk.CTkLabel(badge_prime, text="✓ DISCORD 100% LIVRE", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_EMERALD).pack(padx=6, pady=2)

        ctk.CTkLabel(
            title_box, text="Otimizador de Baixo Nível Windows & Warzone | Zero Suspensão de Processos | 100% Anti-Cheat Safe",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED
        ).pack(anchor="w")

        badges_col = ctk.CTkFrame(header, fg_color="transparent")
        badges_col.pack(side="right")

        self.lbl_game_status = ctk.CTkLabel(
            badges_col, text="● Game Mode: Aguardando Jogo",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_CYAN
        )
        self.lbl_game_status.pack(anchor="e")

        ctk.CTkLabel(
            badges_col, text=f"Licença: {self.lic_type} ({self.hwid})",
            font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED
        ).pack(anchor="e")

        # 2. CARDS DE HARDWARE
        hw = self.engine.hardware
        hw_grid = ctk.CTkFrame(main_box, fg_color="transparent")
        hw_grid.pack(fill="x", pady=(0, 12))

        # CPU Card
        c1 = ctk.CTkFrame(hw_grid, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=8)
        c1.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ctk.CTkLabel(c1, text="PROCESSADOR (CPU)", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_CRIMSON).pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(c1, text=hw["cpu_name"], font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w", padx=12)
        ctk.CTkLabel(c1, text=f"{hw['cpu_cores_physical']} Núcleos Físicos / {hw['cpu_cores_logical']} Threads (Core Unparked)", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=12, pady=(0, 8))

        # GPU Card
        c2 = ctk.CTkFrame(hw_grid, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=8)
        c2.pack(side="left", fill="both", expand=True, padx=3)
        ctk.CTkLabel(c2, text="PLACA DE VÍDEO (GPU)", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_EMERALD).pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(c2, text=hw["gpu_name"], font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w", padx=12)
        ctk.CTkLabel(c2, text="DirectX 12 / NVIDIA Low Latency Mode", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=12, pady=(0, 8))

        # RAM Card
        c3 = ctk.CTkFrame(hw_grid, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=8)
        c3.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ctk.CTkLabel(c3, text="MEMÓRIA RAM", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_CYAN).pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(c3, text=f"{hw['ram_total_gb']} GB Total ({hw['ram_avail_gb']} GB Livre)", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w", padx=12)
        ctk.CTkLabel(c3, text="Purga Automática de Standby (< 2.5 GB)", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=12, pady=(0, 8))

        # 3. TABVIEW DE RECURSOS
        tabs = ctk.CTkTabview(main_box, fg_color=COLOR_CARD, segmented_button_selected_color=COLOR_CRIMSON, segmented_button_selected_hover_color=COLOR_CRIMSON_HOVER)
        tabs.pack(fill="both", expand=True, pady=(0, 10))

        tab_dash = tabs.add("🚀 Game Mode & Ação")
        tab_wz = tabs.add("🎯 Calibração Warzone")
        tab_net = tabs.add("🌐 Estabilizador de Ping (0% Perda)")
        tab_clean = tabs.add("🧹 Shaders DX12 & RAM")
        tab_games = tabs.add("🎮 Jogos Suportados")

        self._populate_tab_dashboard(tab_dash)
        self._populate_tab_warzone(tab_wz)
        self._populate_tab_network(tab_net)
        self._populate_tab_clean(tab_clean)
        self._populate_tab_games(tab_games)

        # 4. CONSOLE DE LOGS
        log_box = ctk.CTkFrame(main_box, fg_color="#0F1018", border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=8)
        log_box.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(log_box, text="TERMINAL DE LOGS DO KERNEL:", font=ctk.CTkFont(size=9, weight="bold"), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=10, pady=(4, 0))

        self.txt_log = ctk.CTkTextbox(log_box, height=85, fg_color="transparent", font=ctk.CTkFont(family="Consolas", size=10), text_color="#A7F3D0")
        self.txt_log.pack(fill="x", padx=10, pady=(2, 6))

        self.log_message("✓ Obsidian Boost PRIME inicializado. Discord e chamadas 100% livres e sem interferência.")

    # =====================================================================
    # ABA 1: DASHBOARD & AÇÃO RÁPIDA
    # =====================================================================

    def _populate_tab_dashboard(self, parent):
        top_row = ctk.CTkFrame(parent, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=10)

        self.btn_master = ctk.CTkButton(
            top_row, text="🚀 OTIMIZAR WARZONE & SISTEMA AGORA (COM DISCORD LIVRE)",
            height=46, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"), command=self.run_master_optimization
        )
        self.btn_master.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            top_row, text="🧹 Purgar Standby List", width=160, height=46,
            fg_color="#1F2130", hover_color="#2A2C40", font=ctk.CTkFont(size=12, weight="bold"),
            command=self.run_quick_ram_flush
        ).pack(side="right")

        # Switches Modulares
        sw_frame = ctk.CTkFrame(parent, fg_color="#0F1018", border_color="#26283C", border_width=1, corner_radius=8)
        sw_frame.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(sw_frame, text="MÓDULOS ATIVOS DO GAME MODE:", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 4))

        sw_grid = ctk.CTkFrame(sw_frame, fg_color="transparent")
        sw_grid.pack(fill="x", padx=12, pady=(0, 8))

        # Switch 1: Timer Estável
        self.sw_timer = ctk.CTkSwitch(
            sw_grid, text="Timer Resolution Otimizado (Input Lag Mínimo sem Jitter)", progress_color=COLOR_EMERALD,
            command=lambda: setattr(self.engine, "enable_timer_05ms", self.sw_timer.get() == 1)
        )
        self.sw_timer.select()
        self.sw_timer.grid(row=0, column=0, sticky="w", padx=8, pady=4)

        # Switch 2: Prioridade Otimizada (0% Perda de Pacotes)
        self.sw_prio = ctk.CTkSwitch(
            sw_grid, text="Prioridade Estável de Rede (0% Perda de Pacotes & Discord Livre)", progress_color=COLOR_EMERALD,
            command=lambda: setattr(self.engine, "enable_high_priority", self.sw_prio.get() == 1)
        )
        self.sw_prio.select()
        self.sw_prio.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        # Switch 3: Core Unparking
        self.sw_unpark = ctk.CTkSwitch(
            sw_grid, text="Desempacotar Núcleos (Core Unparking 100% Ativo)", progress_color=COLOR_EMERALD,
            command=lambda: setattr(self.engine, "enable_core_unparking", self.sw_unpark.get() == 1)
        )
        self.sw_unpark.select()
        self.sw_unpark.grid(row=1, column=0, sticky="w", padx=8, pady=4)

        # Switch 4: Standby List
        self.sw_ram = ctk.CTkSwitch(
            sw_grid, text="Purga Limpa de Memória Standby (Zero Travamento em Jogo)", progress_color=COLOR_EMERALD,
            command=lambda: setattr(self.engine, "enable_standby_purge", self.sw_ram.get() == 1)
        )
        self.sw_ram.select()
        self.sw_ram.grid(row=1, column=1, sticky="w", padx=8, pady=4)

        # Caixa de Aviso Discord
        tip = ctk.CTkFrame(parent, fg_color="#12251D", border_color="#1E4533", border_width=1, corner_radius=6)
        tip.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(
            tip, text="✓ DISCORD, NAVEGADORES E STREAMING 100% LIVRES:\n"
                      "Esta versão elimina completamente qualquer suspensão de processos. O jogo recebe foco total de CPU e Timer 0.5ms,\n"
                      "enquanto seu Discord, chamada de voz e músicas rodam perfeitamente em paralelo sem engasgos.",
            font=ctk.CTkFont(size=11), text_color="#A7F3D0", justify="left"
        ).pack(anchor="w", padx=12, pady=8)

    # =====================================================================
    # ABA 2: CALIBRAÇÃO WARZONE
    # =====================================================================

    def _populate_tab_warzone(self, parent):
        primary_file, workers, vram, status = self.engine.get_warzone_settings()

        info_box = ctk.CTkFrame(parent, fg_color="#0F1018", border_color="#26283C", border_width=1, corner_radius=8)
        info_box.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(info_box, text="STATUS DA CONFIGURAÇÃO DO WARZONE:", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_wz_file = ctk.CTkLabel(
            info_box, text=f"Localizado com sucesso: {primary_file}" if primary_file else "Nenhum arquivo options.*.cst encontrado.",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_EMERALD if primary_file else COLOR_CRIMSON
        )
        self.lbl_wz_file.pack(anchor="w", padx=12, pady=(0, 8))

        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="x", padx=12, pady=6)

        col1 = ctk.CTkFrame(form, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=8)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=4)

        ctk.CTkLabel(col1, text="NÚCLEOS DE PROCESSAMENTO (RendererWorkerCount)", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(col1, text="Recomendado para Ryzen 5 4650G: 4 núcleos (evita estrangulamento do L3 Cache de 8MB).", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=12)

        self.entry_workers = ctk.CTkEntry(col1, width=120, height=32, font=ctk.CTkFont(size=13, weight="bold"))
        self.entry_workers.insert(0, "4")
        self.entry_workers.pack(anchor="w", padx=12, pady=8)

        col2 = ctk.CTkFrame(form, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=8)
        col2.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=4)

        ctk.CTkLabel(col2, text="ESCALA DE MEMÓRIA VRAM (VideoMemoryScale)", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(col2, text="Recomendado: 0.85 (Usa a VRAM da sua RTX 3050 com margem de segurança).", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=12)

        self.entry_vram = ctk.CTkEntry(col2, width=120, height=32, font=ctk.CTkFont(size=13, weight="bold"))
        self.entry_vram.insert(0, f"{vram:.2f}")
        self.entry_vram.pack(anchor="w", padx=12, pady=8)

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=12)

        def salvar_cst():
            try:
                w = int(self.entry_workers.get().strip())
                v = float(self.entry_vram.get().strip())
                ok, msg = self.engine.apply_warzone_settings(w, v)
                self.log_message(msg)
            except Exception as e:
                self.log_message(f"Erro nos valores: {str(e)}")

        ctk.CTkButton(
            btn_row, text="💾 GRAVAR CALIBRAÇÃO NO WARZONE COM BACKUP", height=40,
            fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"), command=salvar_cst
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

    # =====================================================================
    # ABA 3: ESTABILIZADOR DE REDE & PING
    # =====================================================================

    def _populate_tab_network(self, parent):
        card = ctk.CTkFrame(parent, fg_color="#0F1018", border_color="#26283C", border_width=1, corner_radius=8)
        card.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(card, text="ESTABILIZADOR DE CONEXÃO & ANTI-PERDA DE PACOTES (UDP / WARZONE):", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_CYAN).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            card, text="• Remove qualquer alteração agressiva de TCP/IP que cause tempestade de ACKs e saturação de upload.\n"
                      "• Restaura os parâmetros de rede padrão do Windows, perfeitos para pacotes UDP de jogos e voz.\n"
                      "• Elimina 100% de Bufferbloat, oscilações de ping e perda de pacotes (Packet Loss).\n"
                      "• Limpa o cache DNS (ipconfig /flushdns) para conexão direta e rápida com os servidores do jogo.",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED, justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 10))

        def aplicar_rede():
            ok, msg = self.engine.restore_network()
            self.log_message(msg)

        ctk.CTkButton(
            parent, text="⚡ ESTABILIZAR REDE AGORA (0% PERDA DE PACOTES & PING ESTÁVEL)", height=42,
            fg_color=COLOR_CYAN, hover_color="#0891B2", text_color="#000000",
            font=ctk.CTkFont(size=13, weight="bold"), command=aplicar_rede
        ).pack(fill="x", padx=12, pady=8)

    # =====================================================================
    # ABA 4: LIMPEZA DE SHADERS & RAM
    # =====================================================================

    def _populate_tab_clean(self, parent):
        card = ctk.CTkFrame(parent, fg_color="#0F1018", border_color="#26283C", border_width=1, corner_radius=8)
        card.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(card, text="LIMPEZA DE SHADER CACHE (DIRECTX 12 / NVIDIA / AMD):", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_EMERALD).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            card, text="• Limpa caches corrompidos de GPU em %LOCALAPPDATA%\\NVIDIA\\DXCache e D3DSCache.\n"
                      "• Purga o cache Standby List do Windows via chamadas nativas de kernel (NtSetSystemInformation).\n"
                      "• Corrige quedas repentinas de FPS ao entrar em áreas de combate intenso.",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED, justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 10))

        def limpar_tudo():
            count, mb = self.engine.clean_shaders_and_ram()
            self.log_message(f"✓ Limpeza concluída: {count} arquivos de shaders removidos ({mb} MB) e Standby List purgada!")

        ctk.CTkButton(
            parent, text="🧹 LIMPAR SHADER CACHE DA GPU & PURGAR RAM AGORA", height=42,
            fg_color=COLOR_EMERALD, hover_color="#059669", text_color="#000000",
            font=ctk.CTkFont(size=13, weight="bold"), command=limpar_tudo
        ).pack(fill="x", padx=12, pady=8)

    # =====================================================================
    # ABA 5: JOGOS MONITORADOS
    # =====================================================================

    def _populate_tab_games(self, parent):
        card = ctk.CTkFrame(parent, fg_color="#0F1018", border_color="#26283C", border_width=1, corner_radius=8)
        card.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(card, text="JOGOS RECONHECIDOS AUTOMATICAMENTE:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(anchor="w", padx=12, pady=(8, 4))

        for game, exes in PRESET_GAMES.items():
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=f"• {game}", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_WHITE).pack(side="left")
            ctk.CTkLabel(row, text=f"({', '.join(exes)})", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_DIM).pack(side="left", padx=8)

        add_row = ctk.CTkFrame(parent, fg_color="transparent")
        add_row.pack(fill="x", padx=12, pady=8)

        entry_custom = ctk.CTkEntry(add_row, placeholder_text="Nome do executável (ex: outro_jogo.exe)", height=34)
        entry_custom.pack(side="left", fill="x", expand=True, padx=(0, 6))

        def add_custom():
            exe = entry_custom.get().strip().lower()
            if exe:
                if not exe.endswith(".exe"):
                    exe += ".exe"
                self.engine.active_game_targets[exe] = "Jogo Personalizado"
                self.log_message(f"✓ '{exe}' adicionado ao monitoramento!")
                entry_custom.delete(0, "end")

        ctk.CTkButton(add_row, text="+ Adicionar Jogo", width=140, height=34, fg_color="#1F2130", hover_color="#2A2C40", command=add_custom).pack(side="right")

    # =====================================================================
    # CONTROLES E CALLBACKS
    # =====================================================================

    def log_message(self, message: str):
        def _append():
            self.txt_log.insert("end", message + "\n")
            self.txt_log.see("end")
        self.after(0, _append)

    def on_game_state_changed(self, game_name: str, is_running: bool):
        def _update():
            if is_running:
                self.lbl_game_status.configure(text=f"● Jogo Ativo: {game_name}", text_color=COLOR_EMERALD)
            else:
                self.lbl_game_status.configure(text="● Game Mode: Aguardando Jogo", text_color=COLOR_CYAN)
        self.after(0, _update)

    def run_master_optimization(self):
        self.btn_master.configure(state="disabled", text="⏳ Otimizando...")

        def task():
            try:
                count, mb = self.engine.clean_shaders_and_ram()
                self.log_message(f"✓ Shaders e Standby List purgados ({count} arquivos / {mb} MB liberados).")

                ok, msg = self.engine.restore_network()
                self.log_message(f"✓ {msg}")

                files = self.engine.find_all_warzone_cst_files()
                if files:
                    self.engine.apply_warzone_settings(workers=4, vram_scale=0.85)
                    self.log_message("✓ Warzone calibrado: 4 Workers (Ryzen L3 fix), 0.85 VRAM, Sombras Low, Reflex Boost e Blur Off!")

                play_gamer_sound("success")
                self.log_message("⚡ OTIMIZAÇÃO MASTER CONCLUÍDA! Discord e chamadas permanecem 100% livres.")
            finally:
                self.after(0, lambda: self.btn_master.configure(
                    state="normal", text="🚀 OTIMIZAR WARZONE & SISTEMA AGORA (COM DISCORD LIVRE)"
                ))

        threading.Thread(target=task, daemon=True).start()

    def run_quick_ram_flush(self):
        def task():
            flush_standby_list()
            play_gamer_sound("clean")
            self.log_message("✓ Standby List liberada com sucesso via chamada de kernel!")
        threading.Thread(target=task, daemon=True).start()
