# Protocolo BLE Confirmado - Família JBL PartyLight

Este documento contém a arquitetura de comunicação oficial extraída diretamente da engenharia reversa do código-fonte Android do aplicativo "JBL One" (`com.harman.command.partylight`). Ele consolida todas as nossas observações físicas, logs do HCI e a verificação no código Java descompilado.

## 1. Características do Dispositivo

- **UUID de Escrita (Command):** `65786365-6c70-6f69-6e74-2e636f6d0002` (Handle `0x0080` / `0x8003`)
- **UUID de Notificação (Status):** `65786365-6c70-6f69-6e74-2e636f6d0001`
- **Transporte GATT:** ATT Write Command (Opcode `0x52`, sem resposta/`response=False`).

## 2. Framing (Estrutura do Pacote GATT)

Todos os comandos de GATT da JBL seguem este empacotamento base, definido na classe Java `GeneralGattCommand`.

| Identifier | Command ID | Payload Len | Byte 00 | Field ID | Field Len | Field Value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AA` | `XX` | `XX` | `00` | `XX` | `XX` | `...` |
| Fixo (1 byte) | (1 byte) | (1 byte) | Fixo (1 byte) | (1 byte) | (1 byte) | (N bytes) |

**Cálculo do Payload Length:**
O tamanho exato do "Payload" inclui o Byte `00` mais todos os blocos de campos que vierem depois dele.
*Exemplo prático:* `AA 33 04 00 45 01 64`
- `AA` = Identifier
- `33` = Command ID (ReqSetLightInfo)
- `04` = Payload Length (4 bytes a seguir)
- `00` = Byte de início de Payload
- `45` = Field ID (Brightness)
- `01` = Field Length (1 byte de valor a seguir)
- `64` = Field Value (100%)

---

## 3. Headers (Command IDs Principais)

A maior virada de chave do protocolo é que **os Field IDs mudam de significado dependendo do Command ID (Header)**.

| Command ID | Classe Java | Descrição |
|---|---|---|
| **`AA 33`** | `ReqSetLightInfo` | Envio de configurações visuais (Cor, Brilho, Modo). |
| **`AA 13`** | `ReqSetDevInfo` | Envio de configurações de hardware (Som, Auracast). |
| **`AA 32`** | `PLLightInfo` | Notificação que a caixa envia de volta ao App contendo os estados atuais. |
| **`AA 31`** | `ReqLightInfo` | Comando de Polling vazio (`AA 31 00`) que força o dispositivo a responder com um `AA 32`. |
| **`AA 11`** | `ReqDevInfo` | Comando de Polling vazio (`AA 11 00`) que força resposta de infos de hardware (`AA 12`). |
| **`AA 9D`** | `ReqBatteryStatus`| Requisita status da bateria (usado na PartyLight Beam). A resposta volta em `AA 9E`. |

---

## 4. Dicionário de Campos (Field IDs)

### 4.1. Sob o Header de Luz: `AA 33` (Comando) e `AA 32` (Status)

| Field ID | Nome Java | Significado Físico | Tamanho do Valor | Formato/Exemplos |
|---|---|---|---|---|
| **`0x31`** | `Pattern` | Modo de Efeito | 1 byte | Enum de 0x00 a 0x22 (ver tabela de modos abaixo). |
| **`0x32`** | `Color` | Cor Base | 3 bytes | Valores RGB Hex (ex: `FF 00 00` para Vermelho). |
| **`0x36`** | `PatternLooping`| Transição de Cor | 1 byte | `00` = COLOR_LOOP (Troca Cores)<br>`01` = STATIC_COLOR (Cor Fixa) |
| **`0x45`** | `lightBrightness`| Brilho | 1 byte | `00` = 0% a `64` = 100%. |
| **`0x46`** | `lEDMovementSpeed`| Velocidade | 1 byte | `00` = 0% a `64` = 100%. |
| **`0x47`** | `speakerIDtoLight`| Identificação | 2 bytes | Parsing de Hex string. Usado possivelmente p/ agrupamento. |
| **`0x48`** | `stageLightNum` | Contagem de luzes| 1 byte | *Somente Leitura* (Apenas no `AA 32`). Indica qts no palco. |
| **`0x49`** | `backLightMode` | **Luz Traseira** | 1 byte | `00` = OFF<br>`01` = ON |
| **`0x4A`** | `supportPatterns`| Modos Suportados | N bytes | *Somente Leitura* (Apenas no `AA 32`). Array de Patterns suportados pela caixa específica (Stick ou Beam). |

---

### 4.2. Sob o Header de Hardware: `AA 13` (Comando) e `AA 12` (Status)

| Field ID | Nome Java | Significado Físico | Tamanho do Valor | Formato/Exemplos |
|---|---|---|---|---|
| **`0x3C`** | `AuracastMode` | Modo de Broadcast| 1 byte | Desconhecido/Em Análise |
| **`0x45`** | `soundDetection` | **Reação ao Som** | 1 byte | `00` = OFF<br>`01` = ON |
| **`0x46`** | `danceMode` | Modo Dança (?) | 1 byte | `00` = OFF<br>`01` = ON |

*(Note como o `0x45` e o `0x46` no hardware têm função de chaves lógicas, diferentemente do controle de intensidade que fazem na aba de luz).*

---

## 5. Tabela Universal de Modos (Patterns - `0x31`)

Estes são todos os 30 efeitos mapeados nativamente no enumerador `Pattern` de `PLLightInfo.java`. Através do campo `0x4A`, o hardware informa ao app quais destes ele consegue reproduzir.

| Hex | Dec | Nome Oficial no Código (Efeito) |
| :--- | :--- | :--- |
| `00` | 0 | **OFF** (Apagado) |
| `01` | 1 | **ROCK** |
| `02` | 2 | **NEON** |
| `03` | 3 | **CLUB** |
| `04` | 4 | **FLOW** |
| `05` | 5 | **RIPPLE** |
| `06` | 6 | **CROSS** |
| `07` | 7 | **FLASH** |
| `08` | 8 | **CUSTOM_RANDOM** |
| `09` | 9 | **LOOP** |
| `0A` | 10 | **BOUNCE** |
| `0B` | 11 | **TRIM** |
| `0C` | 12 | **SWITCH** |
| `0D` | 13 | **FREEZE** |
| `10` | 16 | **OCEAN** (Especial Beam?) |
| `11` | 17 | **AURORA** (Especial Beam?) |
| `12` | 18 | **BLOSSOM** |
| `13` | 19 | **SUNRISE** |
| `14` | 20 | **FIREPLACE** |
| `15` | 21 | **STATIC** (Cor Fixa) |
| `16` | 22 | **GRAVITY** |
| `17` | 23 | **LIGHTNING** |
| `18` | 24 | **GLITCH** |
| `19` | 25 | **CAMPFIRE** |
| `1A` | 26 | **UNIVERSE** (Especial Beam?) |
| `1B` | 27 | **FIREFLY** |
| `1F` | 31 | **BEER** |
| `20` | 32 | **STORM** |
| `21` | 33 | **HOVER** |
| `22` | 34 | **SKY** (Especial Beam?) |

*Para enviar uma cor fixa, o protocolo correto é: Enviar Pattern `0x15` (STATIC), enviar a Cor (`0x32`), e configurar o PatternLooping (`0x36`) para `0x01` (STATIC_COLOR).*
