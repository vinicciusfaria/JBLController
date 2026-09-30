@echo off
echo Compilando FariaFX.dll para VirtualDJ...
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cl /LD /MT /EHsc src\faria_vdj_plugin.cpp /link /DEF:src\FariaFX.def Ws2_32.lib /OUT:FariaFX.dll
if exist FariaFX.dll (
    echo Copiando para pasta de plugins do VirtualDJ...
    copy /Y FariaFX.dll "%LOCALAPPDATA%\VirtualDJ\Plugins64\SoundEffect\FariaFX.dll"
    echo Sucesso!
) else (
    echo Falha na compilacao!
)
pause
