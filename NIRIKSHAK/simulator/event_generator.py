import argparse
import json
import sys
import httpx

DEFAULT_API_URL = "http://localhost:8000/api/v1"


def trigger_scenario(scenario: str, api_url: str = DEFAULT_API_URL):
    """Triggers an on-demand demo scenario via the NIRIKSHAK API."""
    endpoint = f"{api_url}/scenarios/trigger"
    print(f"\n[NIRIKSHAK SIMULATOR] Triggering scenario: '{scenario}' -> {endpoint}")

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.post(endpoint, json={"scenario": scenario})

            if res.status_code == 200:
                data = res.json()
                print("\n=======================================================")
                print(f"  SCENARIO RESULT: {data['scenario'].upper()}")
                print("=======================================================")
                print(f"  Event ID     : {data['event_id']}")
                print(f"  Risk Score   : {data['total_score']} / 100.0")
                print(f"  Risk Level   : {data['risk_level']}")
                print(f"  Case Created : {data['case_created']} ({data.get('case_id') or 'N/A'})")
                print(f"  Summary      : {data['summary']}")
                print("=======================================================\n")
                return data
            else:
                print(f"[ERROR] API returned {res.status_code}: {res.text}")
                sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Connection to NIRIKSHAK backend failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="NIRIKSHAK On-Demand Scenario Generator")
    parser.add_argument(
        "--scenario",
        type=str,
        default="normal",
        choices=["normal", "off_hours", "exfiltration", "kill_chain"],
        help="Scenario to inject: 'normal', 'off_hours', 'exfiltration', or 'kill_chain'",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=DEFAULT_API_URL,
        help="Base API URL (default: http://localhost:8000/api/v1)",
    )

    args = parser.parse_args()
    trigger_scenario(args.scenario, args.api_url)


if __name__ == "__main__":
    main()
