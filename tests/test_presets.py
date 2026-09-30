import unittest
import asyncio
from unittest.mock import AsyncMock, call

from jbl_controller.partylight import PartyLight
from jbl_controller.stage import Stage
from jbl_controller.patterns import Pattern

class TestPresets(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Create a mock Stick
        self.stick = PartyLight("STICK_MAC")
        self.stick.client = AsyncMock()
        self.stick.client.write_gatt_char = AsyncMock()
        self.stick._capabilities_fetched.set()
        # Stick supports CAMPFIRE, ROCK, FREEZE, LOOP, BOUNCE
        self.stick.supported_patterns = [
            Pattern.CAMPFIRE.value, Pattern.ROCK.value,
            Pattern.FREEZE.value, Pattern.LOOP.value,
            Pattern.BOUNCE.value, Pattern.NEON.value
        ]

        # Create a mock Beam
        self.beam = PartyLight("BEAM_MAC")
        self.beam.client = AsyncMock()
        self.beam.client.write_gatt_char = AsyncMock()
        self.beam._capabilities_fetched.set()
        # Beam supports NEON, LOOP, BOUNCE, FREEZE (but NOT CAMPFIRE or ROCK)
        self.beam.supported_patterns = [
            Pattern.NEON.value, Pattern.LOOP.value,
            Pattern.BOUNCE.value, Pattern.FREEZE.value
        ]

        self.stage = Stage([self.stick, self.beam])

    async def test_fuego_preset(self):
        """Tests that fuego() sends CAMPFIRE to Stick but NEON/LOOP to Beam."""
        await self.stage.fuego()
        
        # Verify STICK received CAMPFIRE (0x19)
        stick_calls = self.stick.client.write_gatt_char.mock_calls
        stick_patterns_sent = [
            c.args[1] for c in stick_calls if b'\x31\x01\x19' in c.args[1]
        ]
        self.assertTrue(len(stick_patterns_sent) > 0, "Stick should receive CAMPFIRE")
        
        # Verify BEAM did NOT receive CAMPFIRE
        beam_calls = self.beam.client.write_gatt_char.mock_calls
        beam_campfire_sent = [
            c.args[1] for c in beam_calls if b'\x31\x01\x19' in c.args[1]
        ]
        self.assertEqual(len(beam_campfire_sent), 0, "Beam should not receive CAMPFIRE")
        
        # Verify BEAM received NEON (0x02) instead
        beam_neon_sent = [
            c.args[1] for c in beam_calls if b'\x31\x01\x02' in c.args[1]
        ]
        self.assertTrue(len(beam_neon_sent) > 0, "Beam should receive NEON as fallback for Fuego")

    async def test_drop_preset_fallback(self):
        """Tests that drop() sends ROCK to Stick and falls back to NEON on Beam."""
        await self.stage.drop()
        
        # STICK should receive ROCK (0x01)
        stick_calls = self.stick.client.write_gatt_char.mock_calls
        stick_rock = [c.args[1] for c in stick_calls if b'\x31\x01\x01' in c.args[1]]
        self.assertTrue(len(stick_rock) > 0, "Stick should receive ROCK")
        
        # BEAM should receive NEON (0x02) because it doesn't support ROCK
        beam_calls = self.beam.client.write_gatt_char.mock_calls
        beam_rock = [c.args[1] for c in beam_calls if b'\x31\x01\x01' in c.args[1]]
        self.assertEqual(len(beam_rock), 0, "Beam should not receive ROCK")
        
        beam_neon = [c.args[1] for c in beam_calls if b'\x31\x01\x02' in c.args[1]]
        self.assertTrue(len(beam_neon) > 0, "Beam should fallback to NEON")

    async def test_warmup_preset_universal(self):
        """Tests that warmup() sends LOOP universally to both."""
        await self.stage.warmup()
        
        # LOOP is 0x09
        stick_calls = self.stick.client.write_gatt_char.mock_calls
        beam_calls = self.beam.client.write_gatt_char.mock_calls
        
        self.assertTrue(any(b'\x31\x01\x09' in c.args[1] for c in stick_calls))
        self.assertTrue(any(b'\x31\x01\x09' in c.args[1] for c in beam_calls))

if __name__ == "__main__":
    unittest.main()

