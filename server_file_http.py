#veri doğrulama yapıyor

from typing import Union
from fastapi import FastAPI , Request
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import json
from datetime import datetime,timezone
from jsonschema import validate
from jsonschema.exceptions import ValidationError

app=FastAPI()

utc_now=datetime.now(timezone.utc)
server_clock={
    "saat":utc_now.strftime("%H"),
    "dakika":utc_now.strftime("%M"),
    "saniye":utc_now.strftime("%S"),
    "milisaniye":utc_now.strftime("%f")[:3]

}
server_str=json.dumps(server_clock)

schema={ "type": "object", 
                  "properties":{
                      "takim_numarasi":{
                          "type":"integer"
                      },
                      "iha_enlem":{
                          "type":"number"
                      },
                      "iha_boylam":{
                          "type":"number"
                      },
                      "iha_irtifa":{
                          "type":"number"
                      },
                      "iha_dikilme":{
                          "type":"number"
                      },
                      "iha_yonelme":{
                          "type":"number"
                      },
                      "iha_yatis":{
                          "type":"number"
                      },
                      "iha_hiz":{
                          "type":"number"
                      },
                      "iha_batarya":{
                          "type":"number"
                      },
                      "iha_otonom": {
                          "type":"integer"
                      },
                      "gps_saati":{
                          "type":"object",
                          "proporties":{
                              "saat":{"type":"integer"},
                              "dakika":{"type":"integer"},
                              "saniye":{"type":"integer"},
                              "milisaniye":{"type":"integer"}
                          },
                          "required":["saat","dakika","saniye","milisaniye"]
                          
                      }
                      
                  },
                  "required":["takim_numarasi","iha_enlem","iha_boylam","iha_irtifa","iha_dikilme"
                              ,"iha_yonelme" ,"iha_batarya","iha_yatis","iha_hiz",
                              "iha_otonom","gps_saati"
                  ]
}

schema2={
    "type":"object",
    "properties":{
        "cross altitude border":{
            "type":"integer"
        },
        "cross longtitude border":{
            "type":"integer"
        },
        "cross latitude border":{
            "type":"integer"
        }
    },
    "requied":["cross altitude border","cross longtitude border","cross latitude border"]
}

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
    print("gelen veri tipi:",type(telemetry_data))
    print(f"telemetry verileri{telemetry_data}")
    
    if isinstance(telemetry_data,str):
        telemetry_data=json.loads(telemetry_data)
    
    try:
        validate(telemetry_data,schema=schema)
        return  telemetry_data
    except ValidationError as e:
        print(f"invalid : {e}") 
        
async def stream_telemetry():
    while True:
        yield json.loads(telemetry_data)
        await asyncio.sleep(1)

@app.get("/telemetry")
async def get_telemetry():
    #telemetry_str=json.dumps(telemetry_data, indent=4)
    html_content=""" 
    <html>
    <head>
        <title> İHA Telemetri </title>
        <meta http-equiv="refresh" content="1">
    <head>
    <body>
        <h1>İHA Telemetri Verileri</h1>
        <pre>%s <br> Sunucu Saati: %s </pre>    
    <body>
    <html>
    """ % (telemetry_data ,server_str)


    return HTMLResponse(content=html_content,media_type="text/html")

@app.post("/boundary_controller")
async def receive_boundary_control(request:Request):
    global count_data
    count_data = await request.json()
    print(f"boundary verileri{count_data}")

    if isinstance(count_data,str):
        count_data=json.loads(count_data)
    
    try:
        validate(count_data,schema=schema2)
        return  count_data
    except ValidationError as e:
        print(f"invalid : {e}") 


async def stream_boundary_control():
    while True:
        yield json.loads(count_data)
        await asyncio.sleep(1)

@app.get("/boundary_controller")
async def boundry_check():
    #count_str=json.dumps(count_data,indent=4)
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
    """ % count_data

    return HTMLResponse(content=html_content_border,media_type="text/html")
 

if __name__=="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)

#uvicorn test_server:app --reload
#uvicorn test_server:app --host 0.0.0.0 --port 8000 --reload
#python HTTP_veri_aktarımı.py
#sim_vehicle.py -v ArduPlane --console --map

#ıp->192.168.1.115/24
