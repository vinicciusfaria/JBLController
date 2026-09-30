import asyncio
import datetime
import os
from bleak import BleakClient, BleakScanner

BEAM_NAME = "JBL PartyLight Beam"
WRITE_UUID = "65786365-6c70-6f69-6e74-2e636f6d0002"

EXPERIMENTS = {
    "1": {
        "name": "BEAM TESTE OFICIAL: Modos Suportados (0x31)",
        "payloads": [
            bytes([0x31, 0x01, 0x02]), # NEON
            bytes([0x31, 0x01, 0x09]), # LOOP
            bytes([0x31, 0x01, 0x0A]), # BOUNCE
            bytes([0x31, 0x01, 0x0D]), # FREEZE
        ]
    },
    "2": {
        "name": "BEAM TESTE OFICIAL: Cor RGB no modo NEON",
        "payloads": [
            # Primeiro seta para NEON
            bytes([0x31, 0x01, 0x02]),
            # Depois testa as cores
            bytes([0x32, 0x03, 0xFF, 0x00, 0x00]), # Vermelho
            bytes([0x32, 0x03, 0x00, 0xFF, 0x00]), # Verde
        ]
    }
}

def format_packet(payload: bytes, header: list = [0xAA, 0x33]) -> bytes:
    length = len(payload) + 1
    return bytes(header) + bytes([length, 0x00]) + payload

def open_log_file():
    os.makedirs("captures", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"captures/lab_beam_{timestamp}.txt"
    return open(filepath, "w", encoding="utf-8"), filepath

async def run_experiment(client, exp_key, log_file):
    exp = EXPERIMENTS[exp_key]
    print(f"\nIniciando {exp['name']}")
    log_file.write(f"\n=== EXPERIMENTO: {exp['name']} ===\n")
    
    for payload in exp["payloads"]:
        packet = format_packet(payload)
        packet_hex = packet.hex(" ")
        
        print(f"\nEnviando pacote: {packet_hex}")
        try:
            await client.write_gatt_char(WRITE_UUID, packet, response=False)
            print("Pacote enviado com sucesso.")
        except Exception as e:
            print(f"Erro ao enviar: {e}")
            continue
            
        print("\nO que aconteceu fisicamente?")
        print("1 = Mudou")
        print("2 = Não mudou")
        
        while True:
            resp = input("Resposta (1/2) ou 'sair': ").strip()
            if resp.lower() == 'sair': return
            if resp in ("1", "2"): break
            
        obs = input("Descrição do efeito / OBS: ").strip()
        status = {"1": "MUDOU", "2": "NAO_MUDOU"}[resp]
        log_line = f"[{datetime.datetime.now()}] PACOTE: {packet_hex} | RESULTADO: {status} | OBS: {obs}\n"
        log_file.write(log_line)
        log_file.flush()

async def main():
    print("Procurando o PartyLight Beam...")
    devices = await BleakScanner.discover()
    beams = [d for d in devices if d.name == BEAM_NAME]

    if not beams:
        print("Nenhum Beam encontrado.")
        return

    target_device = beams[0]
    print(f"Conectando a {target_device.name}...")
    
    try:
        client = BleakClient(target_device)
        await client.connect()
        
        log_file, _ = open_log_file()
        
        while True:
            print("\n" + "=" * 50)
            print("LABORATÓRIO BEAM - TESTE DE MODOS CONFIRMADOS")
            print("=" * 50)
            for k, v in EXPERIMENTS.items():
                print(f"{k} - {v['name']}")
            print("0 - Sair")
            
            choice = input("\nEscolha: ").strip()
            if choice == "0": break
            if choice in EXPERIMENTS:
                await run_experiment(client, choice, log_file)
                
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
