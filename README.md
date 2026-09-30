# JBLController

Jbl Controller é um projeto desenvolvido em Python e C++ que tem o objetivo de tornar o uso das Jbl Partylights algo profissional para a comunidade de DJs. A ideia do software surgiu devido as limitações do JBL One, que não permite o controle simultâneo de Sticks e Beams sem uma caixa Jbl com Auracast, além do mesmo ser de uso exclusivo para celualres. O programa faz engenharia reversa do protocolo Bluetooth Low Energy (BLE) dos dispositivos **JBL PartyLight Stick** e **JBL PartyLight Beam**, permitindo um maior controle sobre a iluminação, além de contar com automação de timecode em tempo real sincronizado com o **VirtualDJ**.

---

## 🎯 O Projeto

Diferente do aplicativo móvel da JBL (focado em uso doméstico casual), o **JBLController** foi arquitetado como uma central de palco e iluminação para DJs e produtores:

* **Controle Centralizado Multi-Luz:** Gerenciamento unificado de múltiplos PartyLight Sticks e Beams em sincronia milimétrica.
* **Auto-Discovery & Auto-Healing (Stage-Proof):** Detecta e conecta automaticamente nas caixas próximas via BLE. Se uma caixa for desligada da tomada e ligada novamente, uma rotina de background restabelece a conexão sem travar o show.
* **Hardware-Aware Fallback:** Ajuste automático de presets de acordo com as capacidades físicas de cada caixa (ex: Beams utilizam padrões adaptados como NEON/LOOP quando o Stick recebe modos lineares como STATIC).
* **Painel Web DJ Desk (`localhost:8080`):** Interface web moderna e responsiva com WebSockets bidirecionais de latência zero, Color Wheel em canvas, faders de velocidade/brilho, monitor de bateria e controle individual ou global de efeitos.
* **FARIA Light FX (Automação de Timecode):** Scheduler interno assíncrono (~50 Hz) integrado ao SQLite para disparo de Cues (cor, presets, efeitos) no milissegundo exato da música.
* **Integração Real VirtualDJ (C++ DSP Plugin):** Plugin nativo de alta performance (`FariaFX.dll`) que transmite telemetria em tempo real (tempo decorrido, BPM, pitch, status de play, volume, crossfader e equalização de graves) via UDP sem onerar a CPU do VirtualDJ.
* **Sincronia à Prova de Falhas (Backspin-Proof):** Detecção inteligente de pulos de agulha, scrubs, rewinds e backspins no VirtualDJ, rearmando instantaneamente o visual correto da iluminação.
* **Desempate Inteligente de Master Deck:** Transição automática de palco orientada por fader e corte/troca de graves (`eq_low`), permitindo que a luz acompanhe a música dominante mesmo com o crossfader no centro.
* **Modo Random de Troca de Faixa:** Sorteio automático de cores vivas e puras para faixas inéditas que ainda não possuem Cues cadastrados.

---

## 🏗️ Arquitetura do Sistema

```
JBLController/
├── src/jbl_controller/
│   ├── protocol.py         # Parser e builder agnóstico de pacotes TLV (AA 33, AA 13, etc.)
│   ├── partylight.py       # Wrapper BLE assíncrono (Bleak) por caixa com Auto-Healing
│   ├── group.py & stage.py # Orquestração em massa de luzes e hardware fallbacks
│   ├── controller.py       # Gerenciador de estado, fila de cores, macros (FUEGO, STROBO, BLACKOUT)
│   ├── playback.py         # Receptor UDP de telemetria do VirtualDJ e gestão de Master Deck
│   ├── faria_db.py         # Persistência SQLite de faixas, aliases e Cues de iluminação
│   ├── faria_engine.py     # Motor de scheduler de timecode com compensação de latência
│   ├── web_app.py          # Servidor aiohttp + WebSockets
│   └── static/             # Frontend completo (HTML5, Canvas, CSS moderno)
├── virtualdj_plugin/
│   ├── src/
│   │   ├── faria_vdj_plugin.cpp # Plugin DSP nativo C++ (Thread UDP a 30 FPS)
│   │   ├── vdjPlugin8.h         # Headers do SDK do VirtualDJ 8
│   │   └── FariaFX.def          # Declaração de exportações DLL
│   ├── CMakeLists.txt           # Build script para CMake
│   ├── build.bat                # Script de compilação 1-clique com MSVC
│   └── FariaFX.dll              # Binário compilado pronto para uso (64-bit)
├── tests/                       # Suíte de testes unitários automatizados
└── examples/
    └── run_web.py               # Ponto de entrada da aplicação
```

---

## 🚀 Como Executar

### 1. Pré-requisitos
- **Python 3.10+** (Recomendado 3.10 ou superior)
- **Bluetooth 4.0+** ativado no computador
- **VirtualDJ 8 / 2021 / 2023+** (64-bit)

### 2. Instalação das Dependências Python
```powershell
pip install bleak aiohttp
```

### 3. Instalação do Plugin do VirtualDJ
O binário pronto `virtualdj_plugin/FariaFX.dll` pode ser copiado diretamente para a pasta de plugins do VirtualDJ:
```powershell
copy virtualdj_plugin\FariaFX.dll "%LOCALAPPDATA%\VirtualDJ\Plugins64\SoundEffect\FariaFX.dll"
```
*(Se preferir compilar do zero, basta rodar `virtualdj_plugin\build.bat` tendo o Visual Studio Build Tools instalado).*

No VirtualDJ:
1. Abra o VirtualDJ.
2. Na aba de **Efeitos de Som (Sound Effect)** ou no slot Master, ative o efeito **FariaFX**.
3. O plugin iniciará automaticamente a transmissão UDP em `127.0.0.1:9666`.

### 4. Iniciar a Mesa de Iluminação
```powershell
python examples/run_web.py
```
Acesse `http://localhost:8080` no navegador.
- Se caixas JBL PartyLight estiverem ligadas por perto, o sistema se conectará automaticamente.
- Se nenhuma caixa for encontrada, o sistema inicia em modo demonstração permitindo testes de timecode e interface visual.

---

## 🧪 Rodando os Testes
Para rodar toda a suíte de testes unitários:
```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests
```

---

## 📄 Licença
Distribuído sob licença MIT. Feito para a comunidade de DJs e entusiastas de engenharia reversa.
