# Experimentos

## Experimentos Realizados

### Envio Direto de Brilho
- **Comando enviado:** `45 01 40` (diretamente para a characteristic de escrita).
- **Resultado:** O Stick não respondeu.
- **Conclusão:** `45 01 XX` não é, pelo menos isoladamente, um comando de controle funcional.

## Próximos Experimentos

### Laboratório da Luz Traseira (AA 13)
**Objetivo:** Confirmar fisicamente se o comando de controle da luz traseira exige o header `AA 13`.
**Método:**
1. Modificar o script de controle para enviar um pacote usando `AA 13 04 00 45 01 00` e `... 01`.
2. Registrar o comportamento físico da luz traseira do Stick.

---

## Experimentos Concluídos

### Laboratório Físico Inicial (0x46, 0x32, 0x31, 0x48, etc)
**Objetivo:** Validar os principais payloads capturados via `ble_control.py`.
**Resultado:** SUCESSO ABSOLUTO. Testes registrados em `lab_results_20260920_171420.txt`.
**Descobertas Físicas Confirmadas:**
- **Cor (0x32):** `AA 33 06 00 32 03 RR GG BB` funciona perfeitamente.
- **Modo (0x31):** Alterna com sucesso os efeitos de luz da PartyLight.
- **Velocidade (0x46):** Reagiu exatamente de lento (`00`) para rápido (`64`).
**Refutações:**
- O envio do payload de estado da luz traseira (`48 01 01`) usando o header padrão (`AA 33 04 00`) não teve efeito algum. Isso indica forte probabilidade de que a luz traseira seja realmente tratada como a zona `AA 13` e use o código de brilho `45` de forma separada.

---

## Experimentos Concluídos

### Controle Físico de Brilho
**Objetivo:** Confirmar se o envio do pacote com o framing descoberto altera o brilho físico.
**Resultado:** SUCESSO. Testado e validado!
**Descobertas:** O envio de `AA 33 04 00 45 01 40` via Write Command (sem resposta) para a characteristic `...0002` controlou com sucesso o hardware, colocando o brilho em ~50%. Todo o caminho de framing e direcionamento GATT foi comprovado na prática.

### Análise de HCI Snoop (btsnoop_hci.log)
**Objetivo:** Descobrir o ATT Write real enviado pelo aplicativo JBL ONE.
**Resultado:** Análise feita com sucesso em 20/09/2026.
**Descobertas:**
1. A characteristic correta possui Handle `0x8003` (o log em little-endian mostrava `03 80`).
2. É um ATT Write Command (Opcode `0x52`).
3. O payload inclui um framing específico: `[Header] [Length] 00 [Opcode] [SubOpcode] [Data...]`. O Header frontal parece ser `AA 33` e o traseiro `AA 13`.
4. Os Writes analisados casam com as ações de brilho, cores (RGB explícito), e toggle de funcionalidades.
**Conclusão:** O envio direito de apenas `45 01 40` falhava devido à falta do Header, Byte de Tamanho, e Handle incorreto (se o usuário tentava no 0x0080 em vez do 0x8003).

