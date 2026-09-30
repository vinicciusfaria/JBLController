import asyncio
import logging
from typing import List, Optional, Dict
from bleak import BleakClient

from .exceptions import ConnectionError, UnsupportedFeatureError, InvalidValueError, ProtocolError
from .patterns import Pattern, PATTERN_NAMES
from . import protocol

WRITE_UUID = "65786365-6c70-6f69-6e74-2e636f6d0002"
NOTIFY_UUID = "65786365-6c70-6f69-6e74-2e636f6d0001"

class PartyLight:
    def __init__(self, address: str, name: str = "PartyLight"):
        self.address = address
        self.name = name
        self.client: Optional[BleakClient] = None
        self.current_state: Dict[int, bytes] = {}
        self.supported_patterns: List[int] = []
        self._capabilities_fetched = asyncio.Event()
        self.on_state_change = None

    async def _send_packet(self, packet: bytes):
        if self.client and self.client.is_connected:
            try:
                await self.client.write_gatt_char(WRITE_UUID, packet, response=False)
            except Exception as e:
                logging.error(f"Erro de BLE na caixa {self.name}: {e}")

    async def connect(self):
        """Connects to the PartyLight and initializes state."""
        if self.client and self.client.is_connected:
            return
            
        self.client = BleakClient(self.address, disconnected_callback=self._handle_disconnect)
        try:
            await self.client.connect()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.address}: {e}")

        await self.client.start_notify(NOTIFY_UUID, self._notification_handler)
        await self.refresh_state()
        
        # Wait until we receive the AA 32 packet with supported patterns
        try:
            await asyncio.wait_for(self._capabilities_fetched.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            pass # Continue even if we didn't get capabilities, though we might fail later

    def _handle_disconnect(self, client):
        logging.warning(f"Conexao perdida com {self.name} ({self.address}). Tentando reconectar...")
        if self.on_state_change:
            self.on_state_change(self, {})
        # Spawn a reconnect loop in the current running event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._reconnect_loop())
        except RuntimeError:
            pass
            
    async def _reconnect_loop(self):
        while not (self.client and self.client.is_connected):
            await asyncio.sleep(5)
            logging.info(f"Tentando reconectar {self.name}...")
            try:
                await self.connect()
                logging.info(f"{self.name} reconectada com sucesso!")
                if self.on_state_change:
                    self.on_state_change(self, {})
                break
            except Exception as e:
                pass # Silent fail, will retry in 5s

    async def disconnect(self):
        """Disconnects from the device intentionally without auto-reconnect."""
        if self.client and self.client.is_connected:
            # Remove callback to prevent auto-reconnect loop on intentional disconnect
            self.client.set_disconnected_callback(None)
            await self.client.stop_notify(NOTIFY_UUID)
            await self.client.disconnect()

    def _notification_handler(self, sender, data: bytearray):
        """Handles incoming GATT notifications."""
        try:
            command_id, fields = protocol.parse_notification(bytes(data))
            if command_id == protocol.NOTIFY_LIGHT_INFO:
                self.current_state.update(fields)
                if protocol.FIELD_SUPPORTED_PATTERNS in fields:
                    self.supported_patterns = list(fields[protocol.FIELD_SUPPORTED_PATTERNS])
                    self._capabilities_fetched.set()
                if self.on_state_change:
                    self.on_state_change(self, fields)
        except ProtocolError:
            pass # Ignore malformed packets

    async def refresh_state(self):
        """Explicitly requests the device to send its current state."""
        if not self.client or not self.client.is_connected:
            raise ConnectionError("Not connected")
        # Send AA 31 00
        cmd = protocol.build_command(protocol.CMD_REQ_LIGHT_INFO, b"")
        await self._send_packet(cmd)

    async def get_supported_effects(self) -> List[str]:
        """Returns a list of supported effect names."""
        if not self._capabilities_fetched.is_set():
            await self.refresh_state()
            try:
                await asyncio.wait_for(self._capabilities_fetched.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                return []
        
        return [PATTERN_NAMES.get(p_id, f"UNKNOWN_{p_id}") for p_id in self.supported_patterns]

    async def get_battery_level(self) -> int:
        """Requests and returns the battery level."""
        # Polling AA 9D
        cmd = protocol.build_command(protocol.CMD_REQ_BATTERY, b"")
        await self._send_packet(cmd)
        # Note: In a fully complete implementation, we'd wait for AA 9E notification.
        # For this initial API, we'll return a stub or raise NotImplementedError for the wait logic.
        # Let's keep it simple:
        raise NotImplementedError("Waiting for battery response is not fully implemented yet.")

    def _check_pattern_support(self, pattern_id: int):
        if self.supported_patterns and pattern_id not in self.supported_patterns:
            name = PATTERN_NAMES.get(pattern_id, str(pattern_id))
            raise UnsupportedFeatureError(f"Pattern '{name}' is not supported by this device.")

    async def set_brightness(self, level: int):
        if not 0 <= level <= 100:
            raise InvalidValueError("Brightness must be between 0 and 100.")
        packet = protocol.build_set_light_info([(protocol.FIELD_BRIGHTNESS, bytes([level]))])
        await self._send_packet(packet)

    async def set_color(self, r: int, g: int, b: int):
        if any(not 0 <= val <= 255 for val in (r, g, b)):
            raise InvalidValueError("RGB values must be between 0 and 255.")
        packet = protocol.build_set_light_info([(protocol.FIELD_COLOR, bytes([r, g, b]))])
        await self._send_packet(packet)

    async def set_effect(self, pattern_name: str):
        pattern_name = pattern_name.upper()
        # Find ID from name
        pattern_id = None
        for pid, name in PATTERN_NAMES.items():
            if name == pattern_name:
                pattern_id = pid
                break
                
        if pattern_id is None:
            raise InvalidValueError(f"Unknown pattern: {pattern_name}")
            
        self._check_pattern_support(pattern_id)
        packet = protocol.build_set_light_info([(protocol.FIELD_PATTERN, bytes([pattern_id]))])
        await self._send_packet(packet)

    async def set_solid_color(self, r: int, g: int, b: int):
        if any(not 0 <= val <= 255 for val in (r, g, b)):
            raise InvalidValueError("RGB values must be between 0 and 255.")
            
        self._check_pattern_support(Pattern.STATIC.value)
        
        # Compound packet: Pattern STATIC + Color + PatternLooping STATIC_COLOR
        fields = [
            (protocol.FIELD_PATTERN, bytes([Pattern.STATIC.value])),
            (protocol.FIELD_COLOR, bytes([r, g, b])),
            (protocol.FIELD_LOOPING, bytes([0x01]))
        ]
        packet = protocol.build_set_light_info(fields)
        await self._send_packet(packet)

    async def set_speed(self, level: int):
        if not 0 <= level <= 100:
            raise InvalidValueError("Speed must be between 0 and 100.")
        packet = protocol.build_set_light_info([(protocol.FIELD_SPEED, bytes([level]))])
        await self._send_packet(packet)

    async def set_backlight(self, on: bool):
        val = 0x01 if on else 0x00
        packet = protocol.build_set_light_info([(protocol.FIELD_BACKLIGHT, bytes([val]))])
        await self._send_packet(packet)

    async def set_sound_reactive(self, on: bool):
        val = 0x01 if on else 0x00
        packet = protocol.build_set_dev_info([(protocol.FIELD_SOUND_DETECTION, bytes([val]))])
        await self._send_packet(packet)


