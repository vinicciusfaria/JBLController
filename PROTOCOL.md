# JBL BLE Protocol Documentation

Status: Engenharia reversa em andamento (Arquitetura TLV decodificada).

Dispositivos-alvo:
- JBL PartyLight Stick
- JBL PartyLight Beam

UUIDs GATT conhecidos:
- Serviço: `65786365-6c70-6f69-6e74-2e636f6d0000`
  - Escrita (`write`, `write-without-response`): `65786365-6c70-6f69-6e74-2e636f6d0002`
  - Notificação (`notify`, `read`): `65786365-6c70-6f69-6e74-2e636f6d0001`
- Serviço Secundário (Google Fast Pair / Intrepid): `0000fea0-0000-1000-8000-00805f9b34fb`
  - Escrita: `0000fea1-0000-1000-8000-00805f9b34fb`
  - Notificação: `0000fea2-0000-1000-8000-00805f9b34fb`

---

## 1. Arquitetura de Enquadramento (Framing)

Todas as notificações emitidas pelo PartyLight iniciam com `0xAA` e seguem a estrutura:

```text
[0xAA] [Opcode: 1 byte] [Comprimento: 2 bytes (uint16 little-endian)] [Payload TLVs...]
```

- **Byte 0 (`0xAA`)**: Preamble / Magic Byte de sincronização.
- **Byte 1 (Opcode / MsgID)**:
  - `0x32`: Notificação de Estado de Iluminação e Efeitos.
  - `0x12`: Notificação de Identidade, Metadados e Telemetria do Dispositivo.
- **Bytes 2–3 (Payload Length)**: Tamanho em bytes dos dados que seguem o cabeçalho, codificado em Little-Endian (ex: `0x32 0x00` = 50 bytes; `0x31 0x00` = 49 bytes).
- **Bytes 4+ (Payload TLV Stream)**: Sequência contígua de blocos TLV (Tag-Length-Value):
  - `Tag`: 1 byte
  - `Length`: 1 byte (quantidade de bytes do valor)
  - `Value`: `Length` bytes

---

## 2. Pacote de Estado: `0x32` (`aa 32 32 00 ...`)

Tamanho total: 53 bytes (4 bytes de cabeçalho + 50 bytes de TLVs).

### TLVs Decodificados

| Tag (Hex) | Tamanho | Significado | Descrição / Valores Observados | Status |
|---|---|---|---|---|
| `0x31` | 1 byte | **Modo / Efeito Ativo** | `0x16`: Gravidade<br>`0x17`: Relâmpago<br>`0x18`: Falha<br>`0x09`, `0x0a`: Outros modos dinâmicos | **CONFIRMADO** |
| `0x32` | 3 bytes | **Cor Base (RGB)** | Componentes `[RR GG BB]` puros.<br>Ex: `05 00 ff` (Azul), `00 ff 2b` (Verde), `ff 00 2a` (Vermelho). | **CONFIRMADO** |
| `0x45` | 1 byte | **Brilho Geral (Master)** | Escala percentual de 0 a 100:<br>`0x00` = 0%<br>`0x40` (64 dec) ≈ 50%<br>`0x64` (100 dec) = 100% | **CONFIRMADO** |
| `0x46` | 1 byte | **Velocidade / Intensidade Dinâmica** | Controla velocidade ou intensidade do efeito dinâmico.<br>Variou para `0x47` em velocidade mínima e `0x31` em ajuste relativo. | **HIPÓTESE** |
| `0x47` | 2 bytes | Desconhecido | Observado sempre como `00 00`. | **NÃO DETERMINADO** |
| `0x36` | 1 byte | **Master Switch de Efeito** | `0x01` (ativo) / `0x00` (desativado/apagado). | **HIPÓTESE** |
| `0x4a` | 20 bytes | **Tabela de Modos Suportados** | Lista fixa de 20 IDs de modos suportados pelo firmware:<br>`08 18 16 17 02 09 0a 0b 0c 0d 19 1a 1b 10 11 12 1f 20 21 22` | **CONFIRMADO** |
| `0x48` | 1 byte | Desconhecido | Observado sempre como `0x00`. *(Correção: não é luz traseira)* | **NÃO DETERMINADO** |
| `0x49` | 1 byte | **Luz Traseira (Rear Light)** | `0x00` = Desligada<br>`0x01` = Ligada | **CONFIRMADO** |

---

## 3. Pacote de Identificação e Metadados: `0x12` (`aa 12 31 00 ...`)

Tamanho total: 52 bytes (4 bytes de cabeçalho + 49 bytes de TLVs).
Emitido em conjunto com atualizações de estado na mesma característica de notificação (`...0001`).

### TLVs Decodificados

| Tag (Hex) | Tamanho | Significado | Descrição / Valores Observados | Status |
|---|---|---|---|---|
| `0x31` | 2 bytes | **Model ID** | `21 09` (Identificador de hardware JBL PartyLight Stick). | **HIPÓTESE** |
| `0x32` | 1 byte | Desconhecido | `0x01`. | **NÃO DETERMINADO** |
| `0x37` | 6 bytes | **Endereço MAC** | Endereço MAC Bluetooth físico (ex: `08 79 ff 1e 98 19`). | **CONFIRMADO** |
| `0x3c` | 1 byte | Desconhecido | `0x00`. | **NÃO DETERMINADO** |
| `0x40` | 16 bytes | **Número de Série (ASCII)** | Serial Number legível (ex: `RT0065-BP0109332`, `RT0065-BP0112028`). | **CONFIRMADO** |
| `0x41` | 3 bytes | **Versão de Firmware** | `00 05 03` (Firmware v0.5.3). | **CONFIRMADO** |
| `0x45` | 1 byte | **Detecção de Som** | `0x00` = Desligada<br>`0x01` = Ligada | **CONFIRMADO** |
| `0x4a` | 2 bytes | Desconhecido | `00 00`. | **NÃO DETERMINADO** |

---

## 4. O que sabemos sobre o Protocolo de Escrita (Write)

1. **Falha do Envio Cru:**
   O envio isolado de `45 01 XX` (3 bytes soltos) para a característica `...0002` não é interpretado pelo dispositivo porque ele exige o enquadramento completo com `0xAA` e cabeçalho de comprimento.
2. **Hipótese de Enquadramento de Escrita:**
   O pacote de escrita deve seguir a mesma sintaxe:
   `[0xAA] [CMD_OPCODE] [LEN_L] [LEN_H] [TLVs...]`
   Podendo ser uma escrita de estado completa (`Opcode 0x32`) ou escritas parciais de comando dedicado (ex: `Opcode 0x01` ou `0x31`).
3. **Próxima validação:**
   A captura de Bluetooth HCI Snoop (Android + JBL ONE) fornecerá o valor exato do Opcode de escrita e se há necessidade de checksum.
