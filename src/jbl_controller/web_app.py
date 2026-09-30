import os
from aiohttp import web
import json
import asyncio
import logging
from .controller import ControllerState
from .faria_db import FariaDB
from .playback import VirtualDJSource
from .faria_engine import FariaEngine

class WebApp:
    def __init__(self, controller: ControllerState):
        self.controller = controller
        
        # FARIA Initialization
        self.faria_db = FariaDB()
        self.visko_db = self.faria_db  # Compatibility alias
        self.playback = VirtualDJSource()
        self.faria = FariaEngine(self.faria_db, self.controller, self.playback)
        self.visko = self.faria  # Compatibility alias
        self.playback.on_sync_callback = self.broadcast_state
        
        self.app = web.Application()
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/ws', self.handle_ws)
        
        # Start background tasks when the event loop is ready
        self.app.on_startup.append(self.start_background_tasks)
        
    async def start_background_tasks(self, app):
        self.faria.start()
        asyncio.create_task(self.playback.start_udp_server())
        
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        os.makedirs(static_dir, exist_ok=True)
        self.app.router.add_static('/static', static_dir)
        
        self.websockets = set()
        self.controller.on_update_callback = self.broadcast_state
        
    async def handle_index(self, request):
        index_path = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
        return web.FileResponse(index_path)

    def get_full_state(self):
        state = self.controller.get_state_dict()
        faria_state = {
            "follow_cues": self.faria.follow_cues,
            "random_on": getattr(self.faria, "random_color_on_track_change", False),
            "latency_ms": self.faria.latency_compensation_ms,
            "track": self.playback.get_current_track(),
            "position": self.playback.get_position_ms(),
            "beat_pos": self.playback.get_position_beats(),
            "is_playing": self.playback.is_playing(),
            "bpm": getattr(self.playback, "bpm", 0),
            "pitch": getattr(self.playback, "pitch", 0.0),
            "length_ms": getattr(self.playback, "length_ms", 0),
            "events": self.faria.events
        }
        state["faria"] = faria_state
        state["visko"] = faria_state  # Compatibility
        return state

    async def broadcast_state(self):
        msg = json.dumps({"type": "state", "state": self.get_full_state()})
        for ws in set(self.websockets):
            try:
                await ws.send_str(msg)
            except:
                self.websockets.discard(ws)

    async def handle_ws(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)
        
        # Send initial state
        await ws.send_str(json.dumps({"type": "state", "state": self.get_full_state()}))
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if not isinstance(data, dict):
                            continue
                            
                        cmd = data.get("action")
                        
                        if cmd == "set_color":
                            color = data.get("color")
                            if isinstance(color, list) and len(color) == 3:
                                r, g, b = [int(c) for c in color]
                                await self.controller.set_color(r, g, b)
                        elif cmd == "set_stick_effect":
                            await self.controller.set_stick_effect(str(data.get("effect", "")))
                        elif cmd == "set_beam_effect":
                            await self.controller.set_beam_effect(str(data.get("effect", "")))
                        elif cmd == "set_brightness":
                            await self.controller.set_brightness(int(data.get("level", 0)))
                        elif cmd == "set_speed":
                            await self.controller.set_speed(int(data.get("level", 0)))
                        elif cmd == "add_color":
                            color = data.get("color")
                            if isinstance(color, list) and len(color) == 3:
                                r, g, b = [int(c) for c in color]
                                self.controller.add_color_to_queue(r, g, b)
                        elif cmd == "remove_color_idx":
                            self.controller.remove_color_at_index(int(data.get("index", -1)))
                        elif cmd == "next_color":
                            await self.controller.next_color()
                        elif cmd == "start_set":
                            asyncio.create_task(self.controller.start_set())
                        elif cmd == "end_set":
                            asyncio.create_task(self.controller.end_set())
                        elif cmd == "preset":
                            await self.controller.apply_preset(str(data.get("preset", "")))
                        elif cmd == "solid":
                            await self.controller.solid_color()
                        elif cmd == "add_event":
                            track = self.playback.get_current_track()
                            if track:
                                pos = data.get("time_ms")
                                beat = data.get("beat_pos")
                                if pos is None:
                                    pos = self.playback.get_position_ms()
                                if beat is None:
                                    beat = self.playback.get_position_beats()
                                preset = data.get("preset", "strobe")
                                track_id = self.faria_db.get_or_create_track(track)
                                self.faria_db.add_event(track_id, int(pos), float(beat), preset)
                                self.faria.refresh_events()
                                await self.broadcast_state()
                        elif cmd == "edit_event":
                            event_id = data.get("id")
                            time_ms = data.get("time_ms")
                            beat_pos = data.get("beat_pos")
                            preset = data.get("preset")
                            if event_id is not None and time_ms is not None and beat_pos is not None and preset is not None:
                                self.faria_db.update_event(int(event_id), int(time_ms), float(beat_pos), preset)
                                self.faria.refresh_events()
                                await self.broadcast_state()
                        elif cmd == "remove_event":
                            event_id = data.get("event_id")
                            if event_id is not None:
                                self.faria_db.delete_event(int(event_id))
                                self.faria.refresh_events()
                                await self.broadcast_state()
                        elif cmd == "blackout":
                            await self.controller.toggle_blackout()
                        elif cmd == "fuego":
                            await self.controller.fuego()
                        elif cmd == "strobo":
                            await self.controller.strobo()
                        elif cmd == "backlight":
                            await self.controller.toggle_backlight()
                        elif cmd == "sound_reactive":
                            await self.controller.toggle_sound_reactive()
                        elif cmd == "rescan_devices":
                            asyncio.create_task(self.controller.rescan_devices())
                            
                        # FARIA Commands
                        elif cmd in ("faria_set_follow", "visko_set_follow"):
                            self.faria.follow_cues = bool(data.get("value"))
                        elif cmd in ("faria_set_random", "visko_set_random"):
                            self.faria.random_color_on_track_change = bool(data.get("value"))
                        elif cmd in ("faria_set_latency", "visko_set_latency"):
                            self.faria.latency_compensation_ms = int(data.get("value", 0))
                        elif cmd in ("faria_add_event", "visko_add_event"):
                            self.faria.db.add_event(self.faria.current_track_id, int(data["time_ms"]), float(data.get("beat_pos", 0.0)), str(data["preset"]))
                            self.faria.refresh_events()
                        elif cmd in ("faria_update_event", "visko_update_event"):
                            self.faria.db.update_event(int(data["id"]), int(data["time_ms"]), float(data.get("beat_pos", 0.0)), str(data["preset"]), bool(data["enabled"]))
                            self.faria.refresh_events()
                        elif cmd in ("faria_delete_event", "visko_delete_event"):
                            self.faria.db.delete_event(int(data["id"]))
                            self.faria.refresh_events()
                        elif cmd in ("faria_rename_track", "visko_rename_track"):
                            self.faria.db.rename_track(self.faria.current_track_id, str(data["new_name"]))
                            self.faria.current_filename = str(data["new_name"])
                            
                        # Mock Playback Commands (for UI testing)
                        elif cmd == "mock_set_track":
                            self.playback.filename = str(data.get("track", ""))
                            self.playback.position = 0
                            self.playback.playing = False
                        elif cmd == "mock_set_position":
                            self.playback.position = int(data.get("position", 0))
                        elif cmd == "mock_play_pause":
                            self.playback.playing = not self.playback.playing
                            
                        await self.broadcast_state()
                    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
                        # Catch malformed data or invalid types and ignore them
                        pass
        finally:
            self.websockets.discard(ws)
        
        return ws

    async def cleanup_background_tasks(self, app):
        pass

    def get_app(self):
        return self.app

def run_app(controller: ControllerState, port=8080):
    webapp = WebApp(controller)
    webapp.app.on_cleanup.append(webapp.cleanup_background_tasks)
    web.run_app(webapp.app, port=port)

