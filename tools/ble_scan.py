import asyncio
from bleak import BleakScanner


async def main():
    print("Procurando dispositivos BLE...\n")

    devices = await BleakScanner.discover()

    for device in devices:
        print(f"Nome: {device.name}")
        print(f"Endereço: {device.address}")
        print("-" * 40)


asyncio.run(main())