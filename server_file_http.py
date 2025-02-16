from typing import Union
from fastapi import FastAPI , Request
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio
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


@app.post("/telemetry")
async def receive_telemetry(request:Request):
    telemetry_data=await request.json()
    print(f"telemetry verileri{telemetry_data}")
    return{"status":"success","message":"veri alındı"}

async def stream_telemetry():
    while True:
        yield json.dumps(telemetry_data)
        await asyncio.sleep(1)

@app.get("/telemetry")
async def get_telemetry():
 
    return StreamingResponse(stream_telemetry(),media_type='application/json')
  
@app.post("/boundary_controller")
async def receive_boundary_control(request:Request):
    count_data = await request.json()
    print(f"boundary verileri{count_data}")
    return{"status":"success","message":"veri alındı"}

async def stream_boundary_control():
    while True:
        yield json.dumps(count_data)
        await asyncio.sleep(1)

@app.get("/boundary_controller")
async def boundry_check():

    return StreamingResponse(stream_boundary_control(),media_type='application/json')
    

if __name__=="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)

#uvicorn test_server:app --reload
#python HTTP_veri_aktarımı.py
