import asyncio
import os
import tempfile
import unittest
from jbl_controller.faria_db import FariaDB
from jbl_controller.playback import VirtualDJSource
from jbl_controller.faria_engine import FariaEngine
from jbl_controller.controller import ControllerState
from jbl_controller.stage import Stage


class DummyController(ControllerState):
    def __init__(self):
        self.stage = Stage([])
        self.triggered = []
        self.is_blackout = False
        self.on_update_callback = None
        
    async def apply_preset(self, preset: str):
        self.triggered.append(preset)


class TestFariaEngine(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_faria.db")
            
        self.db = FariaDB(self.db_path)
        self.controller = DummyController()
        self.playback = VirtualDJSource()
        self.engine = FariaEngine(self.db, self.controller, self.playback)
        
        self.playback.filename = "Track1.mp3"
        self.playback.position = 0
        self.playback.playing = False
        self.engine.start()
        await asyncio.sleep(0.05)

    async def asyncTearDown(self):
        self.engine.stop()
        await asyncio.sleep(0.05)
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    async def test_cue_trigger_and_debounce(self):
        self.engine.db.add_event(self.engine.current_track_id, 64000, "DROP")
        self.engine.refresh_events()
        
        self.engine.follow_cues = True
        self.playback.position = 63900
        self.playback.playing = True
        await asyncio.sleep(0.3)
        self.assertIn("DROP", self.controller.triggered)
        self.controller.triggered.clear()
        
        # Should not fire again on steady play
        await asyncio.sleep(0.2)
        self.assertEqual(len(self.controller.triggered), 0)

    async def test_rewind_cross_again(self):
        self.engine.db.add_event(self.engine.current_track_id, 64000, "DROP")
        self.engine.refresh_events()
        self.engine.follow_cues = True
        self.playback.position = 63900
        self.playback.playing = True
        await asyncio.sleep(0.3)
        self.controller.triggered.clear()
        
        # Rewind
        self.playback.position = 63900
        await asyncio.sleep(0.3)
        self.assertIn("DROP", self.controller.triggered)

    async def test_follow_cues_disabled(self):
        self.engine.db.add_event(self.engine.current_track_id, 64000, "DROP")
        self.engine.refresh_events()
        self.engine.follow_cues = False
        self.playback.position = 63900
        self.playback.playing = True
        await asyncio.sleep(0.3)
        self.assertEqual(len(self.controller.triggered), 0)

    async def test_latency_compensation(self):
        self.engine.db.add_event(self.engine.current_track_id, 64000, "DROP")
        self.engine.refresh_events()
        self.engine.follow_cues = True
        self.engine.latency_compensation_ms = 40
        self.playback.position = 63900
        self.playback.playing = True
        await asyncio.sleep(0.2)
        self.assertIn("DROP", self.controller.triggered)

    async def test_rename_track_and_alias(self):
        self.engine.db.add_event(self.engine.current_track_id, 64000, "DROP")
        self.engine.refresh_events()
        
        self.db.rename_track(self.engine.current_track_id, "Track1_Renamed.mp3")
        self.playback.filename = "Track1_Renamed.mp3"
        await asyncio.sleep(0.1)
        self.assertEqual(len(self.engine.events), 1)
        
        # Old alias should resolve
        self.playback.filename = "Track1.mp3"
        await asyncio.sleep(0.1)
        self.assertEqual(len(self.engine.events), 1)

    async def test_seek_forward_jump(self):
        self.playback.position = 0
        self.db.add_event(self.engine.current_track_id, 10000, "BUILD")
        self.engine.refresh_events()
        self.playback.position = 60000
        await asyncio.sleep(0.2)
        self.assertNotIn("BUILD", self.controller.triggered)


if __name__ == "__main__":
    unittest.main()
