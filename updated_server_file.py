from typing import Union
from fastapi import FastAPI , WebSocket
import json

app=FastAPI()
telemetry_data={}
count_data={}
@app.get('/')
async def root():
    return{"message":"iha sunucusu oluşturuldu"}

@app.get("/item/{item_id}")
async def read_item(item_id:int,q:Union[str,None]=None):
    return {"item_id":item_id,"q":q}

@app.get("/telemetry")
async def get_telemetry():
    return telemetry_data

@app.get("/boundry_controller")
async def boundry_check():
    return count_data

@app.websocket("/ws")
async def websocket_endpoint(websocket:WebSocket):
    await websocket.accept()
    print("iha bağlantı kuruldu")
    while True:
        data=await websocket.receive_text()
        print(f"ihadan gelen veri:{data}")
        try:
            parsed_telemetry_data=json.loads(data)
            parsed_border_data=json.loads(data)
            if parsed_telemetry_data.get("type")=="telemetry":
                telemetry_data.update(parsed_telemetry_data)
            elif parsed_border_data.get("type")=="border_cross_count":
                count_data.update(parsed_border_data)

        except json.JSONDecodeError:
            print("Hatalı Json Formatı")
        await websocket.send_text(f"alındı:{data}")
