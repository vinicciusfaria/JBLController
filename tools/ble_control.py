import asyncio
import datetime
import os
from bleak import BleakClient, BleakScanner

STICK_NAME = "JBL PartyLight Stick"
WRITE_UUID = "65786365-6c70-6f69-6e74-2e636f6d0002"

# Laboratório Refatorado - Baseado no JBL One APK.
# O framing AA 33 [Len] 00 será adicionado automaticamente pela função `format_packet`.

EXPERIMENTS = {
    "1": {
        "name": "TESTE: Brilho (AA 33 -> 0x45)",
        "payloads": [
            bytes([0x45, 0x01, 0x00]), # 0%
            bytes([0x45, 0x01, 0x40]), # 50%
            bytes([0x45, 0x01, 0x64]), # 100%
        ]
    },
    "2": {
        "name": "TESTE: Efeitos Visuais (AA 33 -> 0x31)",
        "payloads": [
            bytes([0x31, 0x01, 0x15]), # 21 (STATIC - Cor Fixa)
            bytes([0x31, 0x01, 0x16]), # 22 (GRAVITY)
            bytes([0x31, 0x01, 0x17]), # 23 (LIGHTNING)
            bytes([0x31, 0x01, 0x18]), # 24 (GLITCH)
        ]
    },
    "3": {
        "name": "TESTE: Cor RGB (AA 33 -> 0x32)",
        "payloads": [
            bytes([0x32, 0x03, 0xFF, 0x00, 0x00]), # Vermelho
            bytes([0x32, 0x03, 0x00, 0xFF, 0x00]), # Verde
            bytes([0x32, 0x03, 0x00, 0x00, 0xFF]), # Azul
            bytes([0x32, 0x03, 0xFF, 0xFF, 0x00]), # Amarelo
        ]
    },
    "4": {
        "name": "TESTE: Comportamento da Cor / Pattern Looping (AA 33 -> 0x36)",
        "payloads": [
            bytes([0x36, 0x01, 0x00]), # COLOR_LOOP (0)
            bytes([0x36, 0x01, 0x01]), # STATIC_COLOR (1)
        ]
    },
    "5": {
        "name": "TESTE: Velocidade do Efeito (AA 33 -> 0x46)",
        "payloads": [
            bytes([0x46, 0x01, 0x00]), # 0%
            bytes([0x46, 0x01, 0x20]), # ~30%
            bytes([0x46, 0x01, 0x40]), # ~60%
            bytes([0x46, 0x01, 0x60]), # ~90%
            bytes([0x46, 0x01, 0x64]), # 100%
        ]
    },
    "6": {
        "name": "TESTE: Luz Traseira Oficial (AA 33 -> 0x49)",
        "payloads": [
            bytes([0x49, 0x01, 0x00]), # OFF
            bytes([0x49, 0x01, 0x01]), # ON
        ]
    },
    "7": {
        "name": "TESTE COMBO: Forçar Cor Fixa (STATIC + COLOR + STATIC_LOOP)",
        # Teste que envia os 3 comandos necessários de uma vez no mesmo pacote!
        "payloads": [
            bytes([
                0x31, 0x01, 0x15,                   # Modo = STATIC (0x15)
                0x32, 0x03, 0xFF, 0x00, 0x00,       # Cor = Vermelho
                0x36, 0x01, 0x01                    # Looping = STATIC_COLOR (1)
            ]),
        ]
    }
}

def format_packet(payload: bytes, header: list = [0xAA, 0x33]) -> bytes:
    """Aplica o framing descoberto: [Header] [Len] 00 [Payload]"""
    length = len(payload) + 1
    return bytes(header) + bytes([length, 0x00]) + payload

def open_log_file():
    os.makedirs("captures", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"captures/lab_results_AA33_{timestamp}.txt"
    return open(filepath, "w", encoding="utf-8"), filepath

async def run_experiment(client, exp_key, log_file):
    exp = EXPERIMENTS[exp_key]
    print(f"\nIniciando {exp['name']}")
    log_file.write(f"\n=== EXPERIMENTO: {exp['name']} ===\n")
    
    header = exp.get("header", [0xAA, 0x33])
    
    for payload in exp["payloads"]:
        packet = format_packet(payload, header)
        packet_hex = packet.hex(" ")
        
        print(f"\nEnviando pacote: {packet_hex}")
        try:
            await client.write_gatt_char(WRITE_UUID, packet, response=False)
            print("Pacote enviado com sucesso.")
        except Exception as e:
            print(f"Erro ao enviar: {e}")
            log_file.write(f"[{datetime.datetime.now()}] ERRO AO ENVIAR: {packet_hex} - {e}\n")
            continue
            
        print("\nO que aconteceu fisicamente?")
        print("1 = Mudou")
        print("2 = Não mudou")
        print("3 = Não sei/Ignorar")
        
        while True:
            resp = input("Resposta (1/2/3) ou 'sair' para parar experimento: ").strip()
            if resp.lower() == 'sair':
                print("Cancelando este experimento...")
                return
            if resp in ("1", "2", "3"):
                break
            print("Inválido.")
            
        obs = input("Observação textual adicional (opcional, aperte Enter para pular): ").strip()
        
        status = {"1": "MUDOU", "2": "NAO_MUDOU", "3": "IGNORAR"}[resp]
        log_line = f"[{datetime.datetime.now()}] PACOTE: {packet_hex} | RESULTADO: {status} | OBS: {obs}\n"
        log_file.write(log_line)
        log_file.flush()
        print("Registrado!")

async def main():
    print("Procurando UM PartyLight Stick para Laboratório...\n")
    devices = await BleakScanner.discover()
    sticks = [d for d in devices if "PartyLight" in d.name]

    if not sticks:
        print("Nenhum PartyLight encontrado.")
        return

    # Pega apenas O PRIMEIRO stick para laboratório
    target_device = sticks[0]
    print(f"Alvo do laboratório: {target_device.name} - {target_device.address}\n")

    print(f"Conectando...")
    try:
        client = BleakClient(target_device)
        await client.connect()
        print(f"CONNECTED: {target_device.address}\n")
    except Exception as error:
        print(f"FALHA: {target_device.address} - {error}")
        return

    log_file, log_path = open_log_file()
    print(f"Resultados serão salvos em: {log_path}")

    try:
        while True:
            print("\n" + "=" * 50)
            print("LABORATÓRIO BLE AA 33 - JBL PARTYLIGHT")
            print("=" * 50)
            for k, v in EXPERIMENTS.items():
                print(f"{k} - {v['name']}")
            print("0 - Sair do Laboratório")
            
            choice = input("\nEscolha o experimento: ").strip()
            
            if choice == "0":
                break
                
            if choice in EXPERIMENTS:
                await run_experiment(client, choice, log_file)
            else:
                print("Opção inválida.")
                
    finally:
        print("Desconectando...")
        await client.disconnect()
        log_file.close()
        print("Log fechado e salvo.")

if __name__ == "__main__":
    asyncio.run(main())