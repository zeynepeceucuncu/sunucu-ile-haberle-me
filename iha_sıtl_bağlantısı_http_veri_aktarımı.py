#veri doğrulama yapıyor
#http
import asyncio
import json
from pymavlink import mavutil
import math
import httpx
import datetime


async def send_data_to_server(altitude_baundary,latitude_baundary,longtitude_boundary):

    print("mavlink bağlantısı kuruluyor")
    master=mavutil.mavlink_connection('udp:127.0.0.1:14550')
    master.wait_heartbeat()
    print("mavlink bağlantısı  kuruldu")
    
    async with httpx.AsyncClient() as client:
        while True:
            
            print("döngüye girildi")
            msg=master.recv_match(type='GLOBAL_POSITION_INT',blocking=True)
            print("msg değerlerine erişildi")
            msg2=master.recv_match(type='BATTERY_STATUS',blocking=True)
            print("msg2 değerlerine erişildi")
            msg3=master.recv_match(type='HEARTBEAT',blocking=True)
            print("msg3 değerlerine erişildi")
            msg4=master.recv_match(type='ATTITUDE',blocking=True)
            print("msg4 değerlerine erişildi")
            msg5=master.recv_match(type='GPS_RAW_INT',blocking=True)
            print("msg5 değerlerine erişildi")
            #msg6=master.recv_match(type='VISION_POSITION_ESTIMATE',blocking=True)
            #print("msg6 değerlerine erişildi")
            #msg7=master.recv_match(type='MISSION_ITEM',blocking=True)
            #print("msg7 değerlerine erişildi")
            
            if msg and msg2 and msg3 and msg4 and msg5  :#and msg6 and msg7
                print("veriler alındı")
                latitude=msg.lat/1e7
                altitude=msg.alt/1000
                longtitude=msg.lon/1e7
                #heading=msg.hdg/100 #iha'nın burnunun yöneldiği pusula açısı
                x_speed=msg.vx
                y_speed=msg.vy
                z_speed=msg.vz
                iha_dikilme=msg4.pitch
                iha_yönelme=msg4.yaw
                iha_yatiş=msg4.roll
                remain_battery=msg2.battery_remaining
                flight_mode=msg3.custom_mode
                
                #hedef_merkez_x=msg6.x
                #hedef_merkez_y=msg6.y
                #hedef_genişlik=msg6.covariance[0]
                #hedef_yüksekliği=msg6.covariance[4]
               
                #if msg7.command == mavutil.mavlink.MAV_CMD_NAV_FOLLOW:
                    #iha_kilitlenme=1
                #else:
                    #iha_kilitlenme=0
                     
                
                time=msg5.time_usec #mikrosaniye cinsinden zamanı elde ederiz
                total_second=time/1000000
                millisecond=time/1000
                gps_saati={
                    "saat":total_second/3600,
                    "dakika":total_second/60,
                    "saniye":total_second,
                    "milisaniye":millisecond
                }


                telemetry_data={
                    "type":"telemetry",
                    "takim_numarasi":12345,
                    "iha_enlem":latitude,
                    "iha_boylam":longtitude,
                    "iha_irtifa":altitude,
                    #"heading":heading,
                    "iha_dikilme":iha_dikilme,
                    "iha_yonelme":iha_yönelme,
                    "iha_yatis":iha_yatiş,
                    "iha_hiz":math.sqrt((x_speed*x_speed)+(y_speed*y_speed)+(z_speed*z_speed)),
                    "iha_batarya":remain_battery,
                    "iha_otonom":flight_mode,
                    #"iha_kilitlenme":iha_kilitlenme,
                    #"hedef_merkez_x":hedef_merkez_x,
                    #"hedef_merkez_y":hedef_merkez_y,
                    #"hedef_genişlik":hedef_genişlik,
                    #"hedef_yüksekliği":hedef_yüksekliği,
                    "gps_saati":gps_saati

                }
                count_of_crossing_the_altitude_border=0
                count_of_crossing_the_longtitude_border=0
                count_of_crossing_the_latitude_border=0
                if telemetry_data["iha_enlem"]>latitude_baundary:
                    count_of_crossing_the_latitude_border+=1
                elif telemetry_data["iha_boylam"] > longtitude_boundary:
                    count_of_crossing_the_longtitude_border+=1
                elif telemetry_data["iha_irtifa"] < altitude_baundary:    
                    count_of_crossing_the_altitude_border+=1
                
                count_data={

                    "type":"border_cross_count",
                    "cross altitude border":count_of_crossing_the_altitude_border,
                    "cross longtitude border":count_of_crossing_the_longtitude_border,
                    "cross latitude border":count_of_crossing_the_latitude_border

                }
                updated_count_data=json.dumps(count_data)
                updated_telemetry_data=json.dumps(telemetry_data)

                try:
                    data=await client.post('http://127.0.0.1:8000/telemetry',json=updated_telemetry_data)
                    data2=await client.post('http://127.0.0.1:8000/boundary_controller',json=updated_count_data)
                    print(f"telemetry verileri gönderildi:{data.json()} ")
                    print(f"sınır kontrol verileri gönderildi:{data2.json()} ")
                except Exception as e:
                    print(f"http isteği başarısız oldu:{e}")

            else:
                break
            
            await asyncio.sleep(1) 


async def main():

    await send_data_to_server(20,50,70)
        

asyncio.run(main())


    await send_data_to_server(20,50,70)
        

asyncio.run(main())
