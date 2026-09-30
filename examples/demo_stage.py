import asyncio
from bleak import BleakScanner
import sys
import os

# Adiciona a pasta src ao PYTHONPATH para rodar o exemplo sem precisar instalar a lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from jbl_controller import PartyLight, Stage

async def main():
    print("Escaneando a pista de dança em busca de PartyLights...")
    devices = await BleakScanner.discover()
    
    party_devices = []
    for d in devices:
        if d.name and "PartyLight" in d.name:
            print(f"Encontrado: {d.name} ({d.address})")
            party_devices.append(PartyLight(d.address))
            
    if not party_devices:
        print("Nenhuma JBL PartyLight encontrada. Verifique se estão ligadas!")
        return
        
    print("\nFormando o Palco e conectando aos dispositivos...")
    palco = Stage(party_devices)
    
    try:
        await palco.connect_all()
        print("Todas as caixas conectadas e prontas!")
        
        # Sequência do Show
        print("\n[Preset] WARMUP: Clima de recepção (Roxo/Azul suave, movimento lento)...")
        await palco.warmup()
        await asyncio.sleep(5)
        
        print("\n[Preset] BUILD: Subindo a energia (Azul intenso, mais rápido)...")
        await palco.build()
        await asyncio.sleep(5)
        
        print("\n[Preset] FUEGO: Pegando fogo! (Laranja/Vermelho)")
        await palco.fuego()
        await asyncio.sleep(5)
        
        print("\n[Preset] DROP: O refrão estourou! (Agressivo, vermelho, velocidade máx)...")
        await palco.drop()
        await asyncio.sleep(5)
        
        print("\n[Preset] RAVE: Cores vibrantes (Magenta neon, muito movimento)...")
        await palco.rave()
        await asyncio.sleep(5)
        
        print("\n[Preset] BREAK / CALM: Finalizando set... Paz e calmaria (Verde menta/Roxo profundo)")
        await palco.calm()
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"Ocorreu um erro durante o show: {e}")
    finally:
        print("\nDesconectando de todos os equipamentos...")
        await palco.disconnect_all()
        print("Show encerrado.")

if __name__ == "__main__":
    asyncio.run(main())

