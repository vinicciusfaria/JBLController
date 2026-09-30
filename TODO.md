# TODO - JBLController

## Protocolo & Engenharia Reversa BLE (CONCLUÍDO ✅)
- [x] Decodificar estrutura de enquadramento (Framing com `0xAA` + Opcode + Comprimento LE).
- [x] Mapear arquitetura TLV das notificações e comandos de escrita (`AA 33`, `AA 32`, `AA 13`, `AA 12`).
- [x] Mapear diferenças de hardware físico e limitações de efeitos entre Stick e Beam.
- [x] Validar controle bidirecional completo de brilho, velocidade, cores RGB, luz traseira e som.

## Backend em Python (`src/jbl_controller/`) (CONCLUÍDO ✅)
- [x] Implementar parser modular e agnóstico do protocolo (`protocol.py`).
- [x] Implementar cliente BLE assíncrono unificado com Auto-Healing anti-quedas (`partylight.py`).
- [x] Implementar orquestrador multi-luz com hardware fallbacks (`stage.py`).
- [x] Implementar máquina de estado com fila de cores circular e macros assíncronas (`controller.py`).
- [x] Construir servidor WebSockets full-duplex de baixa latência (`web_app.py`).

## VISKO Light FX & Automação de Timecode (CONCLUÍDO ✅)
- [x] Persistência SQLite para faixas, aliases e Cues com timestamps em milissegundos (`visko_db.py`).
- [x] Scheduler de alta precisão (~50 Hz) com compensação de latência (`visko_engine.py`).
- [x] Retrospectiva inteligente de timecode (Seek / Play / Scrub).
- [x] Suporte a Backspins e saltos rápidos na linha do tempo (Backspin-proof).
- [x] Modo Random de cor viva na troca de faixas não mapeadas.
- [x] Cues personalizados com snapshots de cor e efeitos salvos em formato JSON estruturado.

## Plugin VirtualDJ C++ (`virtualdj_plugin/`) (CONCLUÍDO ✅)
- [x] Desenvolver plugin DSP nativo em C++ baseado no SDK oficial do VirtualDJ 8.
- [x] Thread de telemetria assíncrona UDP a 30 FPS sem travar o loop de áudio.
- [x] Extração de tempo decorrido oficial imune a preferências visuais de interface (`"get_time elapsed"`).
- [x] Transmissão de BPM, pitch, volume, crossfader e estado de reprodução.
- [x] Extração e transmissão dos graves dos decks (`deck 1 eq_low` e `deck 2 eq_low`).
- [x] Lógica de histerese e desempate de Master Deck por equalização de graves no Python (`playback.py`).
- [x] Script de compilação facilitado em 1 clique (`build.bat`).

## Frontend UI (`static/index.html`) (CONCLUÍDO ✅)
- [x] Layout estilo mesa de DJ com tema Dark e Color Wheel canvas interativa.
- [x] Faders de brilho e velocidade em tempo real com broadcast bidirecional.
- [x] Botões rápidos para cores estáticas (`RED`, `GREEN`, `BLUE`).
- [x] Painel de criação e listagem formatada de Cues personalizados.
- [x] Tradução dinâmica de nomes de efeitos de fábrica para Português (`EFFECT_NAMES_PT`).
- [x] Sincronia de estado do checkbox de modo Random e Seguir Cues com o servidor.

## Inovações Futuras 🚀
- [ ] **Beat Detection Local / FFT:** Análise em tempo real do stream de áudio do sistema para disparo de efeitos rítmicos sem necessidade de marcação manual prévia.
- [ ] **Integração MIDI:** Suporte a pads físicos (Launchpad, Akai APC, etc.) usando a biblioteca `mido`.
- [ ] **Exportação & Importação de Cues:** Salvar e carregar mapas completos de timecode de sets em arquivos JSON portáveis.
- [ ] **Standalone Packaging:** Empacotar a aplicação em executável único com PyInstaller ou PyWebView.
