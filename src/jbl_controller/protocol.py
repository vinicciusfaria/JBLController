from typing import List, Dict, Any, Tuple
from .exceptions import ProtocolError

# Constants
HEADER_IDENTIFIER = 0xAA
PAYLOAD_START_BYTE = 0x00

CMD_SET_LIGHT_INFO = 0x33
CMD_SET_DEV_INFO = 0x13
CMD_REQ_LIGHT_INFO = 0x31
CMD_REQ_DEV_INFO = 0x11
CMD_REQ_BATTERY = 0x9D

NOTIFY_LIGHT_INFO = 0x32
NOTIFY_DEV_INFO = 0x12
NOTIFY_BATTERY = 0x9E

# Field IDs for AA 33 / AA 32
FIELD_PATTERN = 0x31
FIELD_COLOR = 0x32
FIELD_LOOPING = 0x36
FIELD_BRIGHTNESS = 0x45
FIELD_SPEED = 0x46
FIELD_BACKLIGHT = 0x49
FIELD_SUPPORTED_PATTERNS = 0x4A

# Field IDs for AA 13 / AA 12
FIELD_SOUND_DETECTION = 0x45

def build_command(command_id: int, fields_payload: bytes) -> bytes:
    """
    Builds the complete GATT packet.
    Format: [AA] [Command ID] [Payload Length] [00] [Fields...]
    """
    if len(fields_payload) > 250:
        raise ProtocolError("Payload too large")
        
    payload_length = 1 + len(fields_payload) # 1 is for the 0x00 byte
    return bytes([HEADER_IDENTIFIER, command_id, payload_length, PAYLOAD_START_BYTE]) + fields_payload

def build_field(field_id: int, value: bytes) -> bytes:
    """Builds a single field: [Field ID] [Length] [Value...]"""
    return bytes([field_id, len(value)]) + value

def build_set_light_info(fields: List[Tuple[int, bytes]]) -> bytes:
    """Builds an AA 33 ReqSetLightInfo command with one or more fields."""
    payload = b"".join(build_field(f_id, f_val) for f_id, f_val in fields)
    return build_command(CMD_SET_LIGHT_INFO, payload)

def build_set_dev_info(fields: List[Tuple[int, bytes]]) -> bytes:
    """Builds an AA 13 ReqSetDevInfo command with one or more fields."""
    payload = b"".join(build_field(f_id, f_val) for f_id, f_val in fields)
    return build_command(CMD_SET_DEV_INFO, payload)

def parse_notification(data: bytes) -> Tuple[int, Dict[int, bytes]]:
    """
    Parses a notification packet.
    Returns (command_id, {field_id: field_value})
    """
    if len(data) < 4:
        raise ProtocolError("Packet too short")
        
    if data[0] != HEADER_IDENTIFIER:
        raise ProtocolError(f"Invalid identifier: {data[0]:02x}")
        
    command_id = data[1]
    payload_length = data[2]
    
    if len(data) < 3 + payload_length:
        raise ProtocolError("Incomplete packet based on payload length")
        
    if data[3] != PAYLOAD_START_BYTE:
        raise ProtocolError(f"Invalid payload start byte: {data[3]:02x}")
        
    fields = {}
    idx = 4
    end_idx = 3 + payload_length
    
    while idx < end_idx:
        if idx + 1 >= end_idx:
            break # Malformed tail
            
        field_id = data[idx]
        field_len = data[idx+1]
        
        if idx + 2 + field_len > end_idx:
            break # Malformed length
            
        field_val = data[idx+2 : idx+2+field_len]
        fields[field_id] = field_val
        idx += 2 + field_len
        
    return command_id, fields

