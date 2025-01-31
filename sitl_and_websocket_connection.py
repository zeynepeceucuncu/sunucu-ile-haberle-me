import asyncio
import websockets
import json
from pymavlink import mavutil

async def send_telemetry():
    print ("mavlink bağlantısı kuruluyor")
    master=mavutil.mavlink_connection('udp:127.0.0.1:14550')
    master.wait_heartbeat()
    print("mavlink bağlantısı kuruldu")

    print("websocket bağlantısı kuruluyor..")
    async with websockets.connect("ws://127.0.0.1:8000/ws") as websocket:
        print("bağlantı başarılı")

        while True:
            msg=master.recv_match(type='GLOBAL_POSITION_INT',blocking=True)
            if msg:
                print("veriler alındı")
                telemetry_data=json.dumps({
                    "latitude":msg.lat/1e7,
                    "altitude":msg.alt/1000,
                    "longtitude":msg.lon/1e7,
                    "heading":msg.hdg/100
                })
                try:
                    await websocket.send(telemetry_data)
                    print(f"gönderilen veriler:{telemetry_data}")
                except Exception as e:
                    print(f"veri gönderilirken hata oluştur:{e}")
                
                try:
                    responce=await websocket.recv()
                    print(f"sunucudan gelen cevap:{responce}")
                except Exception as e:
                    print(f"yanıt alınırken hata oluştu:{e}")
