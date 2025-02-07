import asyncio
import websockets
import json
from pymavlink import mavutil
import math

async def websocket_connection():
    try:
        print("websocket bağlantısı kuruluyor..")
        websocket=await websockets.connect("ws://127.0.0.1:8000/ws")
        print("bağlantı başarılı")
        return websocket
    except Exception as e:
        print(f"bağlantı başarsız, hata oluştu {e}")
        return None



async def send_telemetry(websocket_function):

    print("mavlink bağlantısı kuruluyor")
    master=mavutil.mavlink_connection('udp:127.0.0.1:14550')
    master.wait_heartbeat()
    print("mavlink bağlantısı  kuruldu")

    #async with websocket_function as websocket:
    while True:
            
            print("döngüye girildi")
            msg=master.recv_match(type='GLOBAL_POSITION_INT',blocking=True)
            print("msg değerlerine erişildi")
            msg2=master.recv_match(type='BATTERY_STATUS',blocking=True)
            print("msg2 değerlerine erişildi")
            msg3=master.recv_match(type='HEARTBEAT',blocking=True)
            print("msg3 değerlerine erişildi")
            #msg4=master.recv_match(type='ATİTUDE',blocking=True)
            #print("tüm verilere ulaşıldı")

            if msg and msg2 and msg3 :
                print("veriler alındı")
                latitude=msg.lat/1e7
                altitude=msg.alt/1000
                longtitude=msg.lon/1e7
                heading=msg.hdg/100
                x_speed=msg.vx
                y_speed=msg.vy
                z_speed=msg.vz
                #pitch=msg4.pitch
                remain_battery=msg2.battery_remaining
                battery_tempreture=msg2.temperature
                flight_mode=msg3.custom_mode
                telemetry_data={

                    "type":"telemetry",
                    "latitude":latitude,
                    "altitude":altitude,
                    "longtitude":longtitude,
                    "heading":heading,
                    "speed":math.sqrt((x_speed*x_speed)+(y_speed*y_speed)+(z_speed*z_speed)),
                    #"pitch":pitch,
                    "remain_battery":remain_battery,
                    "battery_tempreture":battery_tempreture,
                    "flight_mode":flight_mode
                }
                
                await boundry_controller(websocket_function,telemetry_data,altitude_baundry=20,latitude_baundry=45,longtitude_boundry=60)

                try:
                    await websocket_function.send(json.dumps(telemetry_data))
                    print(f"gönderilen veriler:{telemetry_data}")
        
                except Exception as e:
                    print(f"veri gönderilirken hata oluştur:{e}")
                
                try:
                    responce=await websocket_function.recv()
                    print(f"sunucudan gelen cevap:{responce}")
                except Exception as e:
                    print(f"yanıt alınırken hata oluştu:{e}")
            
                else:
                    break
                

            await asyncio.sleep(1)

    

async def boundry_controller(websocket_function,telemetry_data,altitude_baundry,latitude_baundry,longtitude_boundry):

    count_of_crossing_the_altitude_border=0
    count_of_crossing_the_longtitude_border=0
    count_of_crossing_the_latitude_border=0

    #async with websocket_function as websocket:
        #while True:
            
    if telemetry_data["altitude"] < altitude_baundry:    
        count_of_crossing_the_altitude_border+=1
    elif telemetry_data["longtitude"] > longtitude_boundry:
        count_of_crossing_the_longtitude_border+=1
    elif telemetry_data["latitude"] > latitude_baundry:
        count_of_crossing_the_latitude_border+=1
    count_data=json.dumps({

        "type":"border_cross_count",
        "cross altitude border":count_of_crossing_the_altitude_border,
        "cross longtitude border":count_of_crossing_the_longtitude_border,
        "cross latitude border":count_of_crossing_the_latitude_border

    })
    try:        
        await websocket_function.send(count_data)
        print(f"gönderilen veriler:{count_data}")
    except Exception as e:
        print(f"veri gönderilirken hata oluştur:{e}")
                
    try:
        responce=await websocket_function.recv()
        print(f"sunucudan gelen cevap:{responce}")
    except Exception as e:
        print(f"yanıt alınırken hata oluştu:{e}")
                

    await asyncio.sleep(1)


async def main():

    websocket_function=await websocket_connection()

   
    await send_telemetry(websocket_function)
        

asyncio.run(main())


#uvicorn test_server:app --reload
#python iha_sunucu_bağlantısı.py
#sim_vehicle.py -v ArduPlane --console --map  (sıtl)
