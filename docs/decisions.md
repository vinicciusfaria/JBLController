# Decisões Arquiteturais

Registro de decisões técnicas tomadas durante o desenvolvimento do JBLController.

---

## 20/09/2026: Framing de comandos BLE a partir do HCI Snoop

**Contexto:**
Tentativas iniciais de enviar comandos curtos sem enquadramento (ex: `45 01 40` direto na característica de escrita) não foram reconhecidas pelo hardware do PartyLight Stick.

**Decisão:**
A partir da análise do log `btsnoop_hci.log` gerado pelo aplicativo oficial JBL One em Android, foi adotada a estrutura de enquadramento completa:
`[0xAA] [Command ID] [Payload Length] [0x00] [Field ID] [Field Len] [Value...]`

- `Command ID 0x33` para configurações visuais (brilho, cor, modo, velocidade, luz traseira).
- `Command ID 0x13` para configurações de hardware (microfone / detecção de som).
- Handle de escrita: `0x8003` / `0x0080` (ATT Write Command `0x52`, sem confirmação).

Todos os construtores de pacote na biblioteca Python (`protocol.py`) devem utilizar essa estrutura.

---

## 24/09/2026: Separação de canais de telemetria VirtualDJ via UDP

**Contexto:**
A integração com o VirtualDJ precisava fornecer posição de áudio e BPM sem interferir na thread principal de processamento de áudio em tempo real do mixer.

**Decisão:**
Implementar o plugin nativo como efeito sonoro (`IVdjPluginDsp8`) que executa uma thread desacoplada em segundo plano transmitindo pacotes UDP locais (`127.0.0.1:9666`) a 30 FPS. O backend Python opera como receptor assíncrono independente, permitindo reiniciar o software de iluminação sem interromper a execução do VirtualDJ.

---

## 30/09/2026: Cálculo de batida contínua no plugin C++

**Contexto:**
A propriedade `SongPosBeats` da API do VirtualDJ retorna apenas a posição dentro do compasso de 4 tempos (oscilando entre 0.0 e 4.0), o que fazia a exibição de compassos no frontend reiniciar periodicamente em loop.

**Decisão:**
Calcular a posição absoluta contínua diretamente em C++ usando o tempo decorrido, a posição do primeiro tempo da grade e o BPM:
`beatPos = ((timeMs - firstBeatMs) / 60000.0) * bpm`
Isso garante monotonicidade ao longo de toda a extensão da faixa musical.
