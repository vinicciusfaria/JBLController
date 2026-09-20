# Estado Atual do Projeto: JBLController

Data da última atualização: 2026-09-20

## 1. Visão Geral
O JBLController é um projeto focado na engenharia reversa do protocolo Bluetooth Low Energy (BLE) dos dispositivos **JBL PartyLight Stick** e **JBL PartyLight Beam**, com o objetivo de construir uma biblioteca Python e um controlador virtual capaz de automatizar as luzes (incluindo futura sincronização com áudio e MIDI).

## 2. Status da Engenharia Reversa
- **Descoberta da Arquitetura do Protocolo:**
  - Foi descoberta e confirmada a arquitetura **TLV (Type-Length-Value)** com frames iniciados em `0xAA` e cabeçalho de comprimento little-endian de 16 bits.
  - O fluxo de notificações do dispositivo foi integralmente mapeado em dois pacotes fundamentais:
    - `0x32`: Pacote de Estado de Iluminação (Modo, Cor RGB, Brilho, Velocidade, Tabela de Modos, Luz Traseira).
    - `0x12`: Pacote de Identificação (MAC físico, Serial Number ASCII, Firmware Version, Detecção de Som).
- **Protocolo de Escrita:**
  - Identificada a causa da falha dos primeiros testes de escrita: o envio de TLVs avulsas sem o frame `0xAA` + cabeçalho de comprimento é descartado pelo firmware.
  - Próximo passo definido: captura de HCI Snoop no Android para obter a sintaxe definitiva de pacotes de escrita.

## 3. Estado das Ferramentas (`tools/`)
- `tools/ble_scan.py`: Funcional para varredura de dispositivos no ambiente.
- `tools/ble_inspect.py`: Funcional para inspeção detalhada de serviços e características GATT.
- `tools/ble_probe.py`: Funcional para captura passiva de notificações com anotação de eventos.
- `tools/ble_capture_analyzer.py`: Analisador automático de capturas (em aprimoramento para decodificação TLV nativa).
- `tools/ble_control.py`: Script inicial de controle ativo (precisa ser atualizado para o novo formato de frame).

## 4. Próximos Marcos
1. Aprimorar o `ble_capture_analyzer.py` para extrair e exibir os nomes dos TLVs decodificados.
2. Obter captura de Bluetooth HCI Snoop (Android + JBL ONE).
3. Implementar a primeira escrita funcional com enquadramento correto e testar controle de brilho e luz traseira.
4. Mapear o JBL PartyLight Beam (verificar paridade com o Stick).
5. Estruturar a biblioteca base em `src/`.
