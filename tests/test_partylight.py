import unittest
import asyncio
from unittest.mock import AsyncMock, patch
from jbl_controller.partylight import PartyLight
from jbl_controller.exceptions import InvalidValueError, UnsupportedFeatureError
from jbl_controller.patterns import Pattern

class TestPartyLight(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.pl = PartyLight("00:11:22:33:44:55")
        self.pl.client = AsyncMock()
        self.pl.client.write_gatt_char = AsyncMock()
        self.pl.supported_patterns = [Pattern.NEON.value, Pattern.LOOP.value]
        self.pl._capabilities_fetched.set()

    async def test_set_brightness_valid(self):
        await self.pl.set_brightness(50)
        self.pl.client.write_gatt_char.assert_called_once()
        args, kwargs = self.pl.client.write_gatt_char.call_args
        self.assertEqual(args[1], bytes([0xAA, 0x33, 0x04, 0x00, 0x45, 0x01, 50]))

    async def test_set_brightness_invalid(self):
        with self.assertRaises(InvalidValueError):
            await self.pl.set_brightness(101)

    async def test_set_color_valid(self):
        await self.pl.set_color(255, 128, 0)
        self.pl.client.write_gatt_char.assert_called_once()
        args, kwargs = self.pl.client.write_gatt_char.call_args
        self.assertEqual(args[1], bytes([0xAA, 0x33, 0x06, 0x00, 0x32, 0x03, 0xFF, 0x80, 0x00]))

    async def test_set_effect_supported(self):
        await self.pl.set_effect("NEON")
        self.pl.client.write_gatt_char.assert_called_once()

    async def test_set_effect_unsupported(self):
        with self.assertRaises(UnsupportedFeatureError):
            await self.pl.set_effect("STATIC")

    async def test_set_solid_color_unsupported(self):
        with self.assertRaises(UnsupportedFeatureError):
            await self.pl.set_solid_color(255, 0, 0)

    async def test_set_solid_color_supported(self):
        self.pl.supported_patterns.append(Pattern.STATIC.value)
        await self.pl.set_solid_color(255, 0, 0)
        self.pl.client.write_gatt_char.assert_called_once()
        args, kwargs = self.pl.client.write_gatt_char.call_args
        expected = bytes([0xAA, 0x33, 0x0C, 0x00, 0x31, 0x01, 0x15, 0x32, 0x03, 0xFF, 0x00, 0x00, 0x36, 0x01, 0x01])
        self.assertEqual(args[1], expected)

if __name__ == "__main__":
    unittest.main()

