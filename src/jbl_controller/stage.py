import asyncio
from typing import List, Tuple
from .partylight import PartyLight
from .group import PartyLightGroup
from .exceptions import UnsupportedFeatureError
from .patterns import Pattern

class Stage(PartyLightGroup):
    """
    An orchestrated group of PartyLights capable of applying high-level artistic presets.
    Inherits all basic group controls from PartyLightGroup.
    """

    async def _apply_to_device(
        self,
        device: PartyLight,
        brightness: int,
        speed: int,
        color: Tuple[int, int, int],
        primary_effect: str,
        fallback_effect: str = None
    ):
        """Helper to safely apply a full configuration to a single device."""
        await device.set_brightness(brightness)
        await device.set_speed(speed)
        await device.set_color(*color)
        
        try:
            await device.set_effect(primary_effect)
        except UnsupportedFeatureError:
            if fallback_effect:
                try:
                    await device.set_effect(fallback_effect)
                except UnsupportedFeatureError:
                    pass

    async def warmup(self):
        """
        Soft lighting, elegant warm/purple colors, low speed.
        Suitable for the beginning of a set.
        """
        color = (128, 0, 255) # Elegant Purple
        brightness = 40
        speed = 20
        # LOOP is universally supported by Stick and Beam
        coros = [self._apply_to_device(d, brightness, speed, color, "LOOP") for d in self.devices]
        await asyncio.gather(*coros)

    async def build(self):
        """
        Increasing energy, intense colors, moderate-high speed.
        """
        color = (0, 100, 255) # Intense Blue
        brightness = 75
        speed = 60
        # BOUNCE is universally supported
        coros = [self._apply_to_device(d, brightness, speed, color, "BOUNCE", fallback_effect="NEON") for d in self.devices]
        await asyncio.gather(*coros)

    async def drop(self):
        """
        Aggressive lighting, max brightness, strong colors, high speed.
        """
        color = (255, 0, 0) # Strong Red
        brightness = 100
        speed = 100
        # ROCK for Stick, NEON for Beam
        coros = [self._apply_to_device(d, brightness, speed, color, "ROCK", fallback_effect="NEON") for d in self.devices]
        await asyncio.gather(*coros)

    async def break_(self):
        """
        Reduced energy, cleaner/calm visual.
        """
        color = (0, 255, 100) # Mint Green
        brightness = 30
        speed = 10
        # FREEZE is universally supported
        coros = [self._apply_to_device(d, brightness, speed, color, "FREEZE") for d in self.devices]
        await asyncio.gather(*coros)

    async def calm(self):
        """
        Sophisticated/conceptual atmosphere, slow movement. (VISKO CALMDWN universe)
        """
        color = (50, 0, 100) # Deep Purple
        brightness = 40
        speed = 5
        coros = [self._apply_to_device(d, brightness, speed, color, "FREEZE", fallback_effect="LOOP") for d in self.devices]
        await asyncio.gather(*coros)

    async def rave(self):
        """
        Energetic visual, fast effects. (VISKO NEWVERSE universe)
        """
        color = (255, 0, 255) # Magenta
        brightness = 100
        speed = 90
        # NEON is universally supported and very dynamic on the Beam
        coros = [self._apply_to_device(d, brightness, speed, color, "NEON") for d in self.devices]
        await asyncio.gather(*coros)

    async def fuego(self):
        """
        Special preset: Creates a fire effect.
        Hardware-aware:
        - STICK: Uses CAMPFIRE (0x19).
        - BEAM: Uses NEON/LOOP with orange/red colors since CAMPFIRE is unsupported.
        """
        color = (255, 60, 0) # Fire Orange
        brightness = 100
        speed = 50 # Fire shouldn't be too fast (not a strobe)

        async def _apply_fuego(device: PartyLight):
            await device.set_brightness(brightness)
            await device.set_speed(speed)
            await device.set_color(*color)
            
            # Check if CAMPFIRE is supported natively
            if Pattern.CAMPFIRE.value in device.supported_patterns:
                await device.set_effect("CAMPFIRE")
            else:
                # Fallback for Beam
                # Use a moving effect like NEON or LOOP which it supports
                if Pattern.NEON.value in device.supported_patterns:
                    await device.set_effect("NEON")
                elif Pattern.LOOP.value in device.supported_patterns:
                    await device.set_effect("LOOP")

        await asyncio.gather(*(_apply_fuego(d) for d in self.devices))

