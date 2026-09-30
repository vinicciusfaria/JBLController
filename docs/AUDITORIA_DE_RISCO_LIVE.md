# Análise de Riscos Operacionais para Apresentações ao Vivo

Este documento analisa possíveis pontos de falha no ecossistema JBLController durante apresentações contínuas e estabelece recomendações técnicas e procedimentos de contingência.

---

## 1. Riscos identificados e mitigações

### 1.1 Interrupção do fluxo UDP com reprodução ativa ("Runaway Mock")
- **Causa:** Se o VirtualDJ for fechado abruptamente ou se houver falha de rede local, o backend Python deixa de receber pacotes UDP (`is_vdj_live = False`). Caso o último estado recebido tenha sido `playing = True`, o mecanismo de simulação local continuará avançando a linha do tempo baseado no relógio do sistema.
- **Impacto:** O áudio é interrompido, mas o scheduler continua disparando alterações de iluminação na sequência da faixa.
- **Mitigação recomendada:** Implementar um modo estrito de apresentação ao vivo (Live Mode): caso o watchdog de UDP ultrapasse 1,5 segundo sem pacotes, forçar `playing = False` e definir um estado neutro de iluminação (ou blackout) em vez de manter a interpolação local ativa.

### 1.2 Congestionamento da fila BLE por excesso de comandos
- **Causa:** Movimentações contínuas e rápidas em faders de crossfader, pitch ou scrubs no jog wheel podem gerar dezenas de mensagens por segundo. A camada Bluetooth do Windows (`Bleak` sobre WinRT) enfileira as operações de escrita, mas o hardware das luminárias possui taxa máxima de recepção de comandos estimada em 10 a 20 comandos por segundo.
- **Impacto:** Latência acumulada na resposta das luminárias, fazendo com que comandos anteriores sejam executados com segundos de atraso em relação à música.
- **Mitigação recomendada:** Aplicar limitação de taxa (rate limiting / coalescing) no nível do `ControllerState`: durante movimentações contínuas, descartar requisições intermediárias e despachar apenas o estado mais recente em intervalos mínimos de 50 ms a 100 ms.

### 1.3 Sobrecarga de CPU em tentativas sucessivas de reconexão
- **Causa:** Se uma luminária for desligada ou ficar fora de alcance, o loop de reconexão atual tenta restabelecer contato em intervalos curtos e fixos. Falhas repetidas de conexão no subsistema Bluetooth do Windows podem elevar o uso de CPU.
- **Impacto:** Degradação do desempenho do event loop do `asyncio`.
- **Mitigação recomendada:** Implementar recuo exponencial (exponential backoff) com limite máximo (ex: 1s, 2s, 5s, 15s, 30s) e pausa nas tentativas caso um limite configurável seja atingido.

### 1.4 Concorrência no banco de dados SQLite
- **Causa:** Gravações frequentes no banco `faria_fx.db` simultâneas a leituras periódicas pelo scheduler.
- **Mitigação implementada:** Configuração do modo WAL (`PRAGMA journal_mode = WAL;`) e `PRAGMA synchronous = NORMAL;`, permitindo leituras simultâneas sem bloqueio mútuo.

---

## 2. Checklist operacional pré-apresentação

1. **Configuração de energia no Windows:**
   - Desativar a suspensão seletiva de USB nas opções avançadas de energia do Windows para evitar desativação do adaptador Bluetooth.
   - Definir o plano de energia como Alto Desempenho.
2. **Ambiente de rede e conectividade:**
   - Como os adaptadores integrados de Wi-Fi e Bluetooth frequentemente compartilham a mesma antena, conectar o computador à rede cabeada (Ethernet) ou operar offline reduz a interferência de radiofrequência no canal de 2.4 GHz do BLE.
3. **Alimentação dos dispositivos:**
   - Manter os PartyLight Sticks conectados a fontes de alimentação estáveis.
   - Na PartyLight Beam (que possui bateria interna), utilizá-la conectada à fonte de carregamento durante toda a apresentação.
4. **Verificação de telemetria:**
   - Confirmar no console que os pacotes UDP estão sendo recebidos do VirtualDJ e que o Master Deck é atualizado conforme o fader correspondente é levantado.

---

## 3. Procedimentos de contingência

- **Se a iluminação travar ou responder fora de sincronia:**
  Acionar os botões de macro de emergência no painel web (**Blackout** ou **Cor Sólida**), o que substitui o estado atual e força o envio de novos parâmetros diretamente ao hardware.
- **Se as luminárias desconectarem durante a reprodução:**
  Não é necessário reiniciar o VirtualDJ nem interromper a música. O backend Python pode ser reiniciado de forma independente no terminal; ao subir, ele retomará a recepção dos pacotes UDP e restabelecerá a comunicação BLE automaticamente.
