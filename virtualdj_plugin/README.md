# FARIA Light FX - VirtualDJ Plugin

Este é um plugin nativo em C++ para VirtualDJ 8. Ele extrai as informações do Master Deck e transmite assincronamente (sem atrasar a UI ou o áudio do VDJ) via UDP na porta `9666`.

## Como Compilar

1. **Obtenha a SDK Oficial:** 
   Faça login no VDJPedia (Developer SDK) e baixe o arquivo `vdjPlugin8.h`. Coloque-o dentro da pasta `src/` deste diretório.
   
2. **Usando CMake (Recomendado):**
   ```powershell
   mkdir build
   cd build
   cmake ..
   cmake --build . --config Release
   ```
   Isso gerará o arquivo `FariaVDJ.dll` na pasta `Release`.

3. **Usando build.bat ou Visual Studio diretamente:**
   Execute `build.bat` para compilar diretamente via MSVC `cl` para `FariaFX.dll`.

## Onde Instalar
Copie o arquivo gerado `FariaFX.dll` para a pasta de plugins do seu VirtualDJ.
No Windows, geralmente fica em:
`%LOCALAPPDATA%\VirtualDJ\Plugins64\SoundEffect\FariaFX.dll` (ou na pasta Documents para versões antigas).

Ao abrir o VirtualDJ, o plugin será carregado silenciosamente e iniciará a transmissão de dados no background via `127.0.0.1:9666`.

