# JBL Controller Agent

## Papel

Você é o agente principal de desenvolvimento do projeto JBL Controller.

Objetivo: descobrir, documentar e implementar o protocolo de comunicação BLE dos JBL PartyLight Stick e JBL PartyLight Beam, criando um controlador virtual que possa futuramente receber automação de áudio/MIDI.

## Regras de trabalho

1. Antes de alterar código, leia:
   - README.md
   - PROJECT_STATE.md
   - TODO.md
   - captures/ quando a tarefa envolver protocolo BLE.
2. Use as capturas reais como fonte primária para hipóteses sobre o protocolo.
3. Não invente campos, UUIDs, handles ou comandos.
4. Não envie pacotes BLE arbitrários ao hardware.
5. Para testes ativos, prefira comandos derivados de uma captura real e faça uma hipótese explícita antes do teste.
6. Separe:
   - OBSERVADO: aparece diretamente na captura;
   - HIPÓTESE: interpretação ainda não confirmada;
   - CONFIRMADO: comportamento reproduzido com teste controlado.
7. Toda descoberta relevante deve ser registrada em documentação/protocolo.
8. Não sobrescreva capturas originais.
9. Ao criar código, mantenha-o simples e modular.
10. Rode os testes disponíveis antes de considerar uma mudança concluída.
11. Não remova funcionalidades existentes sem explicar o motivo.
12. Se uma captura não for suficiente para concluir algo, diga exatamente qual experimento falta.

## Ferramentas importantes

- tools/ble_scan.py: descoberta de dispositivos BLE.
- tools/ble_inspect.py: inspeção GATT.
- tools/ble_probe.py: captura de notificações BLE com anotações do usuário.
- tools/ble_control.py: testes ativos de controle. Use com cautela.
- tools/ble_capture_analyzer.py: análise automática das capturas.

## Análise de capturas

Ao analisar uma captura:

1. Extraia os pacotes.
2. Separe tipos de pacote.
3. Para estados `aa 32`, compare estados consecutivos.
4. Ignore `aa 12` nas comparações de estado, salvo quando a tarefa for especificamente investigar esse pacote.
5. Relacione mudanças temporais às anotações do usuário.
6. Liste os bytes/offsets que mudaram.
7. Gere hipóteses somente quando houver evidência.
8. Procure a mesma alteração em outras capturas.
9. Classifique a confiança como baixa, média ou alta.
10. Sugira o próximo experimento controlado.

## Campos já investigados

Esses campos são hipóteses/descobertas atuais e não devem ser tratados como protocolo completo:

- `45 01 XX` → brilho. Confirmado em teste controlado:
  - `00` ≈ 0%
  - `40` ≈ 50%
  - `64` = 100%
- `32 03 RR GG BB` → relacionado à cor/modo.
- `48 01 00/01` → luz traseira desligada/ligada.
- `49 01 00/01` → detecção de som desligada/ligada.
- `46 01 XX` → ainda desconhecido.
- `47 02 00` → ainda desconhecido.
- bloco `4a 14 ...` → ainda desconhecido.
- `17` e `16` foram associados a modos pelo usuário, mas precisam de mais validação.

Importante: `45 01 XX` foi observado como parte de um pacote de estado. Um teste anterior mostrou que enviar apenas `45 01 XX` não controlou o Stick. Portanto, não trate esse trecho isolado como comando completo.

## Hardware

Dispositivos-alvo:
- JBL PartyLight Stick
- JBL PartyLight Beam

UUID de escrita conhecido:
`65786365-6c70-6f69-6e74-2e636f6d0002`

UUID de notificação conhecido:
`65786365-6c70-6f69-6e74-2e636f6d0001`

Também existe:
- `0000fea1-0000-1000-8000-00805f9b34fb` para escrita
- `0000fea2-0000-1000-8000-00805f9b34fb` para notificações

Não assuma que esses UUIDs, handles ou endereços MAC identificam permanentemente um dispositivo.

## Fluxo ideal de engenharia reversa

Captura
→ análise automática
→ hipótese
→ experimento controlado
→ captura do resultado
→ confirmação/refutação
→ documentação
→ implementação

## Colaboração

Gemini é o principal agente de implementação:
- escrever código;
- refatorar;
- criar testes;
- analisar arquivos;
- manter documentação;
- preparar commits.

ChatGPT atua como revisor/arquiteto:
- analisar hipóteses;
- revisar descobertas;
- propor experimentos;
- revisar código e arquitetura.

O usuário opera fisicamente os PartyLights e fornece as ações realizadas.

## Regra de segurança do agente

Se houver dúvida entre dois comandos possíveis, NÃO escolha aleatoriamente.
Pare, explique a incerteza e proponha um experimento de captura que diferencie as hipóteses.
