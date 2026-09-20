import asyncio
from datetime import datetime
from pathlib import Path

from bleak import BleakClient, BleakScanner


STICK_NAME = "JBL PartyLight Stick"
BEAM_NAME = "JBL PartyLight Beam"

NOTIFY_UUIDS = {
    "65786365-6c70-6f69-6e74-2e636f6d0001",
    "0000fea2-0000-1000-8000-00805f9b34fb",
}

CHANGE_WAIT = 1.5


async def main():
    print("Procurando dispositivos do Viskostage...\n")

    devices = await BleakScanner.discover()

    sticks = [
        device for device in devices
        if device.name == STICK_NAME
    ]

    beams = [
        device for device in devices
        if device.name == BEAM_NAME
    ]

    if len(sticks) < 2:
        print("Não encontrei os dois PartyLight Stick.")
        return

    if len(beams) < 1:
        print("Não encontrei o PartyLight Beam.")
        return

    selected_devices = sticks + [beams[0]]

    print("Dispositivos encontrados:\n")

    for device in sticks:
        print(f"STICK  - {device.address}")

    print(f"BEAM   - {beams[0].address}")
    print()

    capture_dir = Path("captures")
    capture_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = capture_dir / f"ble_probe_{timestamp}.txt"

    def log(text):
        print(text)

        with output.open("a", encoding="utf-8") as file:
            file.write(text + "\n")

    log("=== VISKOSTAGE BLE CAPTURE ===")
    log(f"INÍCIO: {datetime.now()}")
    log("")

    clients = []
    last_data = {}
    pending_changes = {}

    event_lock = asyncio.Lock()

    def get_device_type(device):
        if device.name == BEAM_NAME:
            return "BEAM"

        return "STICK"

    async def document_change(device, uuid, old_data, new_data):
        async with event_lock:
            log("")
            log("=" * 60)
            log("POSSÍVEL ALTERAÇÃO DETECTADA")
            log("=" * 60)
            log(f"HORÁRIO: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            log(f"TIPO DETECTADO: {get_device_type(device)}")
            log(f"UUID: {uuid}")
            log("")

            log("[1] SIM, EU MEXI EM UM DISPOSITIVO")
            log("[2] NÃO / NÃO MEXI EM NADA")
            log("[3] IGNORAR")

            while True:
                choice = await asyncio.to_thread(
                    input,
                    "\nEscolha: "
                )

                if choice in ("1", "2", "3"):
                    break

                print("Escolha inválida.")

            if choice == "1":
                while True:
                    device_type = await asyncio.to_thread(
                        input,
                        "Em qual tipo de dispositivo você mexeu? [STICK/BEAM] > "
                    )

                    device_type = device_type.strip().upper()

                    if device_type in ("STICK", "BEAM"):
                        break

                    print("Digite STICK ou BEAM.")

                action = await asyncio.to_thread(
                    input,
                    "O que você mexeu nele? > "
                )

                log("")
                log("=== AÇÃO DO USUÁRIO ===")
                log(f"TIPO: {device_type}")
                log(f"AÇÃO: {action}")
                log(f"PACOTE ANTERIOR: {old_data}")
                log(f"PACOTE NOVO:      {new_data}")
                log("")

            elif choice == "2":
                log("")
                log("=== EVENTO SEM AÇÃO DO USUÁRIO ===")
                log("MOTIVO: BLE mudou, mas o usuário não mexeu em nada.")
                log(f"PACOTE ANTERIOR: {old_data}")
                log(f"PACOTE NOVO:      {new_data}")
                log("")

            else:
                log("")
                log("=== EVENTO IGNORADO ===")
                log("")

            log("=" * 60)
            log("VOLTANDO AO MONITORAMENTO...")
            log("")

    async def delayed_document(device, uuid, old_data, new_data):
        await asyncio.sleep(CHANGE_WAIT)

        key = (device.address, uuid)

        if pending_changes.get(key) != new_data:
            return

        pending_changes.pop(key, None)

        await document_change(
            device,
            uuid,
            old_data,
            new_data
        )

    def callback(sender, data, device):
        uuid = str(sender)
        hex_data = data.hex(" ")
        key = (device.address, uuid)

        previous = last_data.get(key)

        if previous is None:
            last_data[key] = hex_data

            now = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            log(
                f"[{now}] "
                f"[{get_device_type(device)}] "
                f"PRIMEIRO PACOTE {uuid}: "
                f"{hex_data}"
            )

            return

        if previous == hex_data:
            return

        last_data[key] = hex_data
        pending_changes[key] = hex_data

        asyncio.create_task(
            delayed_document(
                device,
                uuid,
                previous,
                hex_data
            )
        )

    try:
        # Conecta UMA VEZ em cada dispositivo.
        for device in selected_devices:
            device_type = get_device_type(device)

            log(
                f"Conectando {device_type}: "
                f"{device.address}"
            )

            client = BleakClient(device)

            await client.connect()

            clients.append((device, client))

            log(
                f"CONNECTED {device_type}: "
                f"{device.address}"
            )

        log("")
        log("=== DISPOSITIVOS CONECTADOS ===")
        log("")

        # Procura as características de NOTIFY de cada dispositivo.
        for device, client in clients:
            device_type = get_device_type(device)

            for service in client.services:
                for char in service.characteristics:

                    if "notify" not in char.properties:
                        continue

                    if char.uuid.lower() not in {
                        uuid.lower()
                        for uuid in NOTIFY_UUIDS
                    }:
                        continue

                    log(
                        f"MONITORANDO "
                        f"{device_type} "
                        f"{device.address} -> "
                        f"{char.uuid}"
                    )

                    callback_for_device = (
                        lambda sender, data, device=device:
                        callback(sender, data, device)
                    )

                    await client.start_notify(
                        char.uuid,
                        callback_for_device
                    )

        log("")
        log("=" * 60)
        log("MONITORAMENTO INICIADO")
        log("=" * 60)
        log("")
        log("O programa está capturando BLE.")
        log("Quando detectar uma mudança, ele perguntará")
        log("se você fez alguma alteração.")
        log("")
        log("Digite ENTER para continuar.")
        log("Digite 'sair' para encerrar.")
        log("")

        while True:
            command = await asyncio.to_thread(
                input,
                "> "
            )

            if command.lower() == "sair":
                break

    except Exception as error:
        log("")
        log("=== ERRO ===")
        log(f"{type(error).__name__}: {error}")

    finally:
        log("")
        log("=== ENCERRANDO ===")

        for device, client in clients:
            try:
                await client.disconnect()
                log(
                    f"Disconnected "
                    f"{get_device_type(device)}: "
                    f"{device.address}"
                )
            except Exception:
                pass

    print("\nCaptura salva em:")
    print(output)


asyncio.run(main())