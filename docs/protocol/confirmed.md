# Protocolo BLE Confirmado - Família JBL PartyLight

Consolidação dos dados de protocolo confirmados experimentalmente em testes com hardware físico e validados contra a descompilação do aplicativo oficial JBL One (`com.harman.command.partylight`).

---

## 1. Características GATT

- **UUID de Escrita:** `65786365-6c70-6f69-6e74-2e636f6d0002` (Handle `0x8003` / `0x0080`)
  - Transporte: ATT Write Command (Opcode `0x52`, sem resposta / `response=False`).
- **UUID de Notificação:** `65786365-6c70-6f69-6e74-2e636f6d0001` (Handle `0x8006`)
  - Transporte: GATT Notify.

---

## 2. Estrutura de Enquadramento

A estrutura base de pacotes segue o padrão da classe Java `GeneralGattCommand`:

| Campo | Tamanho | Valor / Descrição |
|---|---|---|
| Identificador | 1 byte | Fixo: `0xAA` |
| Command ID | 1 byte | Categoria do comando |
| Payload Length | 1 byte | Comprimento dos dados a partir do próximo byte |
| Início de Payload | 1 byte | Fixo: `0x00` |
| Field ID | 1 byte | Código da propriedade |
| Field Length | 1 byte | Tamanho do valor |
| Field Value | N bytes | Dados da propriedade |

**Exemplo:** `AA 33 04 00 45 01 64`
- `AA`: Identificador
- `33`: Command ID (`ReqSetLightInfo`)
- `04`: Payload Length (4 bytes a seguir)
- `00`: Início de payload
- `45`: Field ID (Brilho)
- `01`: Field Length (1 byte)
- `64`: Field Value (100% em hexadecimal)

---

## 3. Command IDs Principais

O significado dos Field IDs varia conforme o Command ID de contexto:

| Command ID | Classe Java | Descrição |
|---|---|---|
| `0x33` | `ReqSetLightInfo` | Envio de comandos de iluminação (brilho, cor, modo, velocidade). |
| `0x13` | `ReqSetDevInfo` | Envio de configurações de hardware (microfone / detecção de som). |
| `0x32` | `PLLightInfo` | Notificação com o estado atual de iluminação e modos suportados. |
| `0x12` | *(Device Info)* | Notificação com metadados do hardware (MAC, serial, firmware). |
| `0x31` | `ReqLightInfo` | Polling vazio (`AA 31 00`) para solicitar envio de `AA 32`. |
| `0x11` | `ReqDevInfo` | Polling vazio (`AA 11 00`) para solicitar envio de `AA 12`. |
| `0x9D` | `ReqBatteryStatus` | Solicita estado da bateria (PartyLight Beam). |
| `0x9E` | *(Battery Info)* | Notificação com o nível de carga da bateria. |

---

## 4. Dicionário de Campos Confirmados

### 4.1. Configurações de iluminação (`AA 33` / `AA 32`)

| Field ID | Nome Java | Tamanho | Valores / Significado | Validação |
|---|---|---|---|---|
| `0x31` | `Pattern` | 1 byte | ID do efeito (`0x00` a `0x22`). | Testado no Stick e no Beam. |
| `0x32` | `Color` | 3 bytes | Cor RGB (`[RR, GG, BB]`). | Testado no Stick e no Beam. |
| `0x36` | `PatternLooping` | 1 byte | `0x00` = COLOR_LOOP, `0x01` = STATIC_COLOR. | Testado no Stick com modo `0x15`. |
| `0x45` | `lightBrightness` | 1 byte | `0x00` (0%) a `0x64` (100%). | Testado no Stick e no Beam. |
| `0x46` | `lEDMovementSpeed` | 1 byte | `0x00` (0%) a `0x64` (100%). | Testado no Stick. |
| `0x49` | `backLightMode` | 1 byte | `0x00` = OFF, `0x01` = ON. | Testado no Stick. |
| `0x4A` | `supportPatterns` | N bytes | Array de IDs de efeitos suportados. | Observado em notificações `AA 32`. |

### 4.2. Configurações de hardware (`AA 13` / `AA 12`)

| Field ID | Nome Java | Tamanho | Valores / Significado | Validação |
|---|---|---|---|---|
| `0x45` | `soundDetection` | 1 byte | `0x00` = OFF, `0x01` = ON. | Testado no Stick. |
| `0x37` | `macAddress` | 6 bytes | Endereço MAC Bluetooth. | Observado em notificações `AA 12`. |
| `0x40` | `serialNumber` | 16 bytes | Número de série em ASCII. | Observado em notificações `AA 12`. |
| `0x41` | `firmwareVersion` | 3 bytes | Versão do firmware (ex: `00 05 03` = v0.5.3). | Observado em notificações `AA 12`. |

---

## 5. Modos de Efeito (Patterns)

Para enviar uma cor fixa uniforme no PartyLight Stick:
- `Pattern` (`0x31`) = `0x15` (`STATIC`)
- `Color` (`0x32`) = componentes RGB
- `PatternLooping` (`0x36`) = `0x01` (`STATIC_COLOR`)

O PartyLight Beam não suporta o modo `0x15`; para alterar a cor do Beam, deve-se selecionar um dos modos dinâmicos compatíveis (como `NEON` `0x02` ou `LOOP` `0x09`) junto ao comando de cor RGB.
