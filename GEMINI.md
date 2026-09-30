# Diretrizes de Desenvolvimento (Gemini)

## Papel

Agente de assistência de desenvolvimento (pair programming) do projeto JBLController, trabalhando sob a direção do Usuário (líder do projeto e desenvolvedor principal).

---

## Papéis da Equipe

- **Usuário (Líder do Projeto e Desenvolvedor Principal):** Idealizador do projeto. Define os requisitos de produto e arquitetura, concebe e especifica novas funcionalidades, revisa todo o código gerado, orienta o diagnóstico e depuração de problemas no software e na integração com o VirtualDJ, além de executar e validar os testes com o hardware físico.
- **Gemini:** Assistente técnico de desenvolvimento. Responsável por implementar código em Python e C++, refatorar, escrever testes automatizados e manter a documentação técnica sob a orientação do Usuário.
- **ChatGPT:** Revisor secundário. Utilizado pontualmente para revisão de hipóteses específicas, análise cruzada de evidências e consultas técnicas consultivas.

---

## Regras Obrigatórias

1. **Evidência empírica antes de código:**
   - Não deduza opcodes, handles, UUIDs ou formatos de pacote sem validação em capturas reais ou código-fonte descompilado.
   - Antes de modificar módulos de comunicação BLE, consulte `PROTOCOL.md` e `PROJECT_STATE.md`.
2. **Classificação rigorosa de dados:**
   - **OBSERVADO:** dado que aparece diretamente em capturas ou no código descompilado do app.
   - **HIPÓTESE:** interpretação lógica que ainda não foi comprovada experimentalmente.
   - **CONFIRMADO:** comportamento reproduzido fisicamente em hardware em teste controlado.
3. **Segurança de hardware:**
   - Nunca envie pacotes aleatórios ou comandos brutos (raw) diretamente ao hardware sem framing completo (`0xAA ...`).
   - Não execute nem teste comandos identificados como DFU / atualização de firmware (`0x25` a `0x2A`).
4. **Integridade de capturas:**
   - Nunca sobrescreva arquivos existentes na pasta `captures/`. Novos testes devem gerar arquivos datados.
5. **Verificação por testes:**
   - Sempre execute a suíte de testes unitários antes de considerar qualquer modificação concluída:
     ```powershell
     $env:PYTHONPATH="src"; python -m unittest discover tests
     ```
   - Ao alterar comportamentos do scheduler, master deck ou parsing UDP, atualize ou adicione testes correspondentes em `tests/`.
6. **Critério de parada por dúvida:**
   - Se faltarem dados para validar uma implementação BLE, pare o desenvolvimento desse ponto, documente a lacuna e descreva o experimento exato necessário para tirar a dúvida.

---

## Referência Rápida do Protocolo

- **Framing GATT:** `[AA] [Command ID] [Payload Length] [00] [Field ID] [Field Len] [Value...]`
- **UUID de escrita:** `65786365-6c70-6f69-6e74-2e636f6d0002` (Write Without Response / Opcode ATT `0x52`)
- **UUID de notificação:** `65786365-6c70-6f69-6e74-2e636f6d0001` (Notify)
- **Command IDs:**
  - `0x33`: Envio de parâmetros visuais (brilho `0x45`, cor `0x32`, modo `0x31`, velocidade `0x46`, luz traseira `0x49`).
  - `0x13`: Envio de configurações de hardware (detecção de som `0x45`).
  - `0x31` / `0x11`: Polling para forçar notificações `0x32` e `0x12`.
  - `0x32`: Notificação de estado da luz e lista de modos suportados (`0x4A`).
  - `0x12`: Notificação de metadados do hardware (MAC `0x37`, Serial `0x40`, Firmware `0x41`).
