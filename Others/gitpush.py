import subprocess

try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "auto update csv"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Pushed to GitHub successfully")
except subprocess.CalledProcessError as e:
    print("Git command failed:", e)