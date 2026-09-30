# VISKO Light FX - VirtualDJ Plugin

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
   Isso gerará o arquivo `ViskoVDJ.dll` na pasta `Release`.

3. **Usando Visual Studio diretamente:**
   Crie um projeto de Biblioteca Dinâmica (DLL) vazio, adicione `visko_vdj_plugin.cpp` e defina `ws2_32.lib` nas dependências do Linker.

## Onde Instalar
Copie o arquivo gerado `ViskoVDJ.dll` para a pasta de plugins do seu VirtualDJ.
No Windows, geralmente fica em:
`C:\Users\SEU_USUARIO\Documents\VirtualDJ\Plugins64\` (ou `Plugins` para versão 32 bits).

Ao abrir o VirtualDJ, o plugin será carregado silenciosamente e iniciará a transmissão de dados no background via `127.0.0.1:9666`.

