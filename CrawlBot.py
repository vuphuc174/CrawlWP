import requests
import json

url = "https://ithelper.cafesua.net/wp-json/wp/v2/tags"

payload = {
  "name": "python"
}
userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
headers = {
  'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2l0aGVscGVyLmNhZmVzdWEubmV0IiwiaWF0IjoxNjY3MDA4NDc5LCJuYmYiOjE2NjcwMDg0NzksImV4cCI6MTY2NzYxMzI3OSwiZGF0YSI6eyJ1c2VyIjp7ImlkIjoiMSJ9fX0.epsPMIo6HkBKUmA8jhlxPegG78XOF9gM9Qg_F0xUIYA',
  'Content-Type': 'application/json',
  'User-Agent':userAgent
}

response = requests.request("POST", url, headers=headers, json=payload)

print(response.status_code)
