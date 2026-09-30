# Protocolo BLE - JBL PartyLight (Stick & Beam)

Documentação técnica do protocolo Bluetooth Low Energy (BLE) utilizado pelas luminárias **JBL PartyLight Stick** e **JBL PartyLight Beam**.

As informações deste documento foram obtidas por meio de:
1. Inspeção de serviços e características GATT via Bleak (`captures/gatt_inspection_20260920_140847.txt`).
2. Captura e análise de notificações passivas (`captures/ble_probe_*.txt`).
3. Análise do log HCI Snoop (`btsnoop_hci.log`) gerado com o aplicativo oficial JBL One.
4. Descompilação das classes de comunicação do aplicativo JBL One Android (`com.harman.command.partylight`).
5. Testes controlados de escrita física (`captures/lab_results_*.txt` e `captures/lab_beam_*.txt`).

---

## 1. Transporte GATT

### Características principais

- **Serviço Principal:** `65786365-6c70-6f69-6e74-2e636f6d0000`
- **Escrita (Comandos):** `65786365-6c70-6f69-6e74-2e636f6d0002`
  - Operação: `Write Without Response` (ATT Write Command, Opcode `0x52`).
  - Handles observados: `0x0080` / `0x8003` (depende da controladora do host).
- **Notificação (Telemetria e Estado):** `65786365-6c70-6f69-6e74-2e636f6d0001`
  - Operação: `Notify` (com subscrição via CCCD).
  - Handles observados: `0x8006`.

### Serviço secundário (Fast Pair / Identificação)
- Serviço: `0000fea0-0000-1000-8000-00805f9b34fb`
- Escrita: `0000fea1-0000-1000-8000-00805f9b34fb`
- Notificação: `0000fea2-0000-1000-8000-00805f9b34fb`

---

## 2. Estrutura de Enquadramento (Framing)

Todas as transmissões (tanto comandos enviados quanto notificações recebidas) utilizam a seguinte estrutura de empacotamento contíguo:

```text
[AA] [Command ID] [Payload Length] [00] [Field 1 ID] [Field 1 Len] [Field 1 Value...] [Field N...]
```

| Campo | Tamanho | Descrição |
|---|---|---|
| `Header Identifier` | 1 byte | Byte mágico fixo: `0xAA`. |
| `Command ID` | 1 byte | Identifica a categoria do pacote (Luz, Hardware, Bateria, etc.). |
| `Payload Length` | 1 byte | Comprimento em bytes a partir do próximo byte inclusive. Calculado como: `1 (marcador 0x00) + somatório(2 + tam_valor) de cada TLV`. |
| `Payload Start Byte`| 1 byte | Marcador de início de payload: fixo `0x00`. |
| `Field ID` (Tag) | 1 byte | Identificador da propriedade. O significado depende do `Command ID`. |
| `Field Length` | 1 byte | Tamanho em bytes do valor do campo. |
| `Field Value` | N bytes | Dados da propriedade. |

O protocolo aceita encadeamento de múltiplos campos TLV no mesmo pacote.

---

## 3. Identificadores de Comando (Command IDs)

| Command ID | Nome no APK | Tipo | Finalidade | Origem da evidência |
|---|---|---|---|---|
| `0x33` | `ReqSetLightInfo` | Escrita | Define configurações visuais (cor, brilho, modo, velocidade). | Confirmado por testes físicos (`lab_results_AA33_*.txt`). |
| `0x32` | `PLLightInfo` | Notificação | Estado atual de iluminação e modos suportados emitido pela caixa. | Observado em capturas BLE (`ble_probe_*.txt`). |
| `0x31` | `ReqLightInfo` | Escrita | Polling: envia `AA 31 00` para solicitar que a caixa responda com `AA 32`. | Confirmado pelo APK e testes físicos. |
| `0x13` | `ReqSetDevInfo` | Escrita | Define configurações de hardware (microfone, detecção de som). | Confirmado pelo APK e testes físicos no Stick. |
| `0x12` | *(Device Info)* | Notificação | Metadados do hardware (MAC, firmware, número de série). | Observado em capturas BLE. |
| `0x11` | `ReqDevInfo` | Escrita | Polling: envia `AA 11 00` para forçar envio de `AA 12`. | Confirmado pelo APK. |
| `0x9D` | `ReqBatteryStatus` | Escrita | Solicita estado de bateria (utilizado na PartyLight Beam). | Identificado no APK. |
| `0x9E` | *(Battery Info)* | Notificação | Nível de bateria retornado pelo dispositivo. | Identificado no APK. |

---

## 4. Dicionário de Campos de Iluminação (`AA 33` e `AA 32`)

### Confirmado em hardware

| Field ID | Nome no APK | Tamanho | Valores / Significado | Detalhes da validação |
|---|---|---|---|---|
| `0x31` | `Pattern` | 1 byte | ID do efeito ativo (`0x00` a `0x22`). | Confirmado no Stick e no Beam. O Beam rejeita modos lineares exclusivos de torre. |
| `0x32` | `Color` | 3 bytes | Cor RGB em formato `[RR, GG, BB]`. | Confirmado no Stick e no Beam. Ex: `FF 00 00` (Vermelho), `00 00 FF` (Azul). |
| `0x36` | `PatternLooping` | 1 byte | Transição de cor: `0x00` = Color Loop, `0x01` = Static Color. | Confirmado no Stick em conjunto com `Pattern = 0x15`. Ignorado pelo Beam. |
| `0x45` | `lightBrightness` | 1 byte | Brilho geral: `0x00` (0%) a `0x64` (100%). | Confirmado por teste físico no Stick e no Beam (`lab_results_20260920_171420.txt`). |
| `0x46` | `lEDMovementSpeed` | 1 byte | Velocidade de animação: `0x00` a `0x64`. | Confirmado por teste físico no Stick. |
| `0x49` | `backLightMode` | 1 byte | Luz traseira do Stick: `0x00` = OFF, `0x01` = ON. | Confirmado fisicamente no Stick. O Beam não possui o LED traseiro. |
| `0x4A` | `supportPatterns` | N bytes | Lista de modos suportados (somente leitura, em `AA 32`). | Observado em `ble_probe_*.txt` e validado contra array de enum do APK. |

### Hipótese

| Field ID | Nome no APK | Tamanho | Valores / Significado | Detalhes |
|---|---|---|---|---|
| `0x47` | `speakerIDtoLight` | 2 bytes | 2 bytes em hexadecimal. | Presente na classe do APK. Hipótese de ser usado para posicionamento espacial no palco. |
| `0x48` | `stageLightNum` | 1 byte | Contador inteiro presente apenas no `AA 32`. | Presente no APK. Hipótese de informar quantidade de luzes associadas ao grupo. |

---

## 5. Dicionário de Campos de Hardware (`AA 13` e `AA 12`)

### Confirmado em hardware

| Field ID | Nome no APK | Tamanho | Valores / Significado | Detalhes da validação |
|---|---|---|---|---|
| `0x45` | `soundDetection` | 1 byte | Reação ao som via microfone interno: `0x00` = OFF, `0x01` = ON. | Confirmado por teste controlado com `AA 13 04 00 45 01 01`. |

### Observado em notificações (`AA 12`)

| Field ID | Tamanho | Significado | Exemplo observado |
|---|---|---|---|
| `0x37` | 6 bytes | Endereço MAC Bluetooth do hardware. | `08 79 ff 1e 98 19` |
| `0x40` | 16 bytes | Número de série em ASCII legível. | `RT0065-BP0109332` |
| `0x41` | 3 bytes | Versão de firmware embarcado. | `00 05 03` (v0.5.3) |

### Hipótese / Pendente de validação

| Field ID | Nome no APK | Tamanho | Valores / Significado | Detalhes |
|---|---|---|---|---|
| `0x46` | `danceMode` | 1 byte | Booleano (`0x00` / `0x01`). | Mapeado no APK. Efeito prático no comportamento do microfone ainda não determinado. |
| `0x3C` | `AuracastMode` | 1 byte | Desconhecido. | Mapeado no APK para gestão de broadcast LE Audio com PartyBoxes. |

---

## 6. Modos de Efeito (`Pattern` / `0x31`)

Mapeamento cruzado entre a enumeração do APK, a tabela divulgada no campo `0x4A` e o comportamento observado fisicamente:

| ID (Hex) | Nome no APK | Suporte Stick | Suporte Beam | Comportamento observado no hardware |
|---|---|:---:|:---:|---|
| `0x02` | NEON | Sim | Sim | Transição contínua e suave de cores. |
| `0x09` | LOOP | Sim | Sim | Movimento cíclico de luz (chaser). |
| `0x0A` | BOUNCE | Sim | Sim | Pulso de luz que rebate nas extremidades. |
| `0x0B` | TRIM | Sim | Sim | Preenchimento estilo medidor VU. |
| `0x0C` | SWITCH | Sim | Sim | Troca rápida de blocos de cor sem fade. |
| `0x0D` | FREEZE | Sim | Sim | Luz estática na cor atual sem movimento. |
| `0x15` | STATIC | Sim | Não | Cor sólida e uniforme em todo o bastão. Requer `PatternLooping = 0x01`. O Beam ignora este modo. |
| `0x16` | GRAVITY | Sim | Não | Gotas ou blocos caindo verticalmente pelo bastão. O Beam ignora. |
| `0x17` | LIGHTNING | Sim | Não | Flashes estroboscópicos simulando raios. O Beam ignora. |
| `0x18` | GLITCH | Sim | Não | Padrão caótico com artefatos visuais. O Beam ignora. |
| `0x19` | CAMPFIRE | Sim | Não | Simulação de chamas oscilando a partir da base. O Beam ignora. |
| `0x10` | OCEAN | Sim | Não | Ondulações lentas em tons de azul. |
| `0x11` | AURORA | Sim | Não | Gradiente lento simulando aurora boreal. |
| `0x12` | BLOSSOM | Sim | Não | Expansão suave a partir do centro. |
| `0x1A` | UNIVERSE | Sim | Não | Pontos brilhantes intermitentes sobre fundo escuro. |
| `0x1B` | FIREFLY | Sim | Não | Pontos isolados pulsando aleatoriamente. |
| `0x1F` | BEER | Sim | Não | Bolhas subindo da base simulando efervescência. |
| `0x20` | STORM | Sim | Não | Base escura com relâmpagos intermitentes. |
| `0x21` | HOVER | Sim | Não | Blocos de luz oscilando com inércia. |
| `0x22` | SKY | Sim | Não | Transição de tons do céu. |

*Nota:* O array `0x4A` retornado pelo Beam informa apenas 7 modos válidos. Enviar modos fora dessa lista faz com que o Beam mantenha o modo anterior ou aplique um fallback interno.

---

## 7. Exemplos de Pacotes (Hexadecimal)

Comandos montados conforme a regra de framing `[AA] [CMD] [LEN] 00 [TLVs...]`:

- **Definir brilho para 50% (`0x40`):**
  `AA 33 04 00 45 01 40`
  *(Len = 1 byte marcador + 3 bytes do TLV 0x45 = 4)*

- **Definir cor para Azul puro (`00 00 FF`):**
  `AA 33 06 00 32 03 00 00 FF`
  *(Len = 1 + 5 = 6)*

- **Luz traseira do Stick ligada:**
  `AA 33 04 00 49 01 01`

- **Luz traseira do Stick desligada:**
  `AA 33 04 00 49 01 00`

- **Detecção de som ligada (`AA 13`):**
  `AA 13 04 00 45 01 01`

- **Cor sólida fixa no Stick (Comando composto: STATIC + Vermelho + StaticLoop):**
  `AA 33 0C 00 31 01 15 32 03 FF 00 00 36 01 01`
  *(Len = 1 + 3 + 5 + 3 = 12 = 0x0C)*

---

## 8. Comandos Críticos Não Testados

Os seguintes comandos foram identificados na engenharia reversa do APK da JBL, mas **não devem ser disparados** em laboratório sem instrumentação apropriada:

- `0x25` (`ReqDfuStartCommand`)
- `0x26` (`ReqDfuSetDataCommand`)
- `0x28` (`ReqDfuCancelCommand`)
- `0x2A` (`ReqDfuApplyCommand`)

Estes são procedimentos de atualização de firmware (OTA). O envio de dados corrompidos ou incompletos pode travar permanentemente a memória flash dos dispositivos.
