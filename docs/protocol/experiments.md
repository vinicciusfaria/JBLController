# Experimentos

## Experimentos Realizados

### Envio Direto de Brilho
- **Comando enviado:** `45 01 40` (diretamente para a characteristic de escrita).
- **Resultado:** O Stick não respondeu.
- **Conclusão:** `45 01 XX` não é, pelo menos isoladamente, um comando de controle funcional.

## Próximos Experimentos

### Análise de HCI Snoop
**Objetivo:** Descobrir o ATT Write real enviado pelo aplicativo JBL ONE.
**Método:** Analisar o log do Android HCI Snoop/bugreport para identificar:
1. ATT Write real enviado pelo JBL ONE;
2. UUID da characteristic utilizada;
3. Se foi Write Request ou Write Command;
4. Payload hexadecimal completo;
5. Quais bytes mudam quando **SOMENTE** o brilho é alterado;
6. Comparação entre o Write real e o estado `0x45` observado nas notificações.

