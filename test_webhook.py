import requests

payload = {
    "repo_name": "Hack-Babies",
    "commit_hash": "c3d4e5f6",
    "error_logs": """Compiling 'f:\\Hack-Babies\\myproject\\manage.py'...
***   File "f:\\Hack-Babies\\myproject\\manage.py", line 22
    main(
        ^
SyntaxError: '(' was never closed""",
    "git_diff": """diff --git a/myproject/manage.py b/myproject/manage.py
--- a/myproject/manage.py
+++ b/myproject/manage.py
@@ -19,2 +19,2 @@
 if __name__ == '__main__':
-    main()
+    main(
""",
    "status": "failed"
}

resp = requests.post("http://localhost:8000/webhook/ci_failure", json=payload)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.json()}")
