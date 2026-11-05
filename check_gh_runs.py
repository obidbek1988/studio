import os
import requests

token = os.environ.get("GITHUB_TOKEN", "")
owner = "xakimovabdubannob-gif"
repo = "cloud-node"
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/actions/runs?status=in_progress", headers=headers)
runs = r.json().get("workflow_runs", [])
print(f"Active in_progress runs: {len(runs)}")
for run in runs:
    print(f"Run ID: {run.get('id')} | Name: {run.get('name')}")
