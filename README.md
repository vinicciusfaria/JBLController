# JBLController

Controlador em Python e C++ para os dispositivos de iluminação **JBL PartyLight Stick** e **JBL PartyLight Beam**, com suporte a controle manual via interface web e automação de iluminação sincronizada por timecode para o **VirtualDJ**.

---

## 1. O que é o projeto

O JBLController é um sistema para gerenciar e automatizar as luzes JBL PartyLight Stick e JBL PartyLight Beam a partir de um computador, sem depender do aplicativo móvel JBL One. O projeto é composto por:

- Uma biblioteca Python que implementa o protocolo Bluetooth Low Energy (BLE) das luminárias.
- Um servidor local com interface web para controle manual de cores, brilho, velocidade e efeitos.
- Um mecanismo de automação (scheduler) que dispara mudanças de iluminação em posições específicas de faixas musicais.
- Um plugin nativo em C++ para VirtualDJ que envia telemetria de reprodução em tempo real para o controlador via UDP.

---

## 2. Motivação

O aplicativo oficial da JBL (JBL One) é voltado para uso doméstico em smartphones: ele não oferece integração com softwares de DJ, não possui suporte a automação de iluminação sincronizada com músicas e não expõe uma API para controle externo.

Este projeto foi criado para permitir que DJs e operadores de iluminação utilizem os PartyLights como parte de um setup de palco, sincronizando efeitos visuais com os pontos estruturais das músicas (intros, builds, drops e transições) tocadas no VirtualDJ.

---

## 3. Funcionalidades atuais

### Controle de hardware (BLE)
- Conexão e controle simultâneo de múltiplos dispositivos PartyLight Stick e Beam.
- Ajuste de cor base (RGB), brilho geral (0 a 100%) e velocidade de animação.
- Seleção de modos de efeito suportados pelo firmware de cada modelo.
- Fallback automático de efeitos: comandos incompatíveis com o Beam (como cores estáticas lineares) são mapeados para alternativas dinâmicas compatíveis (como NEON ou LOOP).
- Controle da luz traseira independente no PartyLight Stick.
- Ativação e desativação do microfone interno para reação ao som (Sound Reactive).
- Reconexão automática em caso de perda temporária de sinal BLE.

### Automação de Cues e Timecode
- Banco de dados SQLite local (`faria_fx.db`) para armazenar Cues vinculados a cada faixa musical.
- Notação de tempo musical em compassos e tempos (Bars, ex: `17.1`).
- Disparo de Cues baseado na posição de reprodução recebida do VirtualDJ.
- Suporte a seeks e rewinds: quando a agulha é movida, o estado de iluminação é recalculado para corresponder ao último ponto da linha do tempo.
- Pré-visualização física: ao clicar em copiar ou editar um Cue na interface web, as luzes conectadas assumem imediatamente o preset selecionado para conferência visual.

### Painel Web
- Interface em página única acessível pelo navegador (`http://localhost:8080`).
- Color wheel em canvas para seleção de cores.
- Controles deslizantes de brilho e velocidade com atualização bidirecional.
- Botões de macros rápidas (Blackout, Cor Sólida, Strobo, Fuego).
- Gerenciamento de Cues da faixa atual (adicionar, editar, copiar, ativar/desativar e excluir).

---

## 4. Arquitetura

O sistema é dividido em três camadas:

```text
[ VirtualDJ ]
      │ (Plugin C++ FariaFX.dll - UDP 30 FPS / porta 9666)
      ▼
[ Backend Python (jbl_controller) ]
      ├── playback.py     -> Recebe e normaliza telemetria do VirtualDJ
      ├── faria_engine.py -> Scheduler de timecode e sincronização de Cues
      ├── faria_db.py     -> Persistência SQLite de faixas e eventos
      ├── controller.py   -> Máquina de estados da mesa de controle
      ├── stage.py        -> Gerenciamento do conjunto de luminárias e fallbacks
      └── partylight.py   -> Comunicação GATT BLE via Bleak
      │ (WebSockets / HTTP)
      ▼
[ Interface Web (Browser) ]
```

### Componentes principais

- `src/jbl_controller/protocol.py`: Codificação e decodificação de pacotes TLV binários com framing `0xAA`.
- `src/jbl_controller/partylight.py`: Gerenciamento da conexão BLE com cada luminária individual via Bleak.
- `src/jbl_controller/stage.py`: Abstração de palco que distribui comandos para múltiplos dispositivos e aplica regras de compatibilidade de hardware.
- `src/jbl_controller/controller.py`: Estado atual da mesa, fila de cores e execução de macros.
- `src/jbl_controller/playback.py`: Servidor UDP que recebe os dados de transporte do VirtualDJ e determina o deck master ativo.
- `src/jbl_controller/faria_engine.py`: Loop periódico (~50 Hz) que compara a posição atual da música com a lista de Cues cadastrados e dispara as alterações.
- `src/jbl_controller/web_app.py`: Servidor HTTP e WebSocket baseado em aiohttp.
- `virtualdj_plugin/`: Código-fonte C++ do plugin DSP para VirtualDJ.

---

## 5. Instalação e execução

### Pré-requisitos
- Python 3.10 ou superior no Windows.
- Adaptador Bluetooth compatível com Bluetooth Low Energy (BLE 4.0+).
- Dispositivos JBL PartyLight Stick e/ou Beam ligados e próximos ao computador.

### Instalação

1. Clone o repositório:
```powershell
git clone https://github.com/seu-usuario/JBLController.git
cd JBLController
```

2. Crie e ative um ambiente virtual:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

3. Instale as dependências:
```powershell
pip install bleak aiohttp
```

### Execução

Para iniciar o servidor web e o controlador:
```powershell
python examples/run_web.py
```

Abra o navegador em `http://localhost:8080`. Se houver luminárias ligadas no alcance do Bluetooth, a conexão será estabelecida automaticamente na inicialização.

---

## 6. Integração com VirtualDJ

O VirtualDJ comunica-se com o JBLController através de um plugin nativo de efeito sonoro (`FariaFX.dll`), que transmite dados de reprodução para `127.0.0.1:9666`.

### Instalação do plugin

Copie o arquivo pré-compilado para a pasta de plugins do VirtualDJ:
```powershell
copy virtualdj_plugin\FariaFX.dll "%LOCALAPPDATA%\VirtualDJ\Plugins64\SoundEffect\FariaFX.dll"
```

Caso queira recompilar a partir do código-fonte:
1. Obtenha o header `vdjPlugin8.h` no portal de desenvolvedores do VirtualDJ e coloque-o em `virtualdj_plugin/src/`.
2. Execute o script de compilação:
```powershell
cd virtualdj_plugin
.\build.bat
```

### Ativação no VirtualDJ
1. Abra o VirtualDJ.
2. No slot de efeitos de som de cada deck (ou na saída Master), ative o efeito **FariaFX**.
3. O plugin iniciará o envio de telemetria contendo:
   - Caminho do arquivo da música.
   - Posição decorrida em milissegundos e tempo total.
   - Posição em batidas (calculada a partir do primeiro tempo da grade e do BPM).
   - Estado de reprodução (play/pause), pitch e BPM.
   - Volumes de fader, crossfader, equalização de graves e filtro.

O backend Python seleciona automaticamente qual deck é o dominante com base na posição dos faders e do crossfader.

---

## 7. Testes

Para executar a suíte de testes unitários:
```powershell
$env:PYTHONPATH="src"; python -m unittest discover tests
```

---

## 8. Documentação técnica

Para detalhes sobre a engenharia reversa e a arquitetura do projeto:

- [PROTOCOL.md](PROTOCOL.md): Estrutura de pacotes GATT, opcodes, tabela TLV e diferenças entre Stick e Beam.
- [PROJECT_STATE.md](PROJECT_STATE.md): Estado detalhado de cada componente do sistema, separando o que foi confirmado em hardware do que ainda é hipótese.
- [docs/LIGHT_MODES.md](docs/LIGHT_MODES.md): Catálogo de IDs de efeitos e descrições dos padrões visuais.
- [docs/decisions.md](docs/decisions.md): Registro de decisões técnicas tomadas durante o desenvolvimento.
- [docs/AUDITORIA_DE_RISCO_LIVE.md](docs/AUDITORIA_DE_RISCO_LIVE.md): Análise de pontos de falha e procedimentos operacionais para apresentações ao vivo.
