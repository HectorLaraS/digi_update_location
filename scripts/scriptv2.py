import os
from dotenv import load_dotenv
import requests
import json 
from digi import Digi
from openpyxl import Workbook


load_dotenv()

DIGI_USER = os.getenv("DIGI_USER")
DIGI_PASS = os.getenv("DIGI_PASS")
url = os.getenv("DIGI_API_INFO")
lst_digis_to_audit: list[str] = []

with open("test_list.txt","r") as list_ips:
    for ip_add in list_ips:
        lst_digis_to_audit.append(ip_add.strip())

headers = {
    "X-Pretty": "true",
    "content-type": "application/json"
}

for digi_ip in lst_digis_to_audit:
    final_url=f"{url}'{digi_ip}'"
    try:
        response = requests.get(final_url, headers=headers, auth=(DIGI_USER, DIGI_PASS))
        print(response.json())
    except Exception as e:
        print(e)