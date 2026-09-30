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

    async def test_fader_transition_takes_over_master(self):
        # Deck 1 starts playing with fader 1.0
        self.playback.update_from_udp("SongA.mp3", 1000, True, 128.0, 180000, deck=1, vol=1.0, cross_result=0.5)
        self.assertEqual(self.playback.current_master_deck, 1)
        self.assertEqual(self.playback.get_current_track(), "SongA.mp3")

        # Deck 2 starts playing with fader 0.0 (crossfader still in middle 0.5)
        self.playback.update_from_udp("SongB.mp3", 500, True, 130.0, 200000, deck=2, vol=0.0, cross_result=0.5)
        self.assertEqual(self.playback.current_master_deck, 1)
        self.assertEqual(self.playback.get_current_track(), "SongA.mp3")

        # DJ lowers Deck 1 fader to 0.1 and raises Deck 2 fader to 0.9 (without touching crossfader!)
        self.playback.update_from_udp("SongA.mp3", 2000, True, 128.0, 180000, deck=1, vol=0.1, cross_result=0.5)
        self.playback.update_from_udp("SongB.mp3", 1500, True, 130.0, 200000, deck=2, vol=0.9, cross_result=0.5)
        
        # Deck 2 must be the new master!
        self.assertEqual(self.playback.current_master_deck, 2)
        self.assertEqual(self.playback.get_current_track(), "SongB.mp3")

    async def test_bass_swap_takes_over_master(self):
        # Both decks playing with faders at 1.0, crossfader centered
        self.playback.update_from_udp("SongA.mp3", 5000, True, 128.0, 180000, deck=1, vol=1.0, cross_result=0.5, eq_low_1=0.5, eq_low_2=0.5)
        self.playback.update_from_udp("SongB.mp3", 5000, True, 128.0, 180000, deck=2, vol=1.0, cross_result=0.5, eq_low_1=0.5, eq_low_2=0.5)
        self.assertEqual(self.playback.current_master_deck, 1)

        # DJ cuts bass on Deck 1 and boosts bass on Deck 2
        self.playback.update_from_udp("SongB.mp3", 6000, True, 128.0, 180000, deck=2, vol=1.0, cross_result=0.5, eq_low_1=0.2, eq_low_2=0.6)
        self.assertEqual(self.playback.current_master_deck, 2)
        self.assertEqual(self.playback.get_current_track(), "SongB.mp3")

    async def test_crossfader_cut_takes_over_master(self):
        # Deck 1 is master
        self.playback.update_from_udp("SongA.mp3", 1000, True, 128.0, 180000, deck=1, vol=1.0, cross_result=0.2)
        self.assertEqual(self.playback.current_master_deck, 1)

        # DJ cuts crossfader to Deck 2 (0.8)
        self.playback.update_from_udp("SongB.mp3", 1000, True, 128.0, 180000, deck=2, vol=1.0, cross_result=0.8)
        self.assertEqual(self.playback.current_master_deck, 2)
        self.assertEqual(self.playback.get_current_track(), "SongB.mp3")


if __name__ == "__main__":
    unittest.main()
