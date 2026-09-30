import asyncio
import logging
from .visko_db import ViskoDB
from .playback import PlaybackSource
from .controller import ControllerState

class ViskoEngine:
    def __init__(self, db: ViskoDB, controller: ControllerState, playback: PlaybackSource):
        self.db = db
        self.controller = controller
        self.playback = playback
        
        self.follow_cues = True
        self.latency_compensation_ms = 0
        
        self.current_track_id = -1
        self.current_filename = ""
        self.events = []
        
        self.last_position = 0
        self.was_playing = False
        self._running = False
        self._task = None

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._scheduler_loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _scheduler_loop(self):
        while self._running:
            await asyncio.sleep(0.02) # ~50 Hz check
            

            try:
                filename = self.playback.get_current_track()
                position = self.playback.get_position_ms()
                is_playing = self.playback.is_playing()
                
                if filename != self.current_filename:
                    self.current_filename = filename
                    if filename:
                        self.current_track_id = self.db.get_or_create_track(filename)
                        self.events = self.db.get_events(self.current_track_id)
                        
                        if getattr(self, "random_color_on_track_change", False):
                            import random
                            vibrant_colors = [
                                (255, 0, 0),    # Red
                                (0, 255, 0),    # Green
                                (0, 0, 255),    # Blue
                                (255, 255, 0),  # Yellow
                                (255, 0, 255),  # Magenta
                                (0, 255, 255),  # Cyan
                                (255, 60, 0),   # Orange Fuego
                                (128, 0, 255),  # Purple
                                (255, 0, 128),  # Pink
                                (0, 255, 128)   # Spring Green
                            ]
                            c = random.choice(vibrant_colors)
                            asyncio.create_task(self.controller.set_color(c[0], c[1], c[2]))
                            
                    else:
                        self.current_track_id = -1
                        self.events = []
                    self.last_position = position
                    self.was_playing = is_playing
                    
                    if is_playing and self.follow_cues and self.events:
                        self._sync_to_current_position(position)
                    continue
                
                if not is_playing or not self.follow_cues or not self.events:
                    self.last_position = position
                    self.was_playing = is_playing
                    continue
                
                if not self.was_playing or abs(position - self.last_position) > 1000 or position < self.last_position:
                    self._sync_to_current_position(position)
                else:
                    for ev in self.events:
                        if not ev["enabled"]:
                            continue
                        trigger_time = ev["time_ms"] - self.latency_compensation_ms
                        if self.last_position <= trigger_time <= position:
                            preset = ev["preset"]
                            asyncio.create_task(self._trigger_preset(preset))
                            
                self.last_position = position
                self.was_playing = is_playing

            except Exception as e:
                logging.error(f"VISKO Scheduler Error: {e}")
                await asyncio.sleep(1.0) # Backoff on error


    def _sync_to_current_position(self, current_pos):
        if not self.events:
            return
            
        # Encontra o ultimo evento antes da posicao atual
        best_event = None
        for ev in self.events:
            if not ev["enabled"]:
                continue
            if ev["time_ms"] <= current_pos:
                if best_event is None or ev["time_ms"] > best_event["time_ms"]:
                    best_event = ev
                    
        if best_event:
            logging.debug(f"[VISKO FX] Sincronizando com tempo atual (Seek/Play): {best_event['preset']}")
            asyncio.create_task(self._trigger_preset(best_event["preset"]))

    async def _trigger_preset(self, preset: str):
        logging.debug(f"[VISKO FX] Triggering '{preset}'!")
        try:
            if preset.startswith("{"):
                import json
                data = json.loads(preset)
                if "color" in data:
                    c = data["color"]
                    await self.controller.set_color(c[0], c[1], c[2])
                if "stick" in data:
                    await self.controller.set_stick_effect(data["stick"])
                if "beam" in data:
                    await self.controller.set_beam_effect(data["beam"])
                return

            # We map specific hardcoded presets to controller methods where needed, 
            # or dynamically via apply_preset if they match.
            if preset.upper() == "BLACKOUT":
                if not self.controller.is_blackout:
                    await self.controller.toggle_blackout()
            elif preset.upper() == "FUEGO":
                await self.controller.fuego()
            elif preset.upper() == "STROBO":
                await self.controller.strobo()
            elif preset.upper() == "RED":
                await self.controller.set_color(255, 0, 0)
                await self.controller.solid_color()
            elif preset.upper() == "GREEN":
                await self.controller.set_color(0, 255, 0)
                await self.controller.solid_color()
            elif preset.upper() == "BLUE":
                await self.controller.set_color(0, 0, 255)
                await self.controller.solid_color()
            else:
                await self.controller.apply_preset(preset)
        except Exception as e:
            logging.error(f"VISKO Trigger Error for preset '{preset}': {e}")
            
    def refresh_events(self):
        """Called by UI when an event is added/edited to reload current track's events."""
        if self.current_track_id != -1:
            self.events = self.db.get_events(self.current_track_id)

