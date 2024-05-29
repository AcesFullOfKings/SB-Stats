import os
import requests

from config     import data_path
from datetime   import datetime
from my_secrets import PA_token, PA_username

def upload_file(source_path, destination_folder, filename):
    with open(source_path, "rb") as f:
        file_contents = f.read()

    upload_url = f"https://eu.pythonanywhere.com/api/v0/user/{PA_username}/files/path{destination_folder}/{filename}"
    headers = {"Authorization": f"Token {PA_token}"}
    files = {"content": (filename, file_contents)}

    response = requests.post(url, headers=headers, files=files)

    if response.status_code in [200, 201]: # either created or updated
        print(f"File \"{filename}\" uploaded successfully to {destination_folder}")
    else:
        print(f"Upload of {filename} failed with status code {response.status_code}: {response.content}")

base_server_file_path   = f"/home/{PA_username}/server/data"  # Destination path on the server
files_to_upload = ["leaderboard.json", "global_stats.json"]
today_string = datetime.now().strftime("%Y-%m-%d")

leaderboard_local_path = os.path.join(data_path, "leaderboard.json")
globalstats_local_path = os.path.join(data_path, "global_stats.json")
lastupdate_local_path  = os.path.join(data_path, "last_db_update.txt")

server_base_path = "/server"

upload_file(leaderboard_local_path, server_base_path+"/data", "leaderboard.json")