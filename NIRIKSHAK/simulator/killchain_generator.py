import time
import uuid
import httpx
import sys

DEFAULT_API_URL = "http://localhost:8000/api/v1"


def run_staged_killchain(api_url: str = DEFAULT_API_URL, delay_seconds: float = 1.0):
    """Executes a 4-stage APT attack scenario showing progressive risk escalation."""
    print("\n" + "=" * 70)
    print("  NIRIKSHAK SIMULATOR: MULTI-STAGE KILL-CHAIN ATTACK EMULATION")
    print("=" * 70)

    stages = [
        {
            "stage": 1,
            "name": "RECONNAISSANCE",
            "desc": "Off-hours initial browse of public repository from an unlisted IP address",
            "payload": {
                "event_id": f"evt_apt_s1_{uuid.uuid4().hex[:6]}",
                "user_identifier": "USER-004",
                "device_identifier": "DEV-104",
                "resource_identifier": "Public Documentation E",
                "action": "READ",
                "result": "SUCCESS",
                "data_volume": 524288,
                "source_context": {"mfa_verified": True, "corporate_network": False, "client_ip": "198.51.100.88"},
            },
        },
        {
            "stage": 2,
            "name": "INTERNAL DIRECTORY ENUMERATION",
            "desc": "Lateral traversal across internal engineering code repositories",
            "payload": {
                "event_id": f"evt_apt_s2_{uuid.uuid4().hex[:6]}",
                "user_identifier": "USER-004",
                "device_identifier": "DEV-104",
                "resource_identifier": "Engineering Repository B",
                "action": "READ",
                "result": "SUCCESS",
                "data_volume": 2097152,
                "source_context": {"mfa_verified": True, "corporate_network": False, "client_ip": "198.51.100.88"},
            },
        },
        {
            "stage": 3,
            "name": "PRIVILEGE TRAVERSAL & BYPASS",
            "desc": "Cross-departmental access to CRITICAL defense algorithm without MFA token",
            "payload": {
                "event_id": f"evt_apt_s3_{uuid.uuid4().hex[:6]}",
                "user_identifier": "USER-004",
                "device_identifier": "DEV-104",
                "resource_identifier": "Operational Repository A",
                "action": "READ",
                "result": "SUCCESS",
                "data_volume": 8388608,
                "source_context": {"mfa_verified": False, "corporate_network": False, "client_ip": "198.51.100.88"},
            },
        },
        {
            "stage": 4,
            "name": "BULK EXFILTRATION ATTEMPT",
            "desc": "Massive 1.8 GB compressed archive export trigger",
            "payload": {
                "event_id": f"evt_apt_s4_{uuid.uuid4().hex[:6]}",
                "user_identifier": "USER-004",
                "device_identifier": "DEV-104",
                "resource_identifier": "Operational Repository A",
                "action": "EXPORT",
                "result": "SUCCESS",
                "data_volume": 1887436800,
                "source_context": {"mfa_verified": False, "corporate_network": False, "client_ip": "198.51.100.88"},
            },
        },
    ]

    with httpx.Client(timeout=15.0) as client:
        for item in stages:
            print(f"\n[STAGE {item['stage']}: {item['name']}]")
            print(f"  Description: {item['desc']}")
            print(f"  Injecting  : {item['payload']['event_id']} ({item['payload']['action']} on {item['payload']['resource_identifier']})...")

            res = client.post(f"{api_url}/events", json=item["payload"])
            if res.status_code not in [200, 201]:
                print(f"  [ERROR] Ingestion failed ({res.status_code}): {res.text}")
                return

            data = res.json()
            score = data.get("total_score")
            level = data.get("risk_level")
            print(f"  --> Ingested. Evaluated Risk: {score}/100.0 [{level}]")

            # Check for ML anomaly and correlation flags
            for f in data.get("factors", []):
                if f["factor"] in ["ML_ISOLATION_FOREST_ANOMALY", "MULTI_EVENT_KILL_CHAIN_CORRELATION"]:
                    print(f"      [FLAG] {f['factor']} (+{f['contribution']} pts): {f['explanation']}")

            if data.get("case_id"):
                print(f"      [ALERT] Generated Case ID: {data['case_id']}")

            if item["stage"] < 4:
                time.sleep(delay_seconds)

    print("\n" + "=" * 70)
    print("  KILL-CHAIN SIMULATION COMPLETE — CHECK SOC DASHBOARD FOR ACTIVE CASE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    delay = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    run_staged_killchain(delay_seconds=delay)
