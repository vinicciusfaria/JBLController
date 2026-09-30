import asyncio
from typing import List, Tuple, Optional
from .stage import Stage
from .patterns import Pattern

class ControllerState:
    def __init__(self, stage: Stage):
        self.stage = stage
        
        # Base state
        self.current_color: Tuple[int, int, int] = (255, 0, 0)
        self.stick_effect: str = "NEON"
        self.beam_effect: str = "NEON"
        self.current_brightness: int = 0
        self.current_speed: int = 50
        
        # Hardware Toggles
        self.backlight_on: bool = False
        self.sound_reactive_on: bool = False
        
        # Color Queue
        self.color_queue: List[Tuple[int, int, int]] = []
        
        self.combination_name: str = "PERSONALIZADO"
        
        # Backup state for Blackout
        self._pre_blackout_brightness = 50
        self.is_blackout = False
        
        self.on_update_callback = None
        for d in self.stage.devices:
            d.on_state_change = self._device_state_changed

    def _device_state_changed(self, device, new_fields):
        updated = False
        import jbl_controller.protocol as protocol
        if protocol.FIELD_BRIGHTNESS in new_fields:
            self.current_brightness = new_fields[protocol.FIELD_BRIGHTNESS][0]
            updated = True
        if protocol.FIELD_SPEED in new_fields:
            self.current_speed = new_fields[protocol.FIELD_SPEED][0]
            updated = True
            
        if updated and self.on_update_callback:
            asyncio.create_task(self.on_update_callback())

    async def _apply_current_state(self):
        if self.is_blackout:
            await self.stage.set_brightness(0)
            return

        coros = []
        for d in self.stage.devices:
            coros.append(d.set_brightness(self.current_brightness))
            coros.append(d.set_color(*self.current_color))
            coros.append(d.set_speed(self.current_speed))
            
            target_eff = self.stick_effect if "Stick" in d.name else self.beam_effect
            try:
                d._check_pattern_support(Pattern[target_eff].value)
                coros.append(d.set_effect(target_eff))
            except Exception:
                if Pattern.NEON.value in d.supported_patterns:
                    coros.append(d.set_effect("NEON"))
                elif Pattern.LOOP.value in d.supported_patterns:
                    coros.append(d.set_effect("LOOP"))

        await asyncio.gather(*coros, return_exceptions=True)

    async def set_color(self, r: int, g: int, b: int):
        self.current_color = (r, g, b)
        self.combination_name = "PERSONALIZADO"
        if not self.is_blackout:
            await self.stage.set_color(r, g, b)

    async def set_stick_effect(self, effect_name: str):
        self.stick_effect = effect_name
        self.combination_name = "PERSONALIZADO"
        if not self.is_blackout:
            coros = []
            for d in self.stage.devices:
                if "Stick" in d.name:
                    try:
                        d._check_pattern_support(Pattern[effect_name].value)
                        coros.append(d.set_effect(effect_name))
                    except:
                        pass
            await asyncio.gather(*coros, return_exceptions=True)
            
    async def set_beam_effect(self, effect_name: str):
        self.beam_effect = effect_name
        self.combination_name = "PERSONALIZADO"
        if not self.is_blackout:
            coros = []
            for d in self.stage.devices:
                if "Beam" in d.name:
                    try:
                        d._check_pattern_support(Pattern[effect_name].value)
                        coros.append(d.set_effect(effect_name))
                    except:
                        pass
            await asyncio.gather(*coros, return_exceptions=True)

    async def set_brightness(self, level: int):
        self.current_brightness = level
        if not self.is_blackout:
            await self.stage.set_brightness(level)

    async def set_speed(self, level: int):
        self.current_speed = level
        if not self.is_blackout:
            await self.stage.set_speed(level)

    # --- Queue Management ---
    def add_color_to_queue(self, r: int, g: int, b: int):
        if len(self.color_queue) < 50:
            self.color_queue.append((r, g, b))

    def remove_color_at_index(self, idx: int):
        if 0 <= idx < len(self.color_queue):
            self.color_queue.pop(idx)

    async def next_color(self):
        if not self.color_queue: return
        next_c = self.color_queue.pop(0)
        await self.set_color(*next_c)

    # --- Start/End Set Faders ---
    async def _fade_loop(self, target: int, step: int):
        while (step > 0 and self.current_brightness < target) or (step < 0 and self.current_brightness > target):
            self.current_brightness += step
            self.current_brightness = max(0, min(100, self.current_brightness))
            await self.stage.set_brightness(self.current_brightness)
            if self.on_update_callback:
                await self.on_update_callback()
            await asyncio.sleep(0.05)

    async def _end_set_task(self):
        await self._fade_loop(0, -2)
        self.is_blackout = True
        self.combination_name = "BLACKOUT"
        coros = []
        for d in self.stage.devices:
            if "Beam" in d.name and Pattern.LOOP.value in d.supported_patterns:
                coros.append(d.set_effect("LOOP"))
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)
        if self.on_update_callback:
            await self.on_update_callback()

    async def start_set(self):
        self.is_blackout = False
        if getattr(self, '_fade_task', None):
            self._fade_task.cancel()
        self._fade_task = asyncio.create_task(self._fade_loop(100, 2))
            
    async def end_set(self):
        if getattr(self, '_fade_task', None):
            self._fade_task.cancel()
        self._fade_task = asyncio.create_task(self._end_set_task())

    # --- Special Buttons ---
    async def toggle_blackout(self):
        if getattr(self, '_fade_task', None):
            self._fade_task.cancel()
            
        if self.is_blackout:
            self.is_blackout = False
            await self.stage.set_brightness(self.current_brightness)
            self.combination_name = "PERSONALIZADO"
            await self.set_stick_effect(self.stick_effect)
            await self.set_beam_effect(self.beam_effect)
        else:
            self.is_blackout = True
            await self.stage.set_brightness(0)
            self.combination_name = "BLACKOUT"
            coros = []
            for d in self.stage.devices:
                if "Beam" in d.name and Pattern.LOOP.value in d.supported_patterns:
                    coros.append(d.set_effect("LOOP"))
            if coros:
                await asyncio.gather(*coros, return_exceptions=True)

    async def solid_color(self):
        self.is_blackout = False
        self.combination_name = "COR SOLIDA"
        self.stick_effect = "STATIC"
        self.beam_effect = "STATIC"
        await self.set_stick_effect("STATIC")
        await self.set_beam_effect("STATIC")
        await self.set_color(*self.current_color)

    async def fuego(self):
        self.is_blackout = False
        self.combination_name = "FUEGO"
        self.current_speed = 50
        self.current_color = (255, 60, 0)
        coros = []
        for d in self.stage.devices:
            if "Beam" in d.name:
                coros.append(d.set_color(255, 0, 0))
            else:
                coros.append(d.set_color(*self.current_color))
                
            if Pattern.CAMPFIRE.value in d.supported_patterns:
                coros.append(d.set_effect("CAMPFIRE"))
                if "Stick" in d.name: self.stick_effect = "CAMPFIRE"
                else: self.beam_effect = "CAMPFIRE"
            else:
                if Pattern.NEON.value in d.supported_patterns:
                    coros.append(d.set_effect("NEON"))
                    if "Stick" in d.name: self.stick_effect = "NEON"
                    else: self.beam_effect = "NEON"
                elif Pattern.LOOP.value in d.supported_patterns:
                    coros.append(d.set_effect("LOOP"))
                    if "Stick" in d.name: self.stick_effect = "LOOP"
                    else: self.beam_effect = "LOOP"
        await asyncio.gather(*coros, return_exceptions=True)

    async def strobo(self):
        self.is_blackout = False
        self.combination_name = "STROBO"
        coros = []
        for d in self.stage.devices:
            if Pattern.FLASH.value in d.supported_patterns:
                coros.append(d.set_effect("FLASH"))
            else:
                coros.append(d.set_effect("LOOP"))
        await asyncio.gather(*coros, return_exceptions=True)

    # --- Hardware Toggles ---
    async def toggle_backlight(self):
        self.backlight_on = not self.backlight_on
        await self.stage.set_backlight(self.backlight_on)

    async def toggle_sound_reactive(self):
        self.sound_reactive_on = not self.sound_reactive_on
        await self.stage.set_sound_reactive(self.sound_reactive_on)

    # --- Standard Presets (as macros) ---
    async def apply_preset(self, preset_name: str):
        self.combination_name = preset_name.upper()
        self.is_blackout = False
        self.current_speed = 50  # Volta ao normal
        if preset_name == "warmup":
            self.current_color = (128, 0, 255)
            self.stick_effect = "LOOP"
            self.beam_effect = "LOOP"
        elif preset_name == "build":
            self.current_color = (0, 100, 255)
            self.stick_effect = "BOUNCE"
            self.beam_effect = "BOUNCE"
        elif preset_name == "drop":
            self.current_color = (255, 0, 0)
            self.stick_effect = "NEON"
            self.beam_effect = "NEON"
        elif preset_name == "break_":
            self.current_color = (0, 255, 100)
            self.stick_effect = "FREEZE"
            self.beam_effect = "FREEZE"
        elif preset_name == "calm":
            self.current_color = (50, 0, 100)
            self.stick_effect = "FREEZE"
            self.beam_effect = "FREEZE"
        elif preset_name == "rave":
            self.current_color = (255, 0, 255)
            self.stick_effect = "NEON"
            self.beam_effect = "NEON"
            
        await self.set_color(*self.current_color)
        await self.set_stick_effect(self.stick_effect)
        await self.set_beam_effect(self.beam_effect)

    async def rescan_devices(self):
        if getattr(self, "_is_rescanning", False):
            print("[RESCAN] Já existe uma busca em andamento. Ignorando...")
            return
            
        self._is_rescanning = True
        try:
            from bleak import BleakScanner
            from jbl_controller.partylight import PartyLight
            
            print("[RESCAN] Procurando novas PartyLights...")
            devices = await BleakScanner.discover(timeout=5.0)
            
            current_addresses = {d.address.upper() for d in self.stage.devices}
            new_devices = []
            
            for d in devices:
                if d.name and "PartyLight" in d.name and d.address.upper() not in current_addresses:
                    print(f"[RESCAN] Nova caixa encontrada: {d.name} ({d.address})")
                    new_light = PartyLight(d.address, name=d.name)
                    new_light.on_state_change = self._device_state_changed
                    new_devices.append(new_light)
                    
            if new_devices:
                self.stage.devices.extend(new_devices)
                for new_light in new_devices:
                    asyncio.create_task(new_light.connect())
                    
            if self.on_update_callback:
                await self.on_update_callback()
        finally:
            self._is_rescanning = False

    def get_state_dict(self):
        devices_status = []
        for d in self.stage.devices:
            is_connected = d.client.is_connected if d.client else False
            devices_status.append({"name": d.name, "connected": is_connected})
            
        return {
            "combination": self.combination_name,
            "beam_effect": self.beam_effect,
            "stick_effect": self.stick_effect,
            "color": self.current_color,
            "brightness": self.current_brightness,
            "speed": self.current_speed,
            "queue": self.color_queue,
            "blackout": self.is_blackout,
            "backlight": self.backlight_on,
            "sound_reactive": self.sound_reactive_on,
            "devices": devices_status
        }

