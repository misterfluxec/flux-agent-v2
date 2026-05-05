import requests

url = "http://localhost:9000/api/v1/ingest/start"
files = {'archivo': ('test.csv', 'nombre,precio\nitem1,10\n', 'text/csv')}
headers = {}

# We need a valid token to test, or we can test without it to see if we get 401
response = requests.post(url, files=files, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.text)
