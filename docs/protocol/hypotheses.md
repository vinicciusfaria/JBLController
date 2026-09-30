# Hipóteses e Campos em Investigação

Registro dos campos identificados na engenharia reversa do aplicativo JBL One que ainda dependem de validação experimental.

---

## 1. Campos de Hardware (`AA 13`)

### Modo de Dança (`danceMode` / `0x46`)
- **Origem:** Campo booleano (`0x00` = OFF, `0x01` = ON) identificado na classe `ReqSetDevInfo` do APK.
- **Hipótese:** Pode alterar a sensibilidade de resposta do microfone interno ou modificar o padrão rítmico das animações com som ativo.
- **Experimento pendente:** Enviar `AA 13 04 00 46 01 01` com áudio ambiente e comparar o comportamento visual em relação ao modo de detecção de som padrão (`0x45`).

### Modo Auracast (`AuracastMode` / `0x3C`)
- **Origem:** Mapeado no código do APK em relação ao suporte a Bluetooth LE Audio Broadcast.
- **Hipótese:** Define se a luminária opera sincronizada ao fluxo Auracast de caixas de som JBL PartyBox compatíveis.
- **Limitação:** Requer hardware transmissor PartyBox compatível para testes.

---

## 2. Campos de Iluminação (`AA 33`)

### Identificador de Palco (`speakerIDtoLight` / `0x47`)
- **Origem:** O campo carrega 2 bytes codificados como string hexadecimal.
- **Hipótese:** Utilizado pelo aplicativo oficial para atribuir uma posição espacial à luminária quando múltiplas unidades estão agrupadas no mesmo ambiente (ex: canal esquerdo, canal direito).
- **Experimento pendente:** Capturar tráfego BLE com 2 ou mais PartyLights pareadas simultaneamente no JBL One.

---

## 3. Comandos de Atualização de Firmware (DFU / OTA)

Os seguintes Command IDs foram identificados no APK e correspondem a rotinas de atualização de firmware:
- `0x25` (`ReqDfuStartCommand`)
- `0x26` (`ReqDfuSetDataCommand`)
- `0x28` (`ReqDfuCancelCommand`)
- `0x2A` (`ReqDfuApplyCommand`)

**Aviso operacional:** Estes comandos não devem ser transmitidos aos dispositivos em testes de controle para evitar corrupção da memória flash do hardware.
