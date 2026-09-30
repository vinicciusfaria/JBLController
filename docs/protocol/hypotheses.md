# Hipóteses e Campos Desconhecidos (Atualizado pós-APK)

*A maior parte das nossas hipóteses antigas foi promovida para `confirmed.md` graças à engenharia reversa do APK real da JBL. O que sobrou aqui são as pontas soltas finais do protocolo.*

## 1. Campos Desconhecidos do Hardware (`ReqSetDevInfo` / `AA 13`)

### O misterioso Dance Mode (`0x46`)
- **Descoberta no APK:** O campo `0x46` enviado pelo header `AA 13` recebe um enum `Switch` (0 = OFF, 1 = ON) mapeado na variável `danceMode`.
- **Dúvida:** O que fisicamente muda na caixa quando isso está ativado? A detecção de som (`0x45`) já faz ela piscar. O que o "Dance Mode" adiciona? 

### Auracast Mode (`0x3C`)
- **Descoberta no APK:** Recebe valores mapeados de `AuracastMode`.
- **Hipótese:** Auracast é a tecnologia Bluetooth LE Audio de broadcast usada nas novas PartyBoxes para conectar múltiplas caixas infinitamente. É provável que esse campo dite se a luz deve seguir o broadcast principal ou não.

## 2. Campos Desconhecidos da Luz (`ReqSetLightInfo` / `AA 33`)

### Identificador de Caixa (`0x47` / `speakerIDtoLight`)
- **Descoberta no APK:** O campo `0x47` carrega 2 bytes que o código converte de/para Hex Strings.
- **Hipótese:** Quando múltiplas PartyLights (ou PartyBoxes) são conectadas no mesmo palco (Stage), a JBL envia um "papel" ou "posição" para cada luz (ex: Direita, Esquerda, Traseira). Precisamos capturar a comunicação com 2 ou mais dispositivos pareados no App oficial para testar como o app os enumera.

## 3. Opcodes Complexos da Engenharia Reversa (Dfu / OTA)
- **`ReqDfuStartCommand` (ID 37 / `0x25`)**
- **`ReqDfuSetDataCommand` (ID 38 / `0x26`)**
- **`ReqDfuCancelCommand` (ID 40 / `0x28`)**
- **`ReqDfuApplyCommand` (ID 42 / `0x2A`)**
- **Hipótese:** Estes são os comandos Over-The-Air (OTA) Firmware Update. Nunca devemos enviar esses headers acidentalmente no laboratório sob risco de corromper o firmware das PartyLights.
