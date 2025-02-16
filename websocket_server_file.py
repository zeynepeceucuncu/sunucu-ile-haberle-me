from typing import Union
from fastapi import FastAPI , WebSocket
import json
import uvicorn
import asyncio
#import subprocess

app=FastAPI()
telemetry_data={}
count_data={}
time_data={}

@app.get('/')
async def root():
    return{"message":"iha sunucusu oluşturuldu"}

@app.get("/item/{item_id}")
async def read_item(item_id:int,q:Union[str,None]=None):
    return {"item_id":item_id,"q":q}

@app.get("/telemetry")
async def get_telemetry():
    return response_telemetry

@app.get("/boundry_controller")
async def boundry_check():
    return response_count


@app.websocket("/ws")
async def websocket_endpoint(websocket:WebSocket):
    
    await websocket.accept()
    print("iha bağlantı kuruldu")


    while True:
        data=await websocket.receive_text()
        print(f"ihadan gelen veri:{data}")
        try:
            parsed_data=json.loads(data)
            data_type=parsed_data.get("type")
            if data_type == "telemetry":
                telemetry_data.update(parsed_data)
                global response_telemetry
                response_telemetry = json.dumps(telemetry_data)
                await websocket.send_text(f"alındı:{response_telemetry}")
            elif data_type == "border_cross_count":
                count_data.update(parsed_data)
                global response_count 
                response_count = json.dumps(count_data)
                await websocket.send_text(f"alındı:{response_count}")
            elif data_type =="border_cross_timer":
                time_data.update(parsed_data)
                global response_time
                response_time = json.dumps(time_data)
                await websocket.send_text(f"alındı:{response_time}")
            asyncio.create_task(send_periodic_data(websocket))
           
        except json.JSONDecodeError:
            print("Hatalı Json Formatı")
            await websocket.send_text("hatalı json formatı")
            
async def send_periodic_data(websocket:WebSocket): 
    while True: 

        await websocket.send_text(f"telemetry:{response_telemetry}")  
        await websocket.send_text(f"count:{response_count}")
        await websocket.send_text(f"time:{response_time}")

        await asyncio.sleep(1)



if __name__=="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)
    #sunucuya başka cihazlardan bağlantı sağlanabilmesi için
    #host="0.0.0.0",sunucunun tüm ağ arayüzlerini dinlemesini sağlar
    #bağlanacak cihazlar aynı wi-fi ya da eternet ağı içerisindeyse yerel ıp adresi ile bağlanabiliyorlar
    
