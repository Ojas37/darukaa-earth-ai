import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def run_demonstration():
    print("=== 1. Health Check ===")
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    health_resp = client.get("/health")
    print("GET /health ->", json.dumps(health_resp.json(), indent=2))

    print("\n=== 2. Scenario A: Incomplete Query (Needs Clarification) ===")
    req_a = {
        "message": "My biodiversity is declining on my farm."
    }
    resp_a = client.post("/api/v1/chat", json=req_a)
    print("POST /api/v1/chat Request:", json.dumps(req_a, indent=2))
    print("POST /api/v1/chat Response:")
    print(json.dumps(resp_a.json(), indent=2))

    print("\n=== 3. Scenario B: Complete Multi-Variable Environmental Scenario ===")
    req_b = {
        "message": "My farm is in a semi-arid region with very little rain (approx 350mm/year). I grow only wheat in monoculture and my soil organic carbon is around 0.35%."
    }
    resp_b = client.post("/api/v1/chat", json=req_b)
    print("POST /api/v1/chat Request:", json.dumps(req_b, indent=2))
    print("POST /api/v1/chat Response:")
    print(json.dumps(resp_b.json(), indent=2))

    conv_id = resp_b.json()["conversation_id"]
    print(f"\n=== 4. Fetch Stored Environmental Profile for Session {conv_id} ===")
    env_resp = client.get(f"/api/v1/environment/{conv_id}")
    print("GET /api/v1/environment/{id} ->")
    print(json.dumps(env_resp.json(), indent=2))

if __name__ == "__main__":
    run_demonstration()
