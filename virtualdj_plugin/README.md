# Plugin VirtualDJ (FariaFX)

Plugin DSP nativo em C++ para VirtualDJ 8 / 2021 / 2023.

O plugin é carregado como efeito sonoro (`IVdjPluginDsp8`) e executa uma thread em segundo plano que extrai dados de reprodução do deck e os transmite via UDP em formato JSON para `127.0.0.1:9666` a aproximadamente 30 quadros por segundo.

---

## Dados transmitidos via UDP

O pacote JSON inclui os seguintes campos:
- `track`: caminho completo do arquivo de áudio carregado no deck.
- `pos`: posição decorrida da música em milissegundos (`get_time elapsed`).
- `beat`: posição contínua em batidas, calculada a partir do tempo decorrido, do primeiro tempo da grade (`firstbeat`) e do BPM.
- `play`: estado de reprodução (`true` se estiver tocando, `false` se pausado).
- `bpm`: BPM da faixa com pitch aplicado.
- `pitch`: variação percentual do pitch.
- `length_ms`: duração total da faixa em milissegundos.
- `deck`: número do deck (1 ou 2) atribuído com auxílio de caching de faders.
- `vol`: volume do deck atual.
- `vol_1` e `vol_2`: volumes individuais dos canais 1 e 2.
- `master_deck`: deck indicado pelo VirtualDJ como master.
- `cross_result`: posição do crossfader (0.0 esquerda, 0.5 centro, 1.0 direita).
- `eq_low_1` e `eq_low_2`: nível do potenciômetro de graves de cada deck.
- `filter_1` e `filter_2`: nível do filtro bipolar de cada deck (0.5 centro, >0.5 High-Pass, <0.5 Low-Pass).

---

## Como compilar

### Pré-requisitos
1. Obtenha o arquivo `vdjPlugin8.h` no portal de desenvolvedores do VirtualDJ (VDJPedia) e coloque-o na pasta `src/`.
2. Compilador C++ com suporte a C++14 (MSVC recomendado no Windows).

### Opção 1: Script de compilação direta (MSVC)
Execute `build.bat` a partir do terminal do Windows:
```powershell
.\build.bat
```
O script invoca as variáveis de ambiente do Visual Studio Build Tools, compila `src/faria_vdj_plugin.cpp` com o arquivo de definição `src/FariaFX.def`, gera `FariaFX.dll` e a copia automaticamente para o diretório de plugins do usuário.

### Opção 2: CMake
```powershell
mkdir build
cd build
cmake ..
cmake --build . --config Release
```
O arquivo `FariaFX.dll` será gerado dentro de `build/Release/`.

---

## Instalação manual

Copie o arquivo `FariaFX.dll` para o diretório de efeitos sonoros do VirtualDJ:
```powershell
copy FariaFX.dll "%LOCALAPPDATA%\VirtualDJ\Plugins64\SoundEffect\FariaFX.dll"
```

No VirtualDJ:
1. Abra as configurações de áudio/efeitos ou o painel de efeitos de um dos decks.
2. Ative o plugin **FariaFX** no master ou nos decks desejados.
3. Certifique-se de que o backend Python do JBLController está em execução para receber as mensagens UDP na porta 9666.
