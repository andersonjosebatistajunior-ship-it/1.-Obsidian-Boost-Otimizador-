# ⚡ Obsidian Boost PRIME — PC & Warzone Optimizer

> Otimizador de Baixo Nível para Windows e *Call of Duty: Warzone* desenvolvido em Python e CustomTkinter.  
> **100% Anti-Cheat Safe** (Zero risco de banimento no Ricochet) | **Discord, Streaming e Chamadas de Voz 100% Livres**.

---

## 🎯 Principais Recursos

- **🚀 Calibração Direta do Warzone (.cst):**
  - Ajuste inteligente de `RendererWorkerCount` calibrado para os núcleos físicos reais da CPU (evita gargalo de L3 Cache).
  - Alocação precisa de `VideoMemoryScale` para a GPU sem estourar o limite de VRAM.
  - Otimizações competitivas em sombras (`SunShadowCascade`), reflexos e desativação de motion blur.
  - Destravamento da taxa de atualização da tela (`RefreshRate`) de 60Hz para 144Hz+.
  - Suporte de aceleração por hardware com **Variable Rate Shading (VRS)** para placas NVIDIA RTX.
  - Eliminação de física pesada de cápsulas de balas ejetadas em combate (`ShowBrass = false`).

- **🌐 Estabilizador de Conexão & Anti-Packet Loss (0% Perda de Pacotes):**
  - Reativação de **Hardware Checksum Offload** (IPv4, TCP, UDP) diretamente no chip da placa de rede física (Realtek/Intel).
  - Expansão de buffers de recebimento e transmissão para 1024x.
  - Elimina bufferbloat e oscilações de ping sem mexer em parâmetros agressivos de TCP.

- **⏱️ Resolução de Timer de Alta Precisão (1.0ms):**
  - Redução da latência de resposta de periféricos e mouse sem causar tempestade de interrupções de CPU.

- **🔋 Core Unparking & Desempenho Máximo:**
  - Desempacotamento de núcleos de processador via esquemas de energia do Windows para manter 100% dos núcleos acordados durante a gameplay.

- **🧹 Limpeza Profunda de Shader Cache & RAM Standby:**
  - Purga de caches corrompidos de GPU em DirectX 12 (`DXCache` / `D3DSCache`).
  - Purga segura da *Standby List* do Windows via chamadas nativas de kernel (`NtSetSystemInformation`).

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.11+
- **Interface Gráfica:** CustomTkinter (Dark Mode moderno com temática gamer)
- **APIs de Baixo Nível:** Win32 API / NTDLL (`ctypes`)
- **Controle de Sistema e Processos:** `psutil`, `pystray` (Bandeja do Windows), `subprocess`
- **Compilação:** PyInstaller (Standalone Executable com elevação UAC nativa)

---

## 📦 Como Executar

### Pré-requisitos
```bash
pip install -r requirements.txt
```

### Executar a partir do código-fonte:
```bash
python main.py
```

### Compilar para Executável (.exe):
```bash
build_exe.bat
```

---

## 📄 Licença
Distribuído sob a licença MIT. Consulte `LICENSE` para mais detalhes.
