import urllib.request
import sys

def check_health():
    try:
        res = urllib.request.urlopen("http://127.0.0.1:5001/api/spaces", timeout=3)
        if res.status == 200:
            print("SpaceLoop Health Status: HEALTHY (200 OK)")
            sys.exit(0)
    except Exception as e:
        print(f"Healthcheck failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    check_health()
