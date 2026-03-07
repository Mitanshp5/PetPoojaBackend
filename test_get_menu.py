import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

data = {
    "message": {
        "type": "tool-calls",
        "toolWithToolCallList": [
            {
                "toolCall": {
                    "id": "call_abc123",
                    "function": {
                        "name": "get_menu",
                        "arguments": "{}"
                    }
                }
            }
        ]
    }
}

req = urllib.request.Request(
    'http://localhost:8000/voice/vapi/webhook', 
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    response = urllib.request.urlopen(req, context=ctx)
    print(response.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
