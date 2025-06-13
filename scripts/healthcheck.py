import os
import http.client
import sys

port = os.environ.get("PORT", 8080)
try:
    connection = http.client.HTTPConnection('localhost', port, timeout=3)
    connection.request("GET", "/livez")
    sys.exit(connection.getresponse().status == 200)
except Exception as e:
    print(f"Healthcheck failed: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    if connection:
        connection.close()
