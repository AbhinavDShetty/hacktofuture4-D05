import requests

API_KEY = "b501a18f1b0a4f11bdbb9c5bfbf96a93.ZrhKkIXatraUjYBLO8rUvcgP"
headers = {"Authorization": f"Bearer {API_KEY}"}
payload = {
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "Hello"}]
}

resp = requests.post("https://open.bigmodel.cn/api/paas/v4/chat/completions", headers=headers, json=payload)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text}")

payload_glm4 = {"model": "glm-4", "messages": [{"role": "user", "content": "Hello"}]}
resp_glm4 = requests.post("https://open.bigmodel.cn/api/paas/v4/chat/completions", headers=headers, json=payload_glm4)
print(f"GLM-4 Status Code: {resp_glm4.status_code}")
print(f"GLM-4 Response: {resp_glm4.text}")
