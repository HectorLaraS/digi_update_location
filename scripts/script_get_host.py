import os
from dotenv import load_dotenv
import requests
import json 
from digi import Digi
from openpyxl import Workbook


load_dotenv()

DIGI_USER = os.getenv("DIGI_USER")
DIGI_PASS = os.getenv("DIGI_PASS")
url = os.getenv("DIGI_API")
lst_digis: list[Digi] = []

headers = {
    "X-Pretty": "true",
    "content-type": "application/json"
}

try:
    
    response = requests.get(url, headers=headers, auth=(DIGI_USER, DIGI_PASS))
    if response.status_code == 200:
        digi_result = response.json()
        if "list" in digi_result and isinstance(digi_result["list"], list):
            digi_info = digi_result["list"]
            ##with open("digis.json","a", encoding="utf-8") as inv_digi_json:
                ##json.dump(digi_info, inv_digi_json, indent=4, ensure_ascii=False)
            ##for digi in digi_info:
            ##    print(type(digi))
            for digi in digi_info: 
                tmp_digi = Digi(
                    customer_id=digi.get("customer_id"),
                    d_type=digi.get("type"),
                    description=digi.get("description"),
                    ip=digi.get("ip"),
                    name=digi.get("name"),
                    location=digi.get("location"),
                )
                lst_digis.append(tmp_digi)
        else: 
            print("not working")
except Exception as e:
    print(e)



wb = Workbook()
ws = wb.active
ws.title = "Routers"
# Encabezados (nombres de las columnas)
headers = [f.name for f in Digi.__dataclass_fields__.values()]
ws.append(headers)

# Filas de datos
for digi in lst_digis:
    # Convertimos el dataclass en dict y tomamos los valores en el mismo orden de los headers
    row_data = [getattr(digi, h) for h in headers]
    ws.append(row_data)

# Guardar el archivo
wb.save("digis.xlsx")
print("Archivo digis.xlsx creado!")