from typing import Union
from fastapi import FastAPI , Request
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import json

app=FastAPI()


@app.get('/')
async def root():
    return{"message":"iha sunucusu oluşturuldu"}

@app.get("/item/{item_id}")
async def read_item(item_id:int,q:Union[str,None]=None):
    return {"item_id":item_id,"q":q}


@app.post("/telemetry")
async def receive_telemetry(request:Request):
    global telemetry_data
    telemetry_data=await request.json()
    print(f"telemetry verileri{telemetry_data}")
    return{"status":"success","message":"veri alındı"}

async def stream_telemetry():
    while True:
        yield json.loads(telemetry_data)
        await asyncio.sleep(1)

@app.get("/telemetry")
async def get_telemetry():
    telemetry_str=json.dumps(telemetry_data, indent=40)
    html_content=""" 
    <html>
    <head>
        <title> İHA Telemetri </title>
        <meta http-equiv="refresh" content="1">
    <head>
    <body>
        <h1>İHA Telemetri Verileri</h1>
        <pre>%s</pre>    
    <body>
    <html>
    """ % telemetry_str

    return HTMLResponse(content=html_content,media_type="text/html")

@app.post("/boundary_controller")
async def receive_boundary_control(request:Request):
    global count_data
    count_data = await request.json()
    print(f"boundary verileri{count_data}")
    return{"status":"success","message":"veri alındı"}

async def stream_boundary_control():
    while True:
        yield json.loads(count_data)
        await asyncio.sleep(1)

@app.get("/boundary_controller")
async def boundry_check():
    count_str=json.dumps(count_data,indent=4)
    html_content_border=""" 
    <html>
    <head>
        <title> İHA border cross verileri </title>
        <meta http-equiv="refresh" content="1">
    <head>
    <body>
        <h1>İHA border cross Verileri</h1>
        <pre> %s </pre>
    <body>
    <html>
    """ % count_str

    return HTMLResponse(content=html_content_border,media_type="text/html")
 

if __name__=="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)

#uvicorn test_server:app --reload
#uvicorn test_server:app --host 0.0.0.0 --port 8000 --reload
#python HTTP_veri_aktarımı.py
#sim_vehicle.py -v ArduPlane --console --map
