# Estado Atual do Projeto

Data da última atualização: 2026-09-30

---

## 1. Visão geral

O JBLController permite operar luminárias JBL PartyLight Stick e JBL PartyLight Beam a partir do computador via Bluetooth Low Energy (BLE), dispensando o uso do aplicativo oficial para celular. O sistema é composto por:

- Uma biblioteca Python para empacotamento GATT e controle de palco.
- Um agendador (scheduler) com banco SQLite para disparo de efeitos em pontos pré-definidos de músicas.
- Um servidor web local com painel no navegador.
- Um plugin em C++ para VirtualDJ que transmite dados de reprodução via UDP.

O foco atual do desenvolvimento é a estabilidade de telemetria durante a reprodução no VirtualDJ e o controle consistente de Cues na interface.

---

## 2. Protocolo BLE

### Confirmado (validado em testes com hardware)

| Recurso | Detalhes | Modelo validado |
|---|---|---|
| **Framing GATT** | Pacotes contíguos: `[0xAA] [Command ID] [Payload Len] [0x00] [Field ID] [Field Len] [Value...]` | Stick e Beam |
| **Canal de escrita** | UUID `65786365-6c70-6f69-6e74-2e636f6d0002` via ATT Write Command (`0x52`, sem resposta) | Stick e Beam |
| **Canal de notificação** | UUID `65786365-6c70-6f69-6e74-2e636f6d0001` via GATT Notify | Stick e Beam |
| **Controle de Brilho** | Field `0x45` em `AA 33`, escala de `0x00` (0%) a `0x64` (100%) | Stick e Beam |
| **Controle de Cor RGB** | Field `0x32` em `AA 33`, 3 bytes `[RR, GG, BB]` | Stick e Beam |
| **Seleção de Modo/Efeito** | Field `0x31` em `AA 33`, 1 byte com o ID do efeito do firmware | Stick e Beam |
| **Cor Sólida Estática** | Modo `0x15` (`STATIC`) combinado com `PatternLooping = 0x01` (`0x36`) | Apenas Stick (o Beam ignora o modo `0x15`) |
| **Velocidade de Animação** | Field `0x46` em `AA 33`, escala de `0x00` a `0x64` | Stick |
| **Luz Traseira** | Field `0x49` em `AA 33`, `0x00` desliga e `0x01` liga | Apenas Stick (o Beam não possui LED traseiro) |
| **Detecção de Som** | Field `0x45` em `AA 13`, `0x00` desliga e `0x01` liga o microfone interno | Stick |
| **Lista de Modos Suportados** | Field `0x4A` em notificações `AA 32`, informa os IDs suportados pelo modelo | Stick (20 modos) e Beam (7 modos) |
| **Metadados do Hardware** | Notificação `AA 12`: MAC (`0x37`), Serial (`0x40`), Firmware (`0x41`) | Stick e Beam |

### Hipóteses (observadas em código ou logs, pendentes de confirmação física)

- **`speakerIDtoLight` (`0x47` em `AA 33`):** 2 bytes observados no APK. Hipótese de ser usado para posicionamento espacial no palco (ex: esquerda/direita).
- **`danceMode` (`0x46` em `AA 13`):** Booleano mapeado no APK. Efeito visual prático ainda não diferenciado da detecção de som padrão.
- **`AuracastMode` (`0x3C` em `AA 13`):** Mapeado no APK em relação ao recurso de broadcast LE Audio com caixas PartyBox. Não testado por falta de equipamento transmissor compatível.
- **Leitura de Bateria (`AA 9D` / `AA 9E`):** Identificada no APK para a PartyLight Beam, ainda não implementada no código Python.

### Ainda não determinado

- **Comandos de Firmware OTA / DFU (`0x25` a `0x2A`):** Identificados no APK, mas categorizados como perigosos para envio manual. Não devem ser disparados para evitar risco de travar a memória flash dos aparelhos.

---

## 3. Backend Python (`src/jbl_controller/`)

### BLE (`protocol.py` e `partylight.py`)
- **Estado:** Implementado e testado.
- `protocol.py`: Monta e decodifica pacotes binários para comandos `AA 33`, `AA 13`, `AA 31` e `AA 11`. Coberto por testes unitários em `tests/test_protocol.py`.
- `partylight.py`: Gerencia a conexão com cada aparelho via Bleak. Possui loop de reconexão automática com intervalo fixo de 5 segundos.

### Stage e Agrupamento (`stage.py` e `group.py`)
- **Estado:** Implementado e testado.
- Permite despachar comandos de cor, brilho e efeitos para múltiplas luminárias de uma só vez.
- Implementa regra de fallback: se um efeito enviado não constar na lista de modos suportados do aparelho (como cor sólida no Beam), converte automaticamente para um modo suportado (`NEON` ou `LOOP`).

### Playback e Telemetria (`playback.py`)
- **Estado:** Implementado e testado.
- Abre servidor UDP ouvindo na porta 9666.
- Recebe mensagens JSON do plugin do VirtualDJ e mantém o estado de reprodução dos Decks 1 e 2.
- Determina o Deck Master ativo com base nos faders de volume e crossfader, com histerese para evitar oscilações em transições lentas.
- Monitora os botões de grave (`eq_low`) e o filtro bipolar (`filter`) para registrar cortes de grave na variável `bass_cut`.
- Se o VirtualDJ parar de enviar dados por mais de 1,5s com a música tocando, assume modo de simulação local (mock) baseado no relógio do computador.

### Banco de Dados (`faria_db.py`)
- **Estado:** Implementado e testado.
- SQLite local (`faria_fx.db`) com tabelas: `tracks`, `track_aliases` e `events`.
- Armazena Cues com tempo em milissegundos e posição relativa em batidas (`beat_pos`).
- Operações de adicionar, editar, excluir e consultar eventos implementadas e testadas.

### Agendador de Cues (`faria_engine.py`)
- **Estado:** Implementado e testado.
- Executa verificação periódica em loop assíncrono a cada ~20 ms (~50 Hz).
- Compara a posição atual em batidas da música com os Cues cadastrados e dispara os efeitos correspondentes.
- Trata saltos na música (seeks para frente ou para trás): quando a agulha é movida, busca o último Cue válido anterior à nova posição e aplica o efeito imediatamente.
- Possui correção validada por teste unitário para rearmar eventos após rewinds anteriores ao ponto de disparo.

---

## 4. Plugin VirtualDJ (`virtualdj_plugin/`)

- **Estado:** Implementado, compilado e testado em execução real com VirtualDJ.
- Desenvolvido em C++14 implementando a interface `IVdjPluginDsp8` do SDK do VirtualDJ.
- Compilação via MSVC gerando `FariaFX.dll`.
- Uma thread em segundo plano envia pacotes UDP JSON a 30 FPS para `127.0.0.1:9666`.
- Dados extraídos e transmitidos:
  - Caminho do arquivo (`get_filepath`).
  - Tempo decorrido em ms (`get_time elapsed`) e tempo total (`get_time total`).
  - Posição contínua em batidas, calculada a partir de `((timeMs - firstBeatMs) / 60000.0) * bpm` (substituiu o uso de `SongPosBeats`, que reiniciava dentro do compasso de 4 tempos).
  - Estado de reprodução (`play`), BPM e pitch.
  - Níveis de fader dos canais (`deck 1 volume`, `deck 2 volume`), fader atual (`volume`) e crossfader.
  - Identificação de canal com memorização em cache (`cachedDeck`) para evitar trocas erráticas durante manipulação dos faders.
  - Níveis de equalização de graves (`deck 1 eq_low`, `deck 2 eq_low`) e filtros bipolares (`deck 1 filter`, `deck 2 filter`).

---

## 5. Interface Web (`src/jbl_controller/static/index.html` e `web_app.py`)

- **Estado:** Implementado e testado.
- Servidor HTTP e WebSocket provido por `aiohttp` rodando em `http://localhost:8080`.
- Roda de cores interativa em canvas para ajuste de cor.
- Sliders de controle direto de brilho e velocidade com envio de comandos em tempo real.
- Botões de macros rápidas: Blackout, Cor Sólida, Strobo e Fuego.
- Tabela de Cues com exibição em compassos (Bars, ex: `17.1`).
- Função de pré-visualização física: clicar em copiar ou editar um Cue aplica imediatamente o visual daquele evento nas luminárias conectadas.

---

## 6. Testes

- **Estado:** 26 testes automatizados implementados e aprovados (100% de sucesso).
- Arquivos de teste:
  - `tests/test_protocol.py`: valida enquadramento `0xAA`, tamanhos de payload e decodificação TLV.
  - `tests/test_presets.py`: valida montagem de macros e regras de compatibilidade entre modelos.
  - `tests/test_partylight.py`: valida inicialização, conexão mock e chamadas de métodos da luminária.
  - `tests/test_faria.py`: valida persistência de Cues no SQLite, agendamento de eventos, compensação de latência, saltos na linha do tempo (seeks/rewinds) e regras de transição de master deck no playback.
- Comando de execução:
  ```powershell
  $env:PYTHONPATH="src"; python -m unittest discover tests
  ```

---

## 7. Próximos passos

1. **Debounce em faders:** Adicionar limitação de taxa (rate limiting) para evitar acúmulo de requisições BLE durante movimentações muito rápidas de faders.
2. **Leitura de bateria:** Implementar o envio de `AA 9D` e o parsing da notificação `AA 9E` para exibir a porcentagem de bateria do PartyLight Beam na interface.
3. **Modo Live:** Criar opção para desativar a simulação por relógio local (mock) quando o VirtualDJ perder conexão durante uma apresentação.
4. **Exportação de Cues:** Permitir salvar e carregar Cues de faixas em arquivos JSON portáveis.