# Registro de Experimentos BLE

Histórico de testes e experimentos controlados realizados para decodificação do protocolo das luminárias JBL PartyLight.

---

## Experimento 1: Envio Direto de Comandos Raw (Sem Framing)

- **Data:** 20/09/2026
- **Objetivo:** Verificar se o hardware aceita comandos simples de TLV (ex: `45 01 40` para ajuste de brilho a 50%) diretamente na característica de escrita `...0002`.
- **Resultado:** O PartyLight Stick não respondeu e o estado permaneceu inalterado.
- **Conclusão:** O envio de TLVs isolados sem cabeçalho não é interpretado pelo dispositivo. O firmware exige enquadramento com byte de sincronização e tamanho.

---

## Experimento 2: Análise de HCI Snoop (`btsnoop_hci.log`)

- **Data:** 20/09/2026
- **Objetivo:** Identificar o formato exato dos pacotes de escrita enviados pelo aplicativo móvel JBL One.
- **Resultado:**
  - Operação utilizada: GATT Write Without Response (Opcode ATT `0x52`).
  - Característica de escrita identificada no Handle `0x8003` / `0x0080`.
  - Estrutura de enquadramento identificada: `[0xAA] [Command ID] [Length] [0x00] [Field ID] [Field Len] [Value...]`.
  - Command IDs observados: `0x33` para iluminação e `0x13` para funções de hardware.
- **Conclusão:** O formato de framing foi adotado como padrão em todo o controlador.

---

## Experimento 3: Teste de Escrita Controlada de Brilho e Cores

- **Data:** 20/09/2026
- **Arquivo de registro:** `captures/lab_results_20260920_171420.txt` e `captures/lab_results_AA33_20260920_182106.txt`
- **Objetivo:** Validar o envio com framing completo para controle de brilho, cor e velocidade no PartyLight Stick.
- **Resultados:**
  - **Brilho (`0x45`):** `AA 33 04 00 45 01 40` ajustou fisicamente o brilho para aproximadamente 50%. Valores de `0x00` a `0x64` confirmados.
  - **Cor RGB (`0x32`):** `AA 33 06 00 32 03 RR GG BB` alterou a cor base para as componentes enviadas (testado com Vermelho, Verde e Azul).
  - **Velocidade (`0x46`):** `AA 33 04 00 46 01 XX` alterou a taxa de animação dos efeitos.
  - **Modo (`0x31`):** `AA 33 04 00 31 01 XX` alternou os padrões de iluminação da luminária.

---

## Experimento 4: Luz Traseira do Stick

- **Data:** 20/09/2026
- **Objetivo:** Confirmar o campo responsável por ligar e desligar a luz traseira no PartyLight Stick.
- **Resultados:**
  - O envio de `48 01 01` em `AA 33` não produziu efeito.
  - O envio de `AA 33 04 00 49 01 01` ligou o LED traseiro; `AA 33 04 00 49 01 00` desligou.
- **Conclusão:** A luz traseira é controlada pelo Field ID `0x49` sob o Command ID `0x33`. O campo `0x48` atua apenas como leitura em `AA 32` (`stageLightNum`).

---

## Experimento 5: Validação de Compatibilidade no PartyLight Beam

- **Data:** 20/09/2026
- **Arquivos de registro:** `captures/lab_beam_20260920_182938.txt` e `captures/lab_beam_20260920_183359.txt`
- **Objetivo:** Avaliar como o PartyLight Beam responde aos comandos confirmados no Stick.
- **Resultados:**
  - Comandos de brilho (`0x45`) e cor RGB (`0x32`) foram aceitos normalmente.
  - O modo estático `0x15` (`STATIC`) foi ignorado pelo Beam.
  - O Beam reportou em `0x4A` uma lista restrita com 7 modos (`0x02`, `0x08`, `0x09`, `0x0A`, `0x0B`, `0x0C`, `0x0D`).
  - O comando de luz traseira (`0x49`) não possui efeito visual no Beam (ausência física de LED traseiro).
- **Conclusão:** O controlador deve aplicar fallback para o Beam, mapeando modos estáticos para modos dinâmicos compatíveis (como `NEON` ou `LOOP`).
