import asyncio
from bleak import BleakClient, BleakScanner


STICK_NAME = "JBL PartyLight Stick"

WRITE_UUID = "65786365-6c70-6f69-6e74-2e636f6d0002"


async def main():
    print("Procurando PartyLight Sticks...\n")

    devices = await BleakScanner.discover()

    sticks = [
        device
        for device in devices
        if device.name == STICK_NAME
    ]

    if not sticks:
        print("Nenhum PartyLight Stick encontrado.")
        return

    print("Sticks encontrados:")

    for i, device in enumerate(sticks, start=1):
        print(f"STICK {i}: {device.address}")

    print()

    clients = []

    # Conecta nos dois Sticks
    for device in sticks[:2]:
        print(f"Conectando STICK: {device.address}...")

        try:
            client = BleakClient(device)
            await client.connect()

            clients.append((device, client))

            print(f"CONNECTED: {device.address}\n")

        except Exception as error:
            print(f"FALHA: {device.address}")
            print(f"{type(error).__name__}: {error}")
            print("Continuando...\n")

    if not clients:
        print("Nenhum Stick conseguiu conectar.")
        return

    print("=" * 50)
    print("CONTROLE DE BRILHO")
    print("=" * 50)
    print()
    print("1 - 0%")
    print("2 - 25%")
    print("3 - 50%")
    print("4 - 75%")
    print("5 - 100%")
    print("0 - sair")
    print()

    brightness = {
        "1": 0x00,
        "2": 0x20,
        "3": 0x40,
        "4": 0x50,
        "5": 0x64,
    }

    try:
        while True:
            choice = input("> ")

            if choice == "0":
                break

            if choice not in brightness:
                print("Opção inválida.")
                continue

            value = brightness[choice]

            packet = bytes([
                0x45,
                0x01,
                value,
            ])

            print()
            print(
                f"Enviando: "
                f"{packet.hex(' ')}"
            )

            for device, client in clients:
                try:
                    await client.write_gatt_char(
                        WRITE_UUID,
                        packet,
                        response=False,
                    )

                    print(
                        f"OK -> STICK "
                        f"{device.address}"
                    )

                except Exception as error:
                    print(
                        f"ERRO -> STICK "
                        f"{device.address}: "
                        f"{type(error).__name__}: {error}"
                    )

            print()

    finally:
        print("\nDesconectando...")

        for device, client in clients:
            try:
                await client.disconnect()
                print(f"Disconnected: {device.address}")
            except Exception:
                pass


asyncio.run(main())