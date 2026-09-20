---
description: "Regras de Colaboração e Investigação BLE para o JBLController"
---

# Estrutura de Colaboração do Projeto

- **Gemini**: Agente executor/desenvolvedor. Responsável por implementar, refatorar, criar testes e manter a documentação.
- **ChatGPT**: Technical Lead/revisor/arquiteto. Analisa evidências, revisa hipóteses/código e orienta o desenvolvimento.
- **Usuário**: Operador do hardware, responsável pela execução de testes físicos e extração de logs (como HCI Snoop).

# Regras de Desenvolvimento e Investigação BLE

1. **Nunca tratar hipótese como fato.** (Exigir sempre confirmação experimental).
2. **Nunca enviar comandos BLE arbitrários** para os dispositivos físicos.
3. **Não assumir** que o framing (estrutura de pacotes) de um Write Request/Command seja igual ao framing das notificações recebidas.
4. Sempre consultar as documentações de protocolo (`docs/protocol/*.md` e `PROTOCOL.md`) antes de propor ou implementar mudanças no controle BLE.
5. Sempre registrar novas descobertas e avanços nos arquivos Markdown correspondentes na pasta `docs/protocol/`.
6. Quando faltar evidência para progredir em uma implementação, **PARE**, não deduza informações e explique ao usuário exatamente qual experimento é necessário realizar.

# Próximos Passos Imediatos (Contexto)

O próximo objetivo técnico **NÃO é** criar mais comandos BLE, mas analisar o Android HCI Snoop/bugreport em busca de:
- ATT Write real enviado pelo JBL ONE;
- UUID da characteristic utilizada;
- Se foi Write Request ou Write Command;
- Payload hexadecimal completo;
- Quais bytes mudam quando SOMENTE o brilho é alterado;
- Comparação entre o Write real e o estado 0x45 observado.
Não invente ou deduza esses dados.

