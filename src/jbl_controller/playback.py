import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod

class PlaybackSource(ABC):
    @abstractmethod
    def get_current_track(self) -> str:
        """Returns the current filename/track string."""
        pass
        
    @abstractmethod
    def get_position_ms(self) -> int:
        """Returns the current playback position in milliseconds."""
        pass
        
    @abstractmethod
    def get_position_beats(self) -> float:
        """Returns the current playback position in beats."""
        pass
        
    @abstractmethod
    def is_playing(self) -> bool:
        """Returns True if music is actively playing."""
        pass


class VirtualDJSource(PlaybackSource):
    """
    Receives UDP packets from the C++ VirtualDJ Plugin.
    Also acts as a Mock if VirtualDJ is closed, allowing the Web UI to override its state.
    """
    def __init__(self):
        self._filename = ""
        self._position = 0
        self._beat_pos = 0.0
        self._playing = False
        self.bpm = 0
        self.pitch = 0.0
        self.length_ms = 0
        self.on_sync_callback = None
        
        # Dual-Deck Tracking
        self.decks = {
            1: {
                "track": "", "pos_ms": 0, "beat_pos": 0.0, "playing": False,
                "bpm": 0.0, "pitch": 0.0, "length_ms": 0, "vol": 1.0, "last_update": 0.0
            },
            2: {
                "track": "", "pos_ms": 0, "beat_pos": 0.0, "playing": False,
                "bpm": 0.0, "pitch": 0.0, "length_ms": 0, "vol": 1.0, "last_update": 0.0
            }
        }
        self.current_master_deck = 1
        self.crossfader = 0.5
        self.eq_low = {1: 0.5, 2: 0.5}

        # Internal timer for Mock behavior (when VDJ is offline)
        self._last_play_time = 0
        self._last_udp_update = 0
        self._last_sync_time = 0
        
        self.transport = None
        
    async def start_udp_server(self, host="127.0.0.1", port=9666):
        loop = asyncio.get_running_loop()
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: VDJUDPProtocol(self),
            local_addr=(host, port)
        )
        logging.info(f"VirtualDJ UDP Receiver listening on {host}:{port}")

    def stop_udp_server(self):
        if self.transport:
            self.transport.close()

    # --- UDP Update (Called by Protocol) ---
    def update_from_udp(self, track_path: str, pos_ms: int, playing: bool, bpm: float = 0, length_ms: int = 0, deck: int = 1, vol: float = 0, cross_result: float = 1.0, pitch: float = 0.0, eq_low_1: float = 0.5, eq_low_2: float = 0.5, hr1: int = 0, hr2: int = 0, filter_1: float = 0.5, filter_2: float = 0.5, beat_pos: float = 0.0, vol_1: float = None, vol_2: float = None, master_deck: int = None):
        basename = os.path.basename(track_path) if track_path else ""
        if beat_pos is None and pos_ms > 0 and bpm > 0:
            beat_pos = (pos_ms / 60000.0) * bpm
        
        if beat_pos is None:
            beat_pos = 0.0
            
        now = time.time()
        needs_sync = False
        
        # Save shared mixer states
        self.crossfader = cross_result
        self.eq_low[1] = eq_low_1
        self.eq_low[2] = eq_low_2
        
        # Identify deck (1 or 2)
        deck_idx = deck
        if deck not in (1, 2):
            if basename and basename == self.decks[1]["track"]: deck_idx = 1
            elif basename and basename == self.decks[2]["track"]: deck_idx = 2
            elif vol_1 is not None and vol_2 is not None and abs(vol - vol_1) < 0.01 and abs(vol - vol_2) > 0.01: deck_idx = 1
            elif vol_1 is not None and vol_2 is not None and abs(vol - vol_2) < 0.01 and abs(vol - vol_1) > 0.01: deck_idx = 2
            else: deck_idx = master_deck if (master_deck in (1, 2)) else self.current_master_deck

        effective_vol_1 = vol_1 if vol_1 is not None else (vol if deck_idx == 1 else self.decks[1]["vol"])
        effective_vol_2 = vol_2 if vol_2 is not None else (vol if deck_idx == 2 else self.decks[2]["vol"])

        if basename != "":
            self.decks[deck_idx]["track"] = basename
        self.decks[deck_idx]["pos_ms"] = pos_ms
        self.decks[deck_idx]["beat_pos"] = beat_pos
        self.decks[deck_idx]["playing"] = playing
        self.decks[deck_idx]["bpm"] = bpm
        self.decks[deck_idx]["pitch"] = pitch
        self.decks[deck_idx]["length_ms"] = length_ms
        self.decks[deck_idx]["last_update"] = now
        self.decks[1]["vol"] = effective_vol_1
        self.decks[2]["vol"] = effective_vol_2

        # -------------------------------------------------------------
        # INTELLIGENT MASTER DECK SELECTION
        # -------------------------------------------------------------
        d1 = self.decks[1]
        d2 = self.decks[2]
        
        d1_alive = (now - d1["last_update"]) < 3.0 and (d1["track"] != "")
        d2_alive = (now - d2["last_update"]) < 3.0 and (d2["track"] != "")
        
        p1 = d1["playing"] and d1_alive
        p2 = d2["playing"] and d2_alive
        v1 = d1["vol"]
        v2 = d2["vol"]
        cross = self.crossfader
        
        target_master = self.current_master_deck
        
        if p1 and not p2: target_master = 1
        elif p2 and not p1: target_master = 2
        elif p1 and p2:
            if self.current_master_deck == 1 and v1 < 0.15 and v2 >= 0.20: target_master = 2
            elif self.current_master_deck == 2 and v2 < 0.15 and v1 >= 0.20: target_master = 1
            elif v2 >= (v1 + 0.20): target_master = 2
            elif v1 >= (v2 + 0.20): target_master = 1
            elif v1 > 0.4 and v2 > 0.4 and cross <= 0.35: target_master = 1
            elif v1 > 0.4 and v2 > 0.4 and cross >= 0.65: target_master = 2
            elif v1 > 0.5 and v2 > 0.5 and 0.35 <= cross <= 0.65:
                eq1 = self.eq_low[1]
                eq2 = self.eq_low[2]
                if eq2 >= (eq1 + 0.15): target_master = 2
                elif eq1 >= (eq2 + 0.15): target_master = 1
            elif abs(v1 - v2) < 0.15:
                target_master = self.current_master_deck

        if target_master != self.current_master_deck:
            logging.info(f"[VDJ MASTER] Deck {self.current_master_deck} -> Deck {target_master}: {self.decks[target_master]['track']}")
            self.current_master_deck = target_master
            needs_sync = True

        active = self.decks[self.current_master_deck]
        
        # -------------------------------------------------------------
        # BASS CUT LOGIC (EQ Low + Filter High-Pass)
        # -------------------------------------------------------------
        low_val = eq_low_1 if target_master == 1 else eq_low_2
        filter_val = filter_1 if target_master == 1 else filter_2
        
        if p1 and p2 and v1 > 0.2 and v2 > 0.2 and 0.3 <= cross <= 0.7:
            # During a mix, only trigger bass cut if BOTH decks have bass cut
            eff_low_1 = min(eq_low_1, max(0.0, 1.0 - (filter_1 - 0.5) * 2.0) if filter_1 >= 0.5 else eq_low_1)
            eff_low_2 = min(eq_low_2, max(0.0, 1.0 - (filter_2 - 0.5) * 2.0) if filter_2 >= 0.5 else eq_low_2)
            actual_low = max(eff_low_1, eff_low_2)
        else:
            eff_low_filter = max(0.0, 1.0 - (filter_val - 0.5) * 2.0) if filter_val >= 0.5 else low_val
            actual_low = min(low_val, eff_low_filter)
            
        self.bass_cut = actual_low < 0.15

        if deck_idx == self.current_master_deck or needs_sync:
            old_filename = self._filename
            old_playing = self._playing
            
            self._filename = active["track"]
            self._position = active["pos_ms"]
            self._beat_pos = active["beat_pos"]
            self._playing = active["playing"]
            self.bpm = active["bpm"]
            self.pitch = active["pitch"]
            self.length_ms = active["length_ms"]
            
            if self._playing:
                self._last_play_time = now
                
            if old_filename != self._filename or old_playing != self._playing:
                needs_sync = True
                
        self._last_udp_update = now
        
        if now - getattr(self, "_last_sync_time", 0) > 1.0:
            needs_sync = True
            
        if needs_sync and self.on_sync_callback:
            self._last_sync_time = now
            asyncio.create_task(self.on_sync_callback())

    # --- Mock Overrides (Called by UI) ---
    @property
    def filename(self):
        return self._filename
        
    @filename.setter
    def filename(self, val):
        self._filename = val
        self.decks[self.current_master_deck]["track"] = val
        
    @property
    def position(self):
        # If VDJ hasn't sent data in >1.5 seconds, we assume it's offline
        # and we simulate time passing locally (Mock behavior)
        is_vdj_live = (time.time() - self._last_udp_update) < 1.5
        
        if self._playing and not is_vdj_live:
            pitch_mult = 1.0 + (self.pitch / 100.0)
            return self._position + int((time.time() - self._last_play_time) * 1000 * pitch_mult)
        return self._position
        
    @position.setter
    def position(self, val):
        self._position = val
        bpm = self.bpm if self.bpm > 0 else 120.0
        self._beat_pos = (val / 60000.0) * bpm
        self.decks[self.current_master_deck]["pos_ms"] = val
        self.decks[self.current_master_deck]["beat_pos"] = self._beat_pos
        if self._playing:
            self._last_play_time = time.time()
            
    @property
    def playing(self):
        return self._playing
        
    @playing.setter
    def playing(self, is_playing):
        if is_playing and not self._playing:
            self._last_play_time = time.time()
        elif not is_playing and self._playing:
            # We are pausing via mock, calculate final position
            is_vdj_live = (time.time() - self._last_udp_update) < 1.5
            if not is_vdj_live:
                pitch_mult = 1.0 + (self.pitch / 100.0)
                self._position += int((time.time() - self._last_play_time) * 1000 * pitch_mult)
        self._playing = is_playing
        self.decks[self.current_master_deck]["playing"] = is_playing

    # --- PlaybackSource Interface ---
    def get_current_track(self) -> str:
        return self.filename
        
    def get_position_ms(self) -> int:
        return self.position
        
    def get_position_beats(self) -> float:
        # Mock behavior for beats (interpolate based on BPM and pitch)
        is_vdj_live = (time.time() - self._last_udp_update) < 1.5
        if self._playing and not is_vdj_live:
            bpm = self.bpm if self.bpm > 0 else 120.0
            beats_per_ms = bpm / 60000.0
            return self._beat_pos + ((time.time() - self._last_play_time) * 1000 * beats_per_ms)
        return self._beat_pos
        
    def is_playing(self) -> bool:
        return self.playing


class VDJUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, source: VirtualDJSource):
        self.source = source
        
    def datagram_received(self, data, addr):
        try:
            payload = json.loads(data.decode('utf-8'))
            
            self.source.update_from_udp(
                payload.get("track", ""),
                payload.get("pos", 0),
                payload.get("play", False),
                payload.get("bpm", 0),
                payload.get("length_ms", 0),
                payload.get("deck", 1),
                payload.get("vol", 0),
                payload.get("cross_result", 1.0),
                payload.get("pitch", 0.0),
                payload.get("eq_low_1", 0.5),
                payload.get("eq_low_2", 0.5),
                payload.get("hr1", 0),
                payload.get("hr2", 0),
                payload.get("filter_1", 0.5),
                payload.get("filter_2", 0.5),
                payload.get("beat", 0.0),
                vol_1=payload.get("vol_1"),
                vol_2=payload.get("vol_2"),
                master_deck=payload.get("master_deck")
            )
        except Exception as e:
            logging.error(f"Erro UDP VDJ: {e} - Dados recebidos: {data}")
