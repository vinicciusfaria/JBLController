---
description: "Regras de Colaboração e Desenvolvimento para o JBLController"
---

# Estrutura de Colaboração do Projeto

- **Usuário (Líder do Projeto e Desenvolvedor Principal):** Autor e idealizador do projeto. Define os requisitos de produto e arquitetura, concebe novas funcionalidades, revisa todo o código, lidera a depuração de problemas e valida a operação física das luminárias e da integração com o VirtualDJ.
- **Gemini:** Assistente técnico de desenvolvimento (pair programming). Responsável por implementar código, refatorar, escrever testes automatizados e manter a documentação sob a direção do Usuário.
- **ChatGPT:** Revisor consultivo secundário. Consultado pontualmente para segundas opiniões sobre hipóteses e análise de dados.

---

# Regras de Desenvolvimento

1. **Distinção estrita:** Nunca tratar hipótese como fato comprovado.
2. **Segurança de hardware:** Nunca enviar pacotes arbitrários ou comandos de atualização de firmware (DFU / `0x25` a `0x2A`).
3. **Consultas prévias:** Sempre consultar `PROTOCOL.md` e `PROJECT_STATE.md` antes de propor ou implementar mudanças nos módulos de comunicação BLE.
4. **Registro de descobertas:** Atualizar `PROTOCOL.md` e os arquivos em `docs/protocol/` sempre que um novo comportamento for confirmado.
5. **Verificação contínua:** Executar a suíte de testes unitários antes de concluir qualquer alteração no código.
6. **Critério de parada por incerteza:** Quando faltarem evidências para definir um comportamento do protocolo, parar a implementação e descrever o experimento necessário para coletar dados.
