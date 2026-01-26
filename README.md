# İHA Telemetri Aktarım ve Doğrulama Sistemi
Bu proje, bir İnsansız Hava Aracı'ndan (İHA) alınan telemetri verilerini **MAVLink protokolü** üzerinden okuyan, sınır ihlallerini denetleyen ve bu verileri doğrulayarak bir **FastAPI** sunucusu üzerinden yayınlayan gerçek zamanlı bir veri yönetim sistemidir.

## Proje Mimarisi

Sistem iki ana modülden oluşur:

1.  **Telemetri İstemcisi:**
    * `pymavlink` kütüphanesi ile  SITL simülasyonuna bağlanır.
    * Telemetri verilerini (GPS, Batarya, Tutum, Hız) anlık olarak çeker.
    * Verileri JSON formatına çevirip HTTP POST isteği ile sunucuya gönderir.

2.  **Server:**
    * **FastAPI** altyapısı ile gelen verileri karşılar.
    * **JSON Schema** kullanarak gelen verinin tipini ve bütünlüğünü doğrular .
    * Doğrulanmış verileri basit bir HTML arayüzünde anlık olarak görselleştirir.

## Kullanılan Teknolojiler

* **Backend Framework:** Python FastAPI, Uvicorn
* **İHA Haberleşme:** Pymavlink (MAVLink Protokolü)
* **HTTP İstekleri:** Httpx (Asenkron Client)
* **Veri Doğrulama:** Jsonschema
* **Eşzamanlılık:** Python Asyncio

## Dosya Yapısı

* **`server_file_http.py`**: Telemetri verilerini alan, doğrulayan ve yayınlayan REST API sunucusu.
* **`iha_sıtl_bağlantısı.py`**: İHA'dan veriyi okumamıza ve sunucuya göndermemizi sağlayan yapı.
