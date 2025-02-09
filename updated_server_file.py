from typing import Union
from fastapi import FastAPI , WebSocket
import json
import uvicorn

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
    connected_ip=websocket.client.host
    allowed_ips=["127.0.0.1","192.168.1.105"]
    if connected_ip not in allowed_ips:
        await websocket.accept()
        print("iha bağlantı kuruldu")
        while True:
           data=await websocket.receive_text()
           print(f"ihadan gelen veri:{data}")
           try:
            parsed_telemetry_data=json.loads(data)
            parsed_border_data=json.loads(data)
            parsed_time_data=json.loads(data)
            
            if parsed_telemetry_data.get("type")=="telemetry":
                telemetry_data.update(parsed_telemetry_data)
            elif parsed_border_data.get("type")=="border_cross_count":
                count_data.update(parsed_border_data)
            elif parsed_time_data.get("type")=="border_cross_timer":
                time_data.update(parsed_time_data)
            

           except json.JSONDecodeError:
            print("Hatalı Json Formatı")
            await websocket.send_text(f"alındı:{data}")
    


if __name__=="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)
    #sunucuya başka cihazlardan bağlantı sağlanabilmesi için
    #host="0.0.0.0",sunucunun tüm ağ arayüzlerini dinlemesini sağlar
    #bağlanacak cihazlar aynı wi-fi ya da eternet ağı içerisindeyse yerel ıp adresi ile bağlanabiliyorlar
    

    
