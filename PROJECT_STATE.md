# Estado Atual do Projeto

Data da última atualização: 2026-09-30

---

## 1. Visão geral

O JBLController é um sistema em desenvolvimento que integra luminárias JBL PartyLight Stick e JBL PartyLight Beam a setups de DJ via Bluetooth Low Energy (BLE). O projeto conta com:
- Implementação do protocolo BLE proprietário descoberto por engenharia reversa.
- Backend em Python para controle manual e agendamento de Cues sincronizados com o VirtualDJ.
- Interface gráfica web em navegador local.
- Plugin C++ nativo para VirtualDJ para envio de telemetria de áudio e transporte via UDP.

---

## 2. Protocolo BLE

### Confirmado (validado em testes com hardware)
- **Framing GATT:** Pacotes contíguos iniciados com `0xAA`, seguidos de `Command ID`, `Payload Length` (1 byte), marcador `0x00` e campos TLV (`Field ID`, `Field Length`, `Value`).
- **UUID de escrita:** `65786365-6c70-6f69-6e74-2e636f6d0002` usando operação ATT Write Command (`0x52`, sem resposta).
- **UUID de notificação:** `65786365-6c70-6f69-6e74-2e636f6d0001` via GATT Notify.
- **Comandos de luz (`AA 33`):**
  - Brilho (`0x45`, 1 byte): valores de `0x00` (0%) a `0x64` (100%).
  - Cor RGB (`0x32`, 3 bytes): componentes `[RR, GG, BB]` diretos.
  - Modo/Efeito (`0x31`, 1 byte): ativação dos efeitos suportados pelo firmware.
  - Transição de cor / Static (`0x36`, 1 byte): `0x01` para cor sólida no Stick em conjunto com o modo `0x15` (STATIC).
  - Luz traseira do Stick (`0x49`, 1 byte): `0x00` desliga, `0x01` liga.
  - Velocidade do efeito (`0x46`, 1 byte): escala de `0x00` a `0x64`.
- **Comandos de hardware (`AA 13`):**
  - Detecção de som pelo microfone interno (`0x45`, 1 byte): `0x00` desliga, `0x01` liga.
- **Notificações recebidas:**
  - `AA 32`: estado da iluminação, incluindo lista de modos suportados no campo `0x4A`.
  - `AA 12`: telemetria do dispositivo (endereço MAC em `0x37`, número de série em `0x40`, versão de firmware em `0x41`).
- **Diferenças físicas de hardware:**
  - PartyLight Stick suporta modo estático (`STATIC` / `0x15`), luz traseira (`0x49`) e efeitos verticais de torre (ex: `CAMPFIRE`, `GRAVITY`, `LIGHTNING`).
  - PartyLight Beam é um projetor motorizado, não possui luz traseira física e ignora o modo estático `0x15`, exigindo efeitos dinâmicos como `NEON`, `LOOP` ou `BOUNCE`.

### Hipóteses (observadas em código ou logs, pendentes de confirmação física)
- **`0x47` em `AA 33` (`speakerIDtoLight`):** Carrega 2 bytes. Hipótese de ser usado pelo aplicativo oficial para identificar a posição espacial do dispositivo no palco (ex: esquerda/direita).
- **`0x46` em `AA 13` (`danceMode`):** Mapeado no APK oficial como booleano, mas seu efeito prático na iluminação ainda não foi diferenciado da detecção de som comum.
- **`0x3C` em `AA 13` (`AuracastMode`):** Mapeado no APK oficial, relacionado a recursos de transmissão LE Audio da JBL. Não testado por falta de caixa PartyBox compatível.
- **Leitura de Bateria (`AA 9D` / `AA 9E`):** Documentada no código do aplicativo para a Beam, ainda não implementada no controlador Python.

### Ainda não determinado
- **Opcodes `0x25` a `0x2A` (DFU):** Identificados como comandos de atualização de firmware (OTA). Não devem ser testados para evitar corrupção de firmware.
- Comportamento de agrupamento nativo entre múltiplas caixas gerido diretamente pelo firmware sem controle do host.

---

## 3. Backend Python (`src/jbl_controller/`)

### BLE (`partylight.py` e `protocol.py`)
- `protocol.py`: Codificação e decodificação completas para comandos `AA 33`, `AA 13`, `AA 31` e `AA 11`. Validado com testes unitários.
- `partylight.py`: Conexão individual assíncrona com reconexão automática em caso de desconexão.
- *Status:* Funcional em laboratório com PartyLight Stick e Beam.

### Stage (`stage.py` e `group.py`)
- Agrupamento de dispositivos e distribuição de comandos em lote.
- Aplicação de regras de fallback de efeitos quando um comando não é suportado pelo hardware de destino.
- *Status:* Funcional.

### Playback (`playback.py`)
- Servidor UDP ouvindo na porta `9666`.
- Decodifica pacote JSON da telemetria do VirtualDJ.
- Gerenciamento de deck master ativo por análise de faders de volume, crossfader, equalização de graves (`eq_low`) e High-Pass `filter`.
- Fallback para relógio local (mock) quando o VirtualDJ deixa de enviar pacotes por mais de 1.5s.
- *Status:* Funcional e validado com testes unitários automatizados.

### Database (`faria_db.py`)
- Persistência SQLite local em `faria_fx.db`.
- Tabelas: `tracks`, `track_aliases` e `cues`.
- Armazena Cues com tempo em milissegundos e posição musical em batidas (`beat_pos`).
- *Status:* Funcional.

### Scheduler (`faria_engine.py`)
- Loop periódico de verificação a ~50 Hz.
- Dispara Cues quando a reprodução atinge a posição da batida cadastrada.
- Sincroniza o estado em saltos manuais (seeks/rewinds), reaplicando o último evento válido anterior à nova posição.
- *Status:* Funcional, com correção aplicada para re-disparo após rewinds antes de pontos de corte.

---

## 4. Plugin VirtualDJ (`virtualdj_plugin/`)

- Plugin de efeito sonoro DSP em C++ (`FariaFX.dll`) baseado no SDK 8 oficial do VirtualDJ.
- Thread em segundo plano enviando telemetria a 30 FPS para `127.0.0.1:9666` via UDP.
- Dados extraídos:
  - Tempo decorrido (`get_time elapsed`) e tempo total.
  - Batida contínua absoluta calculada por `((timeMs - firstBeatMs) / 60000.0) * bpm` (substituiu o uso de `SongPosBeats`, que reiniciava dentro de cada compasso).
  - Estado de reprodução, BPM e pitch.
  - Volumes de canais (`deck 1 volume`, `deck 2 volume`), crossfader e master deck.
  - Níveis de graves (`eq_low`) e filtros de frequência (`filter`) dos Decks 1 e 2.
- *Status:* Compilado e validado em execução conjunta com o VirtualDJ 2021/2023.

---

## 5. Interface Web (`src/jbl_controller/static/index.html`)

- Painel de controle em página única servido via aiohttp.
- Comunicação bidirecional com o backend via WebSockets.
- Ajuste de cor por roda de cores (canvas), sliders de brilho e velocidade.
- Tabela de Cues com visualização em compassos (Bars, ex: `17.1`).
- Função de preview físico: ao clicar em copiar ou editar um Cue, o comando de cor e efeito é enviado imediatamente às luminárias para conferência visual.
- *Status:* Funcional.

---

## 6. Testes

- 26 testes unitários automatizados cobrindo:
  - Enquadramento e parsing do protocolo (`test_protocol.py`).
  - Lógica de presets e fallbacks (`test_presets.py`).
  - Conexão e métodos do PartyLight (`test_partylight.py`).
  - Sincronização do scheduler, transições de master deck e banco de Cues (`test_faria.py`).
- Execução com 100% de aprovação via `python -m unittest discover tests`.

---

## 7. Próximos passos

1. Implementar leitura do nível de bateria (`AA 9D` / `AA 9E`) na PartyLight Beam.
2. Investigar o comportamento prático do campo `danceMode` (`0x46` em `AA 13`).
3. Adicionar recurso de importação e exportação de Cues em arquivos JSON portáveis.
4. Avaliar proteção contra congestionamento de fila BLE em movimentações contínuas e rápidas de faders.