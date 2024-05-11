import requests
from my_secrets import PA_token, PA_username

server_file_path = f"/home/{PA_username}/server/"  # Destination path on the server
files_to_upload = ["leaderboard.csv", "global_stats.txt", "last_db_update.txt"]

for filename in files_to_upload:
    with open(filename, "rb") as f:
        file_contents = f.read()

    url = f"https://eu.pythonanywhere.com/api/v0/user/{PA_username}/files/path{server_file_path}{filename}"
    headers = {"Authorization": f"Token {PA_token}"}
    files = {"content": (filename, file_contents)}

    response = requests.post(url, headers=headers, files=files)

    if response.status_code in [200, 201]: # either created or updated
        print(f"File \"{filename}\" uploaded successfully to {server_file_path}")
    else:
        print(f"Upload of {filename} failed with status code {response.status_code}: {response.content}")