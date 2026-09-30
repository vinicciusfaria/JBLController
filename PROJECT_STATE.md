# Estado Atual do Projeto: JBLController

Data da última atualização: 2026-09-30

---

## 1. Visão Geral
O **JBLController** evoluiu de uma investigação inicial de protocolo BLE para uma plataforma completa de iluminação de palco voltada para DJs. O ecossistema abrange desde decodificação TLV em baixo nível até um plugin nativo em C++ para VirtualDJ e uma suíte completa de automação de timecode em tempo real (FARIA Light FX) com interface web responsiva.

---

## 2. Engenharia Reversa BLE (CONCLUÍDO)
- **Protocolo TLV Homologado:** Enquadramento via `0xAA` (Opcode + Length Little-Endian).
- **Mapeamento de Escrita e Notificações:** Operações de controle via `AA 33` e leituras de estado via `AA 32` / `AA 12`.
- **Diferenças de Hardware Stick vs Beam:** Mapeamento completo de efeitos aceitos por cada dispositivo (ex: Stick aceita modo estático `STATIC`, enquanto o Beam foca em dinâmicas rotativas como `LOOP` e `NEON`).
- **Comandos Validados:** Brilho (0-100), Velocidade de efeito, Cores RGB em 24-bit, Seleção de padrões de animação, Luz traseira independente (Stick) e Detecção interna de áudio (Sound Reactive).

---

## 3. Biblioteca Python & Backend (`src/jbl_controller/`) (CONCLUÍDO)
- `protocol.py`: Codificador e decodificador TLV puro, modular e agnóstico de I/O.
- `partylight.py`: Cliente assíncrono sobre `bleak`. Inclui rotina de **Auto-Healing** (reconexão automática em background com restauração de estado sem interrupção da aplicação em caso de queda de energia ou sinal).
- `group.py` & `stage.py`: Orquestradores de dispositivos múltiplos com sistema de Fallback inteligente de hardware.
- `controller.py`: Máquina de estado da Mesa de DJ. Gerencia Fila de Cores circular protegida contra sobrecarga de memória, seleção independente de animações para Stick e Beam, e macros de palco (`BLACKOUT`, `FUEGO`, `STROBO`, `COR SOLIDA`).
- `playback.py`: Servidor UDP assíncrono para telemetria externa com gestão de Master Deck baseada em histerese de crossfader e desempate por equalização de graves (`eq_low`).
- `faria_db.py`: Camada de persistência SQLite com suporte a faixas, aliases e Cues de iluminação com timestamps em milissegundos.
- `faria_engine.py`: Motor de agendamento de timecode de alta frequência (~50 Hz) com compensação configurável de latência, suporte a retrospectiva de agulha (Seek), tolerância a backspins e modo de cor aleatória viva para novas faixas.
- `web_app.py`: Servidor aiohttp com WebSocket full-duplex sincronizando instantaneamente estado de hardware, timecode do VDJ e listagem de eventos.

---

## 4. Plugin Nativo VirtualDJ (`virtualdj_plugin/`) (CONCLUÍDO)
- **Tecnologia:** C++14 compilado como DLL Sound Effect de 64 bits (`FariaFX.dll`) baseada no SDK oficial do VirtualDJ 8.
- **Thread UDP Assíncrona:** Ciclo de transmissão a 30 FPS (`127.0.0.1:9666`) isolado do loop de áudio principal do VDJ para latência zero e ausência de travamentos.
- **Telemetria de Alta Precisão:**
  - Extração de tempo absoluto decorrido via `"get_time elapsed"` e tempo total via `"get_time total"` (imune a preferências de layout do usuário no VDJ).
  - Status de reprodução (`play`), detecção de pitch e BPM.
  - Monitoramento de volume e crossfader.
  - Extração dos níveis de equalização de graves dos decks ativos (`deck 1 eq_low` e `deck 2 eq_low`).
- **Facilidade de Compilação:** Script `build.bat` pronto para compilação em 1 clique via MSVC e cópia direta para a pasta de plugins do VirtualDJ.

---

## 5. Interface Web & Automação (CONCLUÍDO)
- **Mesa de DJ Responsiva:** Dark theme com Color Wheel canvas interativa, barras de progresso de status BLE, controles de intensidade e velocidade.
- **Tradução em Tempo Real:** Mapeamento integral de todos os nomes de efeitos de fábrica para português amigável ao operador (`EFFECT_NAMES_PT`).
- **Criador de Cues Dinâmicos:**
  - Botões de marcação rápida de cores estáticas primárias (`RED`, `GREEN`, `BLUE`).
  - Botão de "Snapshot" personalizado: empacota a cor exata da roda e os efeitos atuais de Stick e Beam em JSON e armazena na linha do tempo da música.
  - Visualização formatada dos Cues na listagem com indicador visual de cor e efeitos.
- **Sincronia à Prova de Backspins:** Acompanhamento automático da iluminação mesmo durante manipulação manual rápida do disco/jog wheel.

---

## 6. Próximas Inovações
1. **Transiente & Beat Detection Local:** Análise FFT do áudio em tempo real via Python para sincronia automática de batidas sem dependência de timecode.
2. **Integração MIDI:** Suporte a controladores físicos (Launchpad, Akai, etc.) via biblioteca `mido`.
3. **Exportação & Importação de Cues:** Compartilhamento de arquivos de timecode e mapas de shows entre DJs em formato JSON.