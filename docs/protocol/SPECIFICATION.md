# Especificação Técnica do Protocolo BLE - JBL PartyLight

Especificação consolidada da camada de transporte e enquadramento de dados dos dispositivos JBL PartyLight Stick e JBL PartyLight Beam, derivada de capturas de tráfego BLE, descompilação de código do aplicativo JBL One e testes físicos controlados.

---

## 1. Transporte BLE

- **Serviço Principal:** `65786365-6c70-6f69-6e74-2e636f6d0000`
- **Característica de Escrita (Comandos):** `65786365-6c70-6f69-6e74-2e636f6d0002`
  - Tipo de escrita: `Write Without Response` (GATT Write Command, Opcode ATT `0x52`).
  - Handles observados: `0x0080` / `0x8003`.
- **Característica de Notificação (Estado):** `65786365-6c70-6f69-6e74-2e636f6d0001`
  - Tipo de leitura: `Notify` (com subscrição no descritor CCCD).
  - Handles observados: `0x8006`.
- **Fluxo de comunicação:**
  - O controlador envia configurações visuais ou de hardware na característica de escrita via comandos sem resposta.
  - A luminária emite notificações periódicas ou em resposta a comandos na característica de notificação, informando o estado completo dos parâmetros.

---

## 2. Estrutura de Enquadramento (Framing)

Todos os pacotes trafegam como uma sequência contígua de bytes:

```text
[AA] [Command ID] [Payload Length] [00] [Field 1 ID] [Field 1 Len] [Field 1 Value...] [Field N...]
```

- **`0xAA` (1 byte):** Byte de sincronização inicial.
- **`Command ID` (1 byte):** Contexto dos dados enviados ou recebidos.
- **`Payload Length` (1 byte):** Quantidade total de bytes a partir do byte seguinte. Calculado como:
  `Payload Length = 1 (marcador 0x00) + somatório(2 + tamanho_do_valor_do_campo)`
- **`0x00` (1 byte):** Marcador fixo que precede os campos de dados.
- **Campos TLV:** Sequência contendo `Field ID` (1 byte), `Field Length` (1 byte) e `Field Value` (N bytes).

O protocolo permite concatenar múltiplos campos TLV no mesmo pacote.

---

## 3. Identificadores de Comando (Command IDs)

| Command ID | Nome no APK | Tipo | Finalidade |
|---|---|---|---|
| `0x33` | `ReqSetLightInfo` | Escrita | Configura parâmetros de iluminação (brilho, cor, modo, velocidade). |
| `0x32` | `PLLightInfo` | Notificação | Notifica estado atual da iluminação e modos suportados. |
| `0x31` | `ReqLightInfo` | Escrita | Polling: envia `AA 31 00` para solicitar emissão imediata de `AA 32`. |
| `0x13` | `ReqSetDevInfo` | Escrita | Configura parâmetros de hardware (detecção de som). |
| `0x12` | *(Device Info)* | Notificação | Notifica metadados de hardware (endereço MAC, versão de firmware, número de série). |
| `0x11` | `ReqDevInfo` | Escrita | Polling: envia `AA 11 00` para solicitar emissão imediata de `AA 12`. |
| `0x9D` | `ReqBatteryStatus` | Escrita | Solicita o nível de carga de bateria (PartyLight Beam). |
| `0x9E` | *(Battery Info)* | Notificação | Retorna o status de carga da bateria. |

---

## 4. Campos de Iluminação (`AA 33` e `AA 32`)

| Field ID | Nome no APK | Tamanho | Valores / Faixa | Suporte Stick | Suporte Beam | Status |
|---|---|---|---|:---:|:---:|---|
| `0x31` | `Pattern` | 1 byte | `0x00` a `0x22` (ver tabela de modos). | Sim | Subconjunto | Confirmado em ambos |
| `0x32` | `Color` | 3 bytes | `[RR, GG, BB]` em hexadecimal. | Sim | Sim | Confirmado em ambos |
| `0x36` | `PatternLooping` | 1 byte | `0x00` = Color Loop, `0x01` = Static Color. | Sim | Não | Confirmado no Stick |
| `0x45` | `lightBrightness`| 1 byte | `0x00` (0%) a `0x64` (100%). | Sim | Sim | Confirmado em ambos |
| `0x46` | `lEDMovementSpeed`| 1 byte | `0x00` a `0x64`. | Sim | Não testado f. | Confirmado no Stick |
| `0x49` | `backLightMode` | 1 byte | `0x00` = OFF, `0x01` = ON. | Sim | Não possui | Confirmado no Stick |
| `0x47` | `speakerIDtoLight`| 2 bytes | 2 bytes em hexadecimal. | - | - | Hipótese (posicionamento de palco) |
| `0x48` | `stageLightNum` | 1 byte | Inteiro indicando total de luminárias. | Somente leitura | Somente leitura | Observado no APK |
| `0x4A` | `supportPatterns`| N bytes | Array de IDs de modos suportados. | Somente leitura | Somente leitura | Confirmado em ambos |

---

## 5. Campos de Hardware (`AA 13` e `AA 12`)

| Field ID | Nome no APK | Tamanho | Valores / Faixa | Finalidade | Status |
|---|---|---|---|---|---|
| `0x45` | `soundDetection` | 1 byte | `0x00` = OFF, `0x01` = ON. | Habilita reação ao som via microfone interno. | Confirmado no Stick |
| `0x46` | `danceMode` | 1 byte | `0x00` = OFF, `0x01` = ON. | Modo de dança documentado no APK. | Hipótese (efeito prático não determinado) |
| `0x3C` | `AuracastMode` | 1 byte | Não testado. | Gestão de broadcast LE Audio com PartyBoxes. | Hipótese |

---

## 6. Diferenças arquiteturais entre Stick e Beam

1. **PartyLight Stick:**
   - Arranjo vertical de LEDs com resolução espacial em 360 graus.
   - Possui LED traseiro dedicado de luz branca (`0x49`).
   - Suporta modo de cor fixa uniforme (`0x15` com `0x36 = 0x01`).
   - Suporta efeitos com gradiente e transição vertical (`CAMPFIRE`, `GRAVITY`, `LIGHTNING`).
2. **PartyLight Beam:**
   - Projetor óptico motorizado voltado para reflexão em superfícies.
   - Não possui LED traseiro.
   - Divulga apenas 7 modos no array `0x4A` e ignora o modo estático `0x15`. Comandos de cor devem ser combinados com modos dinâmicos como `NEON` (`0x02`), `LOOP` (`0x09`) ou `BOUNCE` (`0x0A`).
   - Possui bateria interna e suporta requisição de carga via `AA 9D`.

---

## 7. Exemplos de Enquadramento

- **Brilho para 50% (`0x40`):**
  `AA 33 04 00 45 01 40`

- **Cor Vermelha pura (`FF 00 00`):**
  `AA 33 06 00 32 03 FF 00 00`

- **Luz traseira ligada:**
  `AA 33 04 00 49 01 01`

- **Comando Composto (Cor sólida Vermelha no Stick):**
  `AA 33 0C 00 31 01 15 32 03 FF 00 00 36 01 01`

- **Detecção de som desligada:**
  `AA 13 04 00 45 01 00`
