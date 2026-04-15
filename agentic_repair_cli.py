#!/usr/bin/env python3
import requests
import json
import os
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Agentic CI/CD Repair CLI Hook")
    parser.add_argument("command", choices=["push"], help="Command to run (e.g., push)")
    parser.add_argument("--endpoint", required=True, help="Webhook endpoint URL (e.g., http://localhost:8000/webhook/ci_failure)")
    
    args = parser.parse_args()
    
    if args.command == "push":
        # In a real environment, you would scrape `os.environ` or a log file.
        # For the hackathon demo, we will push a simulated dummy payload.
        payload = {
            "repo_name": os.getenv("GITHUB_REPOSITORY", "HackToFuture/core-api"),
            "commit_hash": os.getenv("GITHUB_SHA", "a1b2c3d4"),
            "error_logs": "Traceback (most recent call last):\n  File \"main.py\", line 12, in <module>\n    result = process_data(None)\nTypeError: Object of type 'NoneType' has no len()",
            "git_diff": "diff --git a/main.py b/main.py\n--- a/main.py\n+++ b/main.py\n@@ -10,3 +10,4 @@\n-result = process_data([])\n+result = process_data(None)\n print(result)",
            "status": "failed"
        }
        
        print(f"Extracted CI failure logs natively.")
        print(f"Pushing telemetry to {args.endpoint} ...")
        
        try:
            response = requests.post(args.endpoint, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                print(f"[SUCCESS] Agentic Repair Pipeline triggered asynchronously! Incident ID: {response.json().get('incident_id')}")
            else:
                print(f"[ERROR] Failed to trigger webhook. Status: {response.status_code}")
                print(response.text)
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Could not connect to {args.endpoint}. Is the FastAPI backend running?")
            sys.exit(1)

if __name__ == "__main__":
    main()
