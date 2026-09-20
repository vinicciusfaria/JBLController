# JBL Capture Analyzer

Ferramenta inicial para analisar automaticamente capturas geradas pelo `ble_probe.py`.

Uso:

```powershell
python tools\ble_capture_analyzer.py captures\ble_probe_YYYYMMDD_HHMMSS.txt
```

Para saída JSON:

```powershell
python tools\ble_capture_analyzer.py captures\ble_probe_YYYYMMDD_HHMMSS.txt --json
```

A ferramenta atualmente:
- extrai pacotes `aa ...`;
- identifica pacotes de estado `aa 32`;
- compara estados consecutivos;
- mostra bytes/offsets alterados;
- encontra anotações `AÇÃO DO USUÁRIO`;
- aplica apenas hipóteses de protocolo já documentadas.
