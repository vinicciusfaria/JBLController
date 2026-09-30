@echo off
echo Compilando ViskoFX.dll para VirtualDJ...
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cl /LD /MT /EHsc src\visko_vdj_plugin.cpp /link /DEF:src\ViskoFX.def Ws2_32.lib /OUT:ViskoFX.dll
if exist ViskoFX.dll (
    echo Copiando para pasta de plugins do VirtualDJ...
    copy /Y ViskoFX.dll "%LOCALAPPDATA%\VirtualDJ\Plugins64\SoundEffect\ViskoFX.dll"
    echo Sucesso!
) else (
    echo Falha na compilacao!
)
pause
