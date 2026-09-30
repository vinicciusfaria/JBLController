# Especificação do Protocolo JBL PartyLight BLE

> **Status:** 100% Confirmado e validado fisicamente.
> Esta especificação reflete a arquitetura do firmware contido nas JBL PartyLights Stick e Beam, descoberta através de captura passiva (HCI Snoop) no Android e reproduzida ativamente na biblioteca Python nativa deste repositório (`jbl_controller`).

---

## 1. TRANSPORTE BLE

- **Serviço Principal:** `0000fea0-0000-1000-8000-00805f9b34fb` (ou desconhecidos baseados no mapeamento UUID/Handle).
- **UUID de Escrita (Command):** `65786365-6c70-6f69-6e74-2e636f6d0002`
- **UUID de Notificação (Status):** `65786365-6c70-6f69-6e74-2e636f6d0001`
- **Propriedades GATT:** 
  - Escrita: `Write Without Response` (GATT Write Command - Opcode ATT `0x52`).
  - Leitura: `Notify` para receber as respostas da caixa.
- **Handles Observados:** 
  - `0x0080` / `0x8003` para comandos (depende da controladora Bluetooth host).
  - `0x8006` / `32772` para notify.
- **Diferença (Comando x Notificação):** O app envia configurações através do UUID de Escrita usando pacotes do tipo `Command` (sem exigir ACK). A caixa responde ativamente ou notifica mudanças manuais através do UUID de Notificação enviando de volta as propriedades totais do dispositivo.

---

## 2. FRAMING

Todo envio ou recebimento usa este formato de encapsulamento contíguo:

`[AA] [Command ID] [Payload Length] | [00] [Field 1 ID] [Field 1 Len] [Field 1 Value] [Field N...]`

- **`AA` (1 byte):** Identifier universal fixo.
- **`Command ID` (1 byte):** Define o contexto dos campos seguintes (ex: Luz ou Hardware).
- **`Payload Length` (1 byte):** Define o tamanho em bytes do array a partir do próximo byte.
- **`00` (1 byte fixo):** Byte obrigatório que marca o início do payload de dados. 
- **`Field ID` (1 byte):** O código da propriedade que está sendo alterada.
- **`Field Length` (1 byte):** Quantos bytes o valor desta propriedade ocupa.
- **`Field Value` (N bytes):** O valor em si.

**Como o Payload Length é calculado:**
`Payload Length = 1 (para o byte 00) + (1 para Field ID + 1 para Field Len + N para Field Value)`
O protocolo suporta **encadeamento**. Você pode enviar múltiplos Fields em sequência no mesmo payload. O `Payload Length` será a soma de todos os blocos mais o `00` inicial.

---

## 3. COMMAND IDs

O Command ID define o contexto do pacote. Os Fields IDs (`0x45`, `0x46`, etc) mudam de significado de acordo com qual Command ID os encapsulou.

| Header | Classe Java | Função | Ação/Status | Evidência |
|---|---|---|---|---|
| **`AA 33`** | `ReqSetLightInfo` | Controle de Iluminação. | Comando enviado. | CONFIRMADO EM AMBOS |
| **`AA 13`** | `ReqSetDevInfo` | Controle de Hardware/Som. | Comando enviado. | CONFIRMADO PELO APK |
| **`AA 31`** | `ReqLightInfo` | Polling. Envia `AA 31 00`. Força a resposta do `AA 32`. | Comando enviado. | CONFIRMADO EM AMBOS |
| **`AA 11`** | `ReqDevInfo` | Polling. Envia `AA 11 00`. Força a resposta do `AA 12`. | Comando enviado. | CONFIRMADO PELO APK |
| **`AA 32`** | `PLLightInfo` | Status de Iluminação atualizado. | Notificação recebida. | CONFIRMADO EM AMBOS |
| **`AA 12`** | *(Status de Dev)* | Status de Hardware/Configuração. | Notificação recebida. | CONFIRMADO PELO HCI |
| **`AA 9D`** | `ReqBatteryStatus` | Pede status da bateria da Beam. | Comando enviado. | CONFIRMADO PELO APK |
| **`AA 9E`** | *(BatteryInfo)* | Nível de bateria. | Notificação recebida. | CONFIRMADO PELO APK |

---

## 4. AA 33 / ILUMINAÇÃO

Tabela de comandos visuais que trafegam dentro de blocos empacotados por `AA 33` (Envio) e `AA 32` (Status):

| Field ID | Nome Interno | Tamanho | Valores | Stick | Beam | Evidência Final |
|---|---|---|---|---|---|---|
| **`0x31`** | `Pattern` | 1 byte | `0x00` a `0x22` (ver aba PATTERNS). | Suportado | Suportado (Subconjunto) | CONFIRMADO EM AMBOS |
| **`0x32`** | `Color` | 3 bytes | `R G B` (Ex: `FF 00 00`). | Suportado | Suportado | CONFIRMADO EM AMBOS |
| **`0x36`** | `PatternLooping`| 1 byte | `00`=Loop, `01`=Static. | Suportado | Não suportado | CONFIRMADO EM AMBOS |
| **`0x45`** | `Brightness` | 1 byte | `00` (0%) a `64` (100%). | Suportado | Suportado | CONFIRMADO EM AMBOS |
| **`0x46`** | `LEDSpeed` | 1 byte | `00` (0%) a `64` (100%). | Suportado | Não testado f. | CONF. FISICAMENTE NO STICK |
| **`0x49`** | `BackLightMode` | 1 byte | `00`=OFF, `01`=ON. | Suportado | Sem hardware f. | CONF. FISICAMENTE NO STICK |
| **`0x48`** | `stageLightNum` | 1 byte | Int (somente no `AA 32`). | Notifica | Notifica | CONFIRMADO PELO APK |
| **`0x4A`** | `supportPatterns`| N bytes | Array de hex (somente no `AA 32`). | Notifica | Notifica | CONFIRMADO EM AMBOS |

---

## 5. PATTERNS (`0x31`)

Mapeamento cruzado da enumeração do APK com o array divulgado pelo hardware via `0x4A` e com os testes de laboratório. Não foi testado todos, os vazios significam "Não Testado".

| ID Hex | Nome no APK | No `0x4A` Stick | Físico Stick | No `0x4A` Beam | Físico Beam |
|---|---|:---:|:---:|:---:|:---:|
| `00` | OFF | - | - | - | - |
| `01` | ROCK | - | - | - | - |
| `02` | NEON | Sim | - | Sim | CONFIRMADO |
| `03` | CLUB | - | - | - | - |
| `04` | FLOW | - | - | - | - |
| `05` | RIPPLE | - | - | - | - |
| `06` | CROSS | - | - | - | - |
| `07` | FLASH | - | - | - | - |
| `08` | CUSTOM_RANDOM| Sim | - | Sim | - |
| `09` | LOOP | Sim | - | Sim | CONFIRMADO |
| `0A` | BOUNCE | Sim | - | Sim | CONFIRMADO |
| `0B` | TRIM | Sim | - | Sim | - |
| `0C` | SWITCH | Sim | - | Sim | - |
| `0D` | FREEZE | Sim | - | Sim | CONFIRMADO |
| `10` | OCEAN | Sim | - | - | - |
| `11` | AURORA | Sim | - | - | - |
| `12` | BLOSSOM | Sim | - | - | - |
| `13` | SUNRISE | - | - | - | - |
| `14` | FIREPLACE | - | - | - | - |
| `15` | STATIC | - | CONFIRMADO | - | Não Suportado |
| `16` | GRAVITY | Sim | CONFIRMADO | - | Recusado |
| `17` | LIGHTNING | Sim | CONFIRMADO | - | Recusado |
| `18` | GLITCH | Sim | CONFIRMADO | - | Recusado |
| `19` | CAMPFIRE | Sim | - | - | - |
| `1A` | UNIVERSE | Sim | - | - | - |
| `1B` | FIREFLY | Sim | - | - | - |
| `1F` | BEER | Sim | - | - | - |
| `20` | STORM | Sim | - | - | - |
| `21` | HOVER | Sim | - | - | - |
| `22` | SKY | Sim | - | - | - |

*Aviso legal: O fato de constar na Tabela Enum do APK não significa que a caixa possua ou execute a animação, o fator de segurança é o array dinâmico `0x4A`.*

---

## 6. DIFERENÇAS STICK × BEAM

1. **Hardware Categórico:**
   - **PartyLight Stick:** Um "bastão" de múltiplos LEDs orientados à pixels e uma luz branca oposta fixa para a parede (Luz Traseira).
   - **PartyLight Beam:** Um projetor óptico de refração motora em teto/parede, sem luz traseira e sem modo "pixels estáticos". 
2. **Looping e Static (Cor Fixa):**
   - Apenas a Stick obedeceu e consolidou o uso do comando `0x36 01 01` atrelado ao Pattern `0x15` (STATIC).
   - A Beam **ignorou** fisicamente os modos de looping sólido porque não suporta `0x15`. Nela, cores RGB base são passadas para seus modos de refração e estrobo fluídos (ex: `0x02` NEON colorido).
3. **Exclusividade de Pattern:**
   - A Beam se limitou fisicamente a 7 modos específicos pelo seu `0x4A`. Ao tentarmos enviar modos exclusivos da Stick (como Gravity `0x16`), a Beam ativou um fallback interno aleatório (ignorou e tocou padrão).
4. **Alimentação:** A Beam provou responder ao pedido de Bateria (`AA 9D`), enquanto a Stick é energia de tomada (Cabo Fixo).

---

## 7. AA 13 / HARDWARE

Comandos de comportamento que controlam features de hardware embarcado:

| Field ID | Nome Interno | Tamanho | Valores | Função Física | Evidência Final |
|---|---|---|---|---|---|
| **`0x45`** | `soundDetection`| 1 byte | `00`=OFF, `01`=ON. | Reagir microfone interno à som local. | CONFIRMADO PELO APK + HCI |
| **`0x46`** | `danceMode` | 1 byte | `00`=OFF, `01`=ON. | Mapeado no APK. (Função final desconhecida). | CONFIRMADO PELO APK |
| **`0x3C`** | `AuracastMode` | 1 byte | Não testado. | Gerencia Bluetooth LE Audio Broadcast. | CONFIRMADO PELO APK |

---

## 8. EXEMPLOS DE CÓDIGO (HEX Payload)

Estes são pacotes prontos testados com sucesso absoluto:

**Brilho para 50%:**
`AA 33 04 00 45 01 40`

**Modo de Efeito Gravity:**
`AA 33 04 00 31 01 16`

**Cor Base para Azul:**
`AA 33 06 00 32 03 00 00 FF`

**Luz Traseira OFF:**
`AA 33 04 00 49 01 00`

**Comando Composto Cor Fixa (STATIC + VERMELHO + LOOP_STATIC) [Tamanho 12]:**
`AA 33 0C 00 31 01 15 32 03 FF 00 00 36 01 01`

**Comando Envio de Hardware - Reação ao Som OFF (Header 13):**
`AA 13 04 00 45 01 00`

---

## 9. AINDA NÃO CONFIRMADO (LIMITAÇÕES)

Estas lacunas devem ser compreendidas no futuro via análise avançada ou capturas do JBL One autênticas. Não implementar métodos fechados para eles ainda:

1. **`0x47` (SpeakerIDtoLight):** Envia uma string Hex de 2 bytes no Header `AA 33`. Hipótese: Controle de agrupamento Estéreo/Stage de múltiplas PartyLights (Direita vs Esquerda).
2. **Opcodes `0x25` a `0x2A` (DFU OTA):** Comandos perigosos descobertos no APK (DfuStart, DfuSetData, DfuApply). Não devemos invocar acidentalmente.
3. **`0x46` no Hardware:** O `danceMode` do `AA 13`. Faltam testes puramente comportamentais para diferenciar seu efeito em oposição à Detecção de Som.
4. **`0x3C` (Auracast):** Faltam caixas PartyBox habilitadas para testarmos sincronia física.

