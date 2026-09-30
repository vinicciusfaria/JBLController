# Protocolo BLE - JBL PartyLight (Stick & Beam)

Documentação de engenharia reversa do protocolo Bluetooth Low Energy (BLE) utilizado pelas luminárias **JBL PartyLight Stick** e **JBL PartyLight Beam**.

---

## 1. Origem das Evidências

As conclusões documentadas neste arquivo baseiam-se em cinco fontes:
1. **Inspeção GATT:** Descoberta de serviços e características via Bleak (`captures/gatt_inspection_20260920_140847.txt`).
2. **Capturas passivas de notificações:** Coleta de pacotes emitidos espontaneamente pelos dispositivos durante uso com o aplicativo oficial (`captures/ble_probe_*.txt`).
3. **Análise de HCI Snoop:** Inspeção de pacotes ATT capturados no Android com o app JBL One (`docs/btsnoop_hci.log` e `docs/parsed_snoop.txt`).
4. **Descompilação de código:** Análise estática das classes Java do aplicativo JBL One (`com.harman.command.partylight`, em `docs/apk_real_results.txt`).
5. **Testes físicos controlados:** Envio direcionado de pacotes gerados em Python com validação do comportamento visual no hardware (`captures/lab_results_*.txt` e `captures/lab_beam_*.txt`).

---

## 2. Transporte GATT

### Confirmado

- **Serviço Principal:** `65786365-6c70-6f69-6e74-2e636f6d0000`
- **Característica de Escrita (Comandos):** `65786365-6c70-6f69-6e74-2e636f6d0002`
  - Tipo de operação: ATT Write Command (Opcode `0x52`, Write Without Response, sem confirmação).
  - Handles observados: `0x8003` / `0x0080` (conforme o driver da controladora do host).
  - Origem: Inspeção GATT e log HCI Snoop.
- **Característica de Notificação (Estado):** `65786365-6c70-6f69-6e74-2e636f6d0001`
  - Tipo de operação: GATT Notify (com subscrição no descritor CCCD).
  - Handle observado: `0x8006`.
  - Origem: Inspeção GATT e capturas passivas.

### Observado (Serviço secundário Fast Pair)
- Serviço: `0000fea0-0000-1000-8000-00805f9b34fb`
- Característica de escrita: `0000fea1-0000-1000-8000-00805f9b34fb`
- Característica de notificação: `0000fea2-0000-1000-8000-00805f9b34fb`
- Origem: Inspeção GATT (`captures/gatt_inspection_20260920_140847.txt`). Utilizado para o emparelhamento rápido do Google (Fast Pair). Não é utilizado para controle de iluminação.

---

## 3. Estrutura de Enquadramento (Framing)

### Confirmado

Todos os pacotes de escrita e de notificação seguem uma estrutura contígua sem delimitadores de escape:

```text
[AA] [Command ID] [Payload Length] [00] [Field ID] [Field Len] [Value...]
```

| Campo | Tamanho | Descrição |
|---|---|---|
| `Header Identifier` | 1 byte | Byte fixo `0xAA`. |
| `Command ID` | 1 byte | Categoria da mensagem. Determina como os Field IDs serão interpretados. |
| `Payload Length` | 1 byte | Total de bytes a seguir a partir do byte subsequente. Calculado como: `1 (marcador 0x00) + somatório(2 + tam_valor) de cada campo TLV`. |
| `Payload Start Byte`| 1 byte | Marcador de início fixo `0x00`. |
| `Field ID` | 1 byte | Código da propriedade a alterar ou notificar. |
| `Field Length` | 1 byte | Quantidade de bytes do valor da propriedade. |
| `Field Value` | N bytes | Conteúdo da propriedade. |

- Origem: Log HCI Snoop, descompilação de `GeneralGattCommand.java` e testes controlados.
- É permitido encadear múltiplos campos TLV após o marcador `0x00` no mesmo pacote.

---

## 4. Identificadores de Comando (Command IDs)

### Confirmado

| Command ID | Nome no APK | Direção | Finalidade | Origem da evidência |
|---|---|---|---|---|
| `0x33` | `ReqSetLightInfo` | Escrita | Altera parâmetros de iluminação (brilho, cor, modo, velocidade). | Testes físicos controlados (`lab_results_AA33_*.txt`). |
| `0x32` | `PLLightInfo` | Notificação | Emite estado atual de iluminação e modos suportados. | Capturas passivas BLE (`ble_probe_*.txt`). |
| `0x31` | `ReqLightInfo` | Escrita | Polling: envia `AA 31 00` para forçar o dispositivo a responder com `AA 32`. | Descompilação do APK e testes físicos. |
| `0x13` | `ReqSetDevInfo` | Escrita | Altera configurações de hardware (microfone / detecção de som). | Descompilação do APK e teste físico no Stick. |
| `0x12` | *(Device Info)* | Notificação | Emite dados de hardware (endereço MAC, número de série, firmware). | Capturas passivas BLE (`ble_probe_*.txt`). |
| `0x11` | `ReqDevInfo` | Escrita | Polling: envia `AA 11 00` para forçar emissão de `AA 12`. | Descompilação do APK. |

### Observado no código do APK (ainda não implementado)

| Command ID | Nome no APK | Direção | Finalidade | Origem da evidência |
|---|---|---|---|---|
| `0x9D` | `ReqBatteryStatus` | Escrita | Requisita estado da bateria (PartyLight Beam). | Descompilação do APK (`ReqBatteryStatusCommand.java`). |
| `0x9E` | *(Battery Info)* | Notificação | Nível e status de carga da bateria. | Descompilação do APK. |

---

## 5. Dicionário de Campos de Iluminação (`AA 33` e `AA 32`)

### Confirmado

| Field ID | Nome no APK | Tam. | Valores / Formato | Origem da validação |
|---|---|---|---|---|
| `0x31` | `Pattern` | 1 byte | `0x00` a `0x22` (ID do efeito do firmware). | Testes físicos no Stick e Beam (`lab_results_20260920_171420.txt`). |
| `0x32` | `Color` | 3 bytes | `[RR, GG, BB]` em hexadecimal puro. | Testes físicos no Stick e Beam. Testado com vermelho (`FF 00 00`), verde (`00 FF 00`) e azul (`00 00 FF`). |
| `0x36` | `PatternLooping` | 1 byte | `0x00` = Color Loop (dinâmico)<br>`0x01` = Static Color (cor fixa). | Teste físico no Stick em conjunto com modo `0x15`. O Beam ignora este campo. |
| `0x45` | `lightBrightness` | 1 byte | `0x00` (0%) a `0x64` (100%). | Teste físico no Stick e Beam. Valores intermediários confirmados (ex: `0x40` ≈ 50%). |
| `0x46` | `lEDMovementSpeed` | 1 byte | `0x00` (mínimo) a `0x64` (máximo). | Teste físico no Stick. |
| `0x49` | `backLightMode` | 1 byte | `0x00` = OFF, `0x01` = ON. | Teste físico no Stick (`lab_results_AA33_20260920_182106.txt`). |
| `0x4A` | `supportPatterns` | N bytes | Array de IDs de efeitos suportados pelo modelo. | Capturas BLE (`ble_probe_*.txt`) e classe `PLLightInfo.java`. |

### Observado

| Field ID | Nome no APK | Tam. | Valores / Formato | Origem da evidência |
|---|---|---|---|---|
| `0x48` | `stageLightNum` | 1 byte | Inteiro presente somente em notificações `AA 32`. | Descompilação do APK. Indica a quantidade de luminárias vinculadas ao grupo. |

### Hipótese

| Field ID | Nome no APK | Tam. | Valores / Formato | Detalhes |
|---|---|---|---|---|
| `0x47` | `speakerIDtoLight` | 2 bytes | 2 bytes codificados em hexadecimal. | Descoberto na classe `PLLightInfo.java`. Hipótese: identificador de posição de palco (canal esquerdo/direito). Pendente de captura com múltiplas luminárias operando no app oficial. |

---

## 6. Dicionário de Campos de Hardware (`AA 13` e `AA 12`)

### Confirmado

| Field ID | Nome no APK | Tam. | Valores / Formato | Origem da validação |
|---|---|---|---|---|
| `0x45` | `soundDetection` | 1 byte | `0x00` = microfone desligado<br>`0x01` = microfone ligado. | Teste físico com `AA 13 04 00 45 01 01`. |

### Observado

| Field ID | Significado | Tam. | Exemplo de valor observado | Origem da evidência |
|---|---|---|---|---|
| `0x37` | Endereço MAC Bluetooth | 6 bytes | `08 79 ff 1e 98 19` | Capturas passivas `AA 12`. |
| `0x40` | Número de Série | 16 bytes | `RT0065-BP0109332` (ASCII) | Capturas passivas `AA 12`. |
| `0x41` | Versão de Firmware | 3 bytes | `00 05 03` (v0.5.3) | Capturas passivas `AA 12`. |

### Hipótese

| Field ID | Nome no APK | Tam. | Descrição | Detalhes |
|---|---|---|---|---|
| `0x46` | `danceMode` | 1 byte | Booleano (`0x00` / `0x01`) em `AA 13`. | Descoberto no APK. Hipótese: variação de sensibilidade da reação ao som. Efeito visual ainda não diferenciado. |
| `0x3C` | `AuracastMode` | 1 byte | Parâmetro de transmissão Auracast. | Descoberto no APK. Não testado por falta de caixa de som PartyBox compatível. |

### Ainda não determinado

- **Comandos de Firmware OTA / DFU (`0x25` a `0x2A`):** Identificados nas classes Java como rotinas de atualização de firmware (`ReqDfuStartCommand`, `ReqDfuSetDataCommand`, etc.). Não devem ser executados para prevenir danos irreversíveis ao firmware das luminárias.

---

## 7. Inconsistências Históricas Resolvidas

Durante as etapas de engenharia reversa, foram registradas discrepâncias que foram esclarecidas por testes físicos posteriores:

1. **Tentativa de envio de comando cru:** Inicialmente supôs-se que enviar `45 01 40` isolado na característica de escrita funcionaria. O teste falhou. A análise de HCI Snoop revelou que o enquadramento `[0xAA] [CMD] [LEN] [0x00]` é obrigatório.
2. **Identificação da luz traseira:** Hipóteses preliminares indicavam o campo `0x48` como responsável pela luz traseira do Stick. O teste físico com `0x48` não produziu efeito. Testes subsequentes com `0x49` sob o comando `AA 33` comprovaram o controle do LED traseiro, o que foi corroborado pela variável `backLightMode` no código descompilado do APK. O campo `0x48` é `stageLightNum` (apenas leitura).

---

## 8. Modos de Efeito (`Pattern` / `0x31`)

Mapeamento cruzado entre a enumeração do APK e o array `0x4A` divulgado pelo hardware:

| ID (Hex) | Nome no APK | Stick | Beam | Observação visual |
|---|---|:---:|:---:|---|
| `0x02` | NEON | Sim | Sim | Gradiente suave e contínuo. |
| `0x09` | LOOP | Sim | Sim | Rotação cíclica da luz. |
| `0x0A` | BOUNCE | Sim | Sim | Pulso de luz que rebate nas pontas. |
| `0x0B` | TRIM | Sim | Sim | Barra de preenchimento tipo medidor de volume. |
| `0x0C` | SWITCH | Sim | Sim | Alternância rápida de cores sem transição. |
| `0x0D` | FREEZE | Sim | Sim | Congela na última cor sem movimento. |
| `0x15` | STATIC | Sim | Não | Cor sólida contínua (exige `0x36 = 0x01`). Ignorado pelo Beam. |
| `0x16` | GRAVITY | Sim | Não | Queda vertical de luz tipo cascata. |
| `0x17` | LIGHTNING | Sim | Não | Flashes rápidos irregulares. |
| `0x18` | GLITCH | Sim | Não | Transições rápidas e desordenadas. |
| `0x19` | CAMPFIRE | Sim | Não | Chamas oscilando a partir da base. |
| `0x10` | OCEAN | Sim | Não | Movimento lento em tons de azul. |
| `0x11` | AURORA | Sim | Não | Gradiente vertical lento. |
| `0x12` | BLOSSOM | Sim | Não | Expansão de luz a partir do meio. |
| `0x1A` | UNIVERSE | Sim | Não | Pontos brilhantes intermitentes sobre fundo escuro. |
| `0x1B` | FIREFLY | Sim | Não | Pontos individuais acesos aleatoriamente. |
| `0x1F` | BEER | Sim | Não | Bolhas subindo da base. |
| `0x20` | STORM | Sim | Não | Fundo escuro com relâmpagos. |
| `0x21` | HOVER | Sim | Não | Blocos de luz oscilando com inércia. |
| `0x22` | SKY | Sim | Não | Variação de tons celestes. |

---

## 9. Exemplos de Comandos Validados (Hexadecimal)

Comandos montados conforme a regra `[AA] [CMD] [LEN] 00 [TLVs...]`:

- **Definir brilho em 50% (`0x40`):**
  `AA 33 04 00 45 01 40`

- **Definir cor para Azul puro (`00 00 FF`):**
  `AA 33 06 00 32 03 00 00 FF`

- **Luz traseira ligada (Stick):**
  `AA 33 04 00 49 01 01`

- **Luz traseira desligada (Stick):**
  `AA 33 04 00 49 01 00`

- **Detecção de som ligada (`AA 13`):**
  `AA 13 04 00 45 01 01`

- **Cor sólida Vermelha no Stick (Comando composto: STATIC + Vermelho + StaticLoop):**
  `AA 33 0C 00 31 01 15 32 03 FF 00 00 36 01 01`
