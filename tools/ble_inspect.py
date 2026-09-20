import asyncio
from datetime import datetime
from pathlib import Path

from bleak import BleakScanner, BleakClient


JBL_NAMES = {
    "JBL PartyLight Stick",
    "JBL PartyLight Beam",
}


async def inspect_device(device, output):
    output.write("=" * 70 + "\n")
    output.write(f"DEVICE: {device.name}\n")
    output.write(f"ADDRESS: {device.address}\n")
    output.write("=" * 70 + "\n\n")

    print(f"\nConectando a {device.name} ({device.address})...")

    try:
        async with BleakClient(device.address) as client:
            print("Conectado!")

            services = client.services

            for service in services:
                output.write(f"SERVICE\n")
                output.write(f"  UUID: {service.uuid}\n")
                output.write(f"  Description: {service.description}\n\n")

                for characteristic in service.characteristics:
                    output.write("  CHARACTERISTIC\n")
                    output.write(f"    UUID: {characteristic.uuid}\n")
                    output.write(f"    Description: {characteristic.description}\n")
                    output.write(f"    Properties: {', '.join(characteristic.properties)}\n\n")

            output.write("\n")

    except Exception as e:
        print(f"Erro: {e}")
        output.write("ERROR\n")
        output.write(f"  {type(e).__name__}: {e}\n\n")


async def main():
    print("Procurando PartyLights...\n")

    devices = await BleakScanner.discover()

    jbl_devices = [
        device
        for device in devices
        if device.name in JBL_NAMES
    ]

    if not jbl_devices:
        print("Nenhum PartyLight encontrado.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path("captures") / f"gatt_inspection_{timestamp}.txt"

    with output_path.open("w", encoding="utf-8") as output:
        output.write("JBL PARTYLIGHT GATT INSPECTION\n")
        output.write(f"Date: {datetime.now().isoformat()}\n\n")

        for device in jbl_devices:
            await inspect_device(device, output)

    print(f"\nInspeção concluída!")
    print(f"Resultado salvo em: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())