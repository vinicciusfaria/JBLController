# JBLController

Controlador em Python e C++ para luminárias **JBL PartyLight Stick** e **JBL PartyLight Beam**, com interface web local e sincronização de efeitos de iluminação com o **VirtualDJ**.

---

## 1. O que é o JBLController?

O JBLController é um software que permite controlar luminárias JBL PartyLight diretamente do computador, usando Bluetooth Low Energy (BLE). Ele inclui:

- Uma biblioteca em Python que empacota e envia comandos no protocolo proprietário das luminárias.
- Um servidor web local com painel no navegador para ajuste manual de cores, brilho, velocidade e efeitos.
- Um agendador de eventos (scheduler) que dispara mudanças de iluminação em pontos pré-definidos das músicas tocadas no VirtualDJ.
- Um plugin em C++ para o VirtualDJ que envia dados de reprodução (tempo, BPM, batidas e faders) para o controlador via rede local (UDP).

---

## 2. Por que ele existe?

O aplicativo oficial da JBL (JBL One) funciona apenas em smartphones e foi desenhado para uso doméstico. Ele não oferece integração com programas de DJ, não possui suporte a timecode ou automação por batidas e não expõe uma interface de controle para terceiros.

O objetivo do JBLController é permitir que essas luminárias sejam usadas como parte de um setup de iluminação de palco ou estúdio, trocando de cor e efeito de acordo com a música em execução no VirtualDJ, sem necessidade de operação manual contínua durante a apresentação.

---

## 3. Dispositivos suportados

- **JBL PartyLight Stick:** Suporte a controle de cor RGB, brilho, velocidade, efeitos nativos da torre de LEDs, modo de cor sólida contínua e luz traseira branca independente.
- **JBL PartyLight Beam:** Suporte a controle de cor RGB, brilho e modos de projeção dinâmica (como NEON e LOOP). O Beam não possui LED traseiro e não suporta o modo de cor sólida estática (`STATIC`), de modo que comandos de cor fixa são mapeados para efeitos em movimento compatíveis.

---

## 4. O que já funciona?

### Comunicação BLE e controle manual
- Descoberta e conexão simultânea com múltiplos dispositivos PartyLight Stick e Beam.
- Envio de comandos de cor RGB, nível de brilho (0 a 100%) e velocidade de animação.
- Seleção de modos de animação suportados pelo firmware de cada aparelho.
- Ativação da luz traseira no PartyLight Stick.
- Ativação e desativação do microfone interno para reação ao som.
- Reconexão automática em segundo plano caso uma luminária perca sinal temporariamente.

### Automação com VirtualDJ
- Recepção contínua de telemetria do VirtualDJ via UDP na porta 9666 (30 atualizações por segundo).
- Rastreamento contínuo de batidas musicais em formato de compasso (Bars, ex: `17.1`).
- Identificação do deck ativo com base na posição dos faders de volume e crossfader.
- Detecção de corte de frequências graves através dos botões de EQ Low e do filtro bipolar (High-Pass).
- Disparo de Cues salvos em banco SQLite local (`faria_fx.db`) quando a música atinge o tempo configurado.
- Tratamento de mudanças de posição (seeks e rewinds), rearmando o estado de iluminação correspondente ao trecho atual da música.

### Interface Web
- Painel acessível pelo navegador em `http://localhost:8080`.
- Roda de cores em canvas para seleção de tons.
- Sliders para controle direto de brilho e velocidade.
- Tabela de Cues com cadastro, edição, exclusão e cópia de eventos.
- Pré-visualização física: ao clicar em copiar ou editar um Cue, as luzes conectadas assumem imediatamente as cores e efeitos daquele evento para conferência visual.

---

## 5. Como o sistema é organizado?

A estrutura de arquivos do projeto é a seguinte:

```text
JBLController/
├── src/jbl_controller/
│   ├── protocol.py         # Codificação e decodificação de pacotes TLV (framing 0xAA)
│   ├── partylight.py       # Conexão GATT individual com cada aparelho via Bleak
│   ├── group.py            # Agrupamento lógico de luminárias
│   ├── stage.py            # Coordenação de palco e fallbacks entre Stick e Beam
│   ├── controller.py       # Estado da mesa, fila de cores e execução de macros
│   ├── playback.py         # Servidor UDP para recepção de telemetria do VirtualDJ
│   ├── faria_db.py         # Banco SQLite de faixas, nomes alternativos e Cues
│   ├── faria_engine.py     # Agendador periódico de eventos de iluminação
│   ├── patterns.py         # Enumeração dos modos de animação do firmware
│   ├── exceptions.py       # Exceções personalizadas da biblioteca
│   ├── web_app.py          # Servidor HTTP e WebSocket com aiohttp
│   └── static/
│       └── index.html      # Interface web em página única (HTML5, CSS, JS)
├── virtualdj_plugin/
│   ├── src/
│   │   ├── faria_vdj_plugin.cpp # Plugin nativo DSP para VirtualDJ (C++14)
│   │   ├── FariaFX.def          # Definições de exportação da DLL
│   │   └── vdjPlugin8.h         # Header do SDK do VirtualDJ
│   ├── build.bat                # Script de compilação direta via MSVC
│   ├── CMakeLists.txt           # Configuração de compilação CMake
│   ├── FariaFX.dll              # Binário compilado pronto para uso
│   └── README.md                # Documentação técnica do plugin
├── tests/                       # Testes unitários automatizados
├── examples/
│   ├── run_web.py               # Script principal de execução da interface web
│   └── demo_stage.py            # Exemplo de controle em linha de comando
├── captures/                    # Logs de pacotes brutos capturados em laboratório
├── docs/                        # Documentação detalhada de engenharia reversa
├── PROTOCOL.md                  # Especificação técnica do protocolo BLE
├── PROJECT_STATE.md             # Estado detalhado de cada componente do sistema
├── TODO.md                      # Lista de tarefas ativas
├── GEMINI.md                    # Instruções de desenvolvimento
└── CHATGPT.md                   # Papel de revisão consultiva
```

---

## 6. Como instalar?

### Pré-requisitos
- Sistema operacional Windows 10 ou 11 (64 bits).
- Python 3.10 ou superior instalado.
- Adaptador Bluetooth compatível com Bluetooth Low Energy (BLE 4.0 ou superior).
- Pelo menos um dispositivo JBL PartyLight Stick ou Beam ligado próximo ao computador.

### Passo a passo

1. Clone o repositório ou baixe o código-fonte:
```powershell
git clone https://github.com/vinicciusfaria/JBLController.git
cd JBLController
```

2. Crie e ative um ambiente virtual:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

3. Instale as bibliotecas necessárias:
```powershell
pip install bleak aiohttp
```

---

## 7. Como executar?

1. Verifique se o Bluetooth do computador está ativado e as luminárias estão ligadas.
2. Inicie o servidor:
```powershell
python examples/run_web.py
```
3. O terminal fará a busca por aparelhos com o nome "PartyLight" e tentará se conectar. Caso não encontre nenhum, o programa entrará em modo de demonstração (permitindo testar a interface e a integração com o VirtualDJ sem luminárias físicas).
4. Abra o navegador e acesse:
```text
http://localhost:8080
```

---

## 8. Como funciona a integração com VirtualDJ?

A integração é feita por um plugin compilado em C++ (`FariaFX.dll`) que roda dentro do VirtualDJ como efeito sonoro.

### Instalação do plugin
Copie a DLL pré-compilada para a pasta de plugins do VirtualDJ no Windows:
```powershell
copy virtualdj_plugin\FariaFX.dll "%LOCALAPPDATA%\VirtualDJ\Plugins64\SoundEffect\FariaFX.dll"
```

### Ativação
1. Abra o VirtualDJ.
2. No painel de efeitos de som de um deck ou no slot Master, ative o efeito **FariaFX**.
3. O plugin cria uma thread secundária que consulta dados do deck a cada ~33 ms (30 FPS) e envia um pacote JSON via UDP para `127.0.0.1:9666`.
4. O backend do JBLController (`playback.py`) recebe os pacotes e repassa as informações para o agendador (`faria_engine.py`), que sincroniza a linha do tempo e dispara os Cues configurados.

---

## 9. Onde estão os documentos técnicos?

Para consultar dados de engenharia reversa, formato de pacotes e decisões de implementação:

- [PROTOCOL.md](PROTOCOL.md): Estrutura completa de pacotes GATT, opcodes, tabela TLV e diferenças entre Stick e Beam.
- [PROJECT_STATE.md](PROJECT_STATE.md): Estado atual de cada módulo, separando o que foi testado em hardware do que ainda é hipótese.
- [TODO.md](TODO.md): Lista de pendências, melhorias em andamento e pontos em investigação.
- [docs/LIGHT_MODES.md](docs/LIGHT_MODES.md): Tabela de IDs de animação do firmware e seus comportamentos visuais.
- [docs/decisions.md](docs/decisions.md): Registro de decisões arquiteturais do projeto.
- [docs/AUDITORIA_DE_RISCO_LIVE.md](docs/AUDITORIA_DE_RISCO_LIVE.md): Análise técnica de riscos operacionais e contingências para apresentações ao vivo.
- [virtualdj_plugin/README.md](virtualdj_plugin/README.md): Detalhes de compilação e payload UDP do plugin para VirtualDJ.
