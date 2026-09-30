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
    def update_from_udp(self, track_path: str, pos_ms: int, playing: bool, bpm: float = 0, length_ms: int = 0, deck: int = 1, vol: float = 0, cross_result: float = 1.0, pitch: float = 0.0, eq_low_1: float = 0.5, eq_low_2: float = 0.5, hr1: int = 0, hr2: int = 0, filter_1: float = 0.5, beat_pos: float = 0.0):
        basename = os.path.basename(track_path) if track_path else ""
        if beat_pos == 0.0 and pos_ms > 0 and bpm > 0:
            beat_pos = (pos_ms / 60000.0) * bpm
        needs_sync = False
        
        # O VirtualDJ agora manda o "crossfader_result" que já faz toda a conta!
        # Se for > 0.1, a música está audível na master.
        # Lógica inteligente de Master Deck com Histerese (anti-flicker) no centro (0.5)
        is_master_deck = (basename == self._filename and basename != "")
        is_new_track = (basename != self._filename and basename != "")
        master = False
        


        if is_new_track and playing and vol > 0.1:
            can_take_over = False
            
            # 1. Se puxou o crossfader pro lado dele, ele rouba na hora
            if deck == 1 and cross_result < 0.5:
                can_take_over = True
            elif deck == 2 and cross_result > 0.5:
                can_take_over = True
                
            # 2. Se tá no meio (entre 0.4 e 0.6), a troca de graves domina!
            elif 0.4 <= cross_result <= 0.6:
                other_deck = 2 if deck == 1 else 1
                my_eq = eq_low_1 if deck == 1 else eq_low_2
                other_eq = eq_low_2 if deck == 1 else eq_low_1
                
                logging.debug(f"[VDJ EQ] Deck {deck} (eq={my_eq:.2f}) vs Deck {other_deck} (eq={other_eq:.2f})")
                
                # Se o meu grave for visivelmente maior que o do outro (ex: 0.5 contra 0.2)
                if my_eq > (other_eq + 0.1):
                    can_take_over = True
                elif not self._playing or self._filename == "":
                    can_take_over = True

            if can_take_over:
                # # print(f"Master Deck Alterado para Deck {deck}: {basename}")
                self._filename = basename
                master = True
                needs_sync = True
        elif is_master_deck:
            # Se é o pacote do deck que já é master, ele continua sendo master
            master = True

        # Ignora tudo que não for master (ex: decks vazios ou decks tocando mutados)
        if not master:
            return

        if playing:
            if not self._playing:
                needs_sync = True
                if basename != "":
                    pass  # print(f"Play Detectado: {basename} ({pos_ms}ms, BPM={bpm}, Pitch={pitch})")
            
            if abs(self.get_position_ms() - pos_ms) > 500:
                needs_sync = True
                
            if abs(self.bpm - bpm) > 0.1:
                needs_sync = True
                
            if abs(self.pitch - pitch) > 0.01:
                needs_sync = True
                
            self._filename = basename
            self._position = pos_ms
            self._beat_pos = beat_pos
            self._playing = True
            self.bpm = bpm
            self.pitch = pitch
            self.length_ms = length_ms
            self._last_play_time = time.time()
        else:
            if self._playing:
                needs_sync = True
            if abs(self._position - pos_ms) > 500:
                needs_sync = True
                
            self._filename = basename
            self._position = pos_ms
            self._beat_pos = beat_pos
            self._playing = False
            self.bpm = bpm
            self.pitch = pitch
            self.length_ms = length_ms
                
        self._last_udp_update = time.time()
        
        if time.time() - getattr(self, "_last_sync_time", 0) > 1.0:
            needs_sync = True
            
        if needs_sync and self.on_sync_callback:
            self._last_sync_time = time.time()
            asyncio.create_task(self.on_sync_callback())

    # --- Mock Overrides (Called by UI) ---
    @property
    def filename(self):
        return self._filename
        
    @filename.setter
    def filename(self, val):
        self._filename = val
        
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
                payload.get("beat", 0.0)
            )
        except Exception as e:
            logging.error(f"Erro UDP VDJ: {e} - Dados recebidos: {data}")
