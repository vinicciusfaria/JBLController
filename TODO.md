# Lista de Trabalho (TODO)

## Em andamento

- [ ] Ajustar debounce e limitação de taxa (rate limiting) no envio de comandos BLE durante movimentações rápidas de faders/jog wheel para evitar acúmulo na fila do Windows.
- [ ] Implementar leitura do status de bateria da PartyLight Beam (`AA 9D` / `AA 9E`) e exibir indicador de carga na interface web.

---

## Próximos passos

- [ ] Criar rotina de exportação e importação de Cues de faixas em arquivos JSON portáveis para permitir backup e compartilhamento de shows.
- [ ] Adicionar modo de segurança operacional ("Modo Live"): se a comunicação UDP com o VirtualDJ for interrompida por mais de 2 segundos durante reprodução, desativar o avanço por relógio local (mock) e manter a iluminação estática ou em blackout.
- [ ] Implementar backoff exponencial na rotina de reconexão do `partylight.py` para reduzir consumo de CPU caso uma luminária seja desligada.
- [ ] Adicionar suporte a backup automático do banco `faria_fx.db` na inicialização do serviço.

---

## Investigação

- [ ] Analisar o comportamento prático do campo `danceMode` (`0x46` em `AA 13`): verificar se altera a sensibilidade do microfone ou a dinâmica dos efeitos com áudio.
- [ ] Capturar tráfego de múltiplas luminárias operando em conjunto no aplicativo JBL One para investigar o uso do campo `0x47` (`speakerIDtoLight`).
- [ ] Avaliar se existe comando dedicado para controle de canais de cor independentes nos segmentos da torre do PartyLight Stick.

---

## Ideias futuras

- [ ] Integração com controladores MIDI físicos (Launchpad, Akai APC) via biblioteca `mido` para disparo manual de presets e macros.
- [ ] Transiente e detecção de batidas local via análise FFT do fluxo de áudio do sistema (independente de timecode).
- [ ] Empacotamento da aplicação em executável único para Windows (PyInstaller / PyWebView).
