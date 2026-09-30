from enum import IntEnum

class Pattern(IntEnum):
    """Enumeration of all known patterns based on the APK's PLLightInfo.Pattern enum."""
    OFF = 0x00
    ROCK = 0x01
    NEON = 0x02
    CLUB = 0x03
    FLOW = 0x04
    RIPPLE = 0x05
    CROSS = 0x06
    FLASH = 0x07
    RANDOM = 0x08
    LOOP = 0x09
    BOUNCE = 0x0A
    TRIM = 0x0B
    SWITCH = 0x0C
    FREEZE = 0x0D
    OCEAN = 0x10
    AURORA = 0x11
    BLOSSOM = 0x12
    SUNRISE = 0x13
    FIREPLACE = 0x14
    STATIC = 0x15
    GRAVITY = 0x16
    LIGHTNING = 0x17
    GLITCH = 0x18
    CAMPFIRE = 0x19
    UNIVERSE = 0x1A
    FIREFLY = 0x1B
    BEER = 0x1F
    STORM = 0x20
    HOVER = 0x21
    SKY = 0x22

# Lookup table to map an ID back to its string name
PATTERN_NAMES = {pattern.value: pattern.name for pattern in Pattern}

