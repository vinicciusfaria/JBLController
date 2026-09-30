import asyncio
import sys
import os
from bleak import BleakScanner

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from jbl_controller import PartyLight, Stage
from jbl_controller.controller import ControllerState
from jbl_controller.web_app import run_app

async def setup():
    print("Escaneando PartyLights...")
    devices = await BleakScanner.discover()
    
    party_devices = []
    for d in devices:
        if d.name and "PartyLight" in d.name:
            print(f"Encontrado: {d.name} ({d.address})")
            party_devices.append(PartyLight(d.address, name=d.name))
            
    if not party_devices:
        print("Nenhuma JBL PartyLight encontrada. Modo demonstração (sem caixas conectadas).")
        # Podemos iniciar com Stage vazio para teste de UI
        palco = Stage([])
    else:
        palco = Stage(party_devices)
        try:
            await palco.connect_all()
            print("Todas as caixas conectadas!")
        except Exception as e:
            print(f"Aviso: Não foi possível conectar nas luzes ({e}). O site abrirá em modo offline para as luzes, mas o VirtualDJ funcionará!")
        
    state = ControllerState(palco)
    await state.set_brightness(0)
    return state

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    state = loop.run_until_complete(setup())
    
    print("Iniciando Interface Web em http://localhost:8080")
    run_app(state, port=8080)

