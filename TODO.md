# TODO - JBLController

## Protocolo & Engenharia Reversa
- [x] Decodificar estrutura de enquadramento (Framing com `0xAA` + Opcode + Comprimento LE).
- [x] Mapear arquitetura TLV das notificações.
- [x] Mapear pacote de estado `0x32` (Modos, RGB, Brilho, Tabela de capacidades, Luz traseira).
- [x] Mapear pacote de identificação `0x12` (MAC, Serial Number, Firmware, Detecção de som).
- [ ] Obter log de Bluetooth HCI Snoop via Android + JBL ONE.
- [ ] Analisar pacotes `ATT Write` no HCI Snoop para determinar Opcode de escrita e checagem de integridade (se houver).
- [ ] Validar controle bidirecional no JBL PartyLight Stick (escrita -> confirmação por notificação).
- [ ] Realizar captura de dados do JBL PartyLight Beam e verificar compatibilidade.

## Ferramentas & Análise
- [x] Criar analisador automático de capturas (`tools/ble_capture_analyzer.py`).
- [ ] Atualizar `tools/ble_capture_analyzer.py` para parsear nativamente os TLVs de `0x32` e `0x12`.
- [ ] Atualizar `tools/ble_probe.py` para separar notificações por tipo de pacote e evitar sobreposição de `0x32` com `0x12`.
- [ ] Atualizar `tools/ble_control.py` com as novas hipóteses de framing (`0xAA` + Opcode + TLV).

## Implementação (`src/`)
- [ ] Criar módulo de pacotes/protocolo (`src/protocol/packet.py` e `src/protocol/tlv.py`).
- [ ] Implementar cliente de conexão BLE assíncrono para o Stick (`src/device/stick.py`).
- [ ] Implementar controle de alto nível (set_brightness, set_color, set_mode, set_rear_light).
- [ ] Desenvolver interface virtual de automação / receptor MIDI.
