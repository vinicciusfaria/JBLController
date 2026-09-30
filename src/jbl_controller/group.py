import asyncio
from typing import List
from .partylight import PartyLight

class PartyLightGroup:
    def __init__(self, devices: List[PartyLight]):
        self.devices = devices

    async def connect_all(self):
        await asyncio.gather(*(device.connect() for device in self.devices))

    async def disconnect_all(self):
        await asyncio.gather(*(device.disconnect() for device in self.devices))

    async def set_brightness(self, level: int):
        await asyncio.gather(*(device.set_brightness(level) for device in self.devices))

    async def set_color(self, r: int, g: int, b: int):
        await asyncio.gather(*(device.set_color(r, g, b) for device in self.devices))

    async def set_effect(self, pattern_name: str):
        # We allow partial success. If a device doesn't support it, it raises UnsupportedFeatureError.
        # asyncio.gather with return_exceptions=True prevents one device from failing the whole group.
        results = await asyncio.gather(*(device.set_effect(pattern_name) for device in self.devices), return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                # Optionally log or re-raise
                pass

    async def set_solid_color(self, r: int, g: int, b: int):
        results = await asyncio.gather(*(device.set_solid_color(r, g, b) for device in self.devices), return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                pass

    async def set_speed(self, level: int):
        await asyncio.gather(*(device.set_speed(level) for device in self.devices))

    async def set_backlight(self, on: bool):
        await asyncio.gather(*(device.set_backlight(on) for device in self.devices))

    async def set_sound_reactive(self, on: bool):
        await asyncio.gather(*(device.set_sound_reactive(on) for device in self.devices))

