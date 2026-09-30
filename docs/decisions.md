# Decisões Arquiteturais e de Investigação
 
 Este documento registra as decisões arquiteturais e as decisões importantes tomadas durante a investigação do protocolo de comunicação BLE dos dispositivos JBL PartyLight.
 
-*(Atualmente sem registros. As decisões serão adicionadas conforme o projeto avança, validadas pelo ChatGPT/Tech Lead e implementadas pelo Gemini.)*
+## 20/09/2026: Framing do Comando BLE (HCI Snoop)
+Foi decidido adotar a estrutura de framing descoberta no log `btsnoop_hci.log` para todos os novos testes de controle, invalidando a tentativa de enviar payloads crus sem cabeçalho.
+
+**Estrutura adotada para comandos:**
+`[Header] [Length] 00 [Comando] [Subcomando] [Dados]`
+
+- **Header:** `AA 33` para zona frontal, `AA 13` possivelmente para zona traseira.
+- **Length:** O tamanho (em bytes) do restante do pacote.
+- **Handle de escrita:** O handle correto identificado foi `0x8003`.
+
+Essa decisão nos protege contra envios espúrios. Todo o código que formata os pacotes no `JBLController` deverá aplicar o framing `AA 33` / `AA 13` e calcular o byte de Length adequadamente.

