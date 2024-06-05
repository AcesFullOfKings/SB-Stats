import os
import requests

from datetime   import datetime
from raspberrypi.my_secrets import PA_token, PA_username

def upload_file(source_path, destination_folder, filename):
    with open(source_path, "rb") as f:
        file_contents = f.read()

    upload_url = f"https://eu.pythonanywhere.com/api/v0/user/{PA_username}/files/path{destination_folder}/{filename}"
    headers = {"Authorization": f"Token {PA_token}"}
    files = {"content": (filename, file_contents)}

    response = requests.post(upload_url, headers=headers, files=files)

    if response.status_code in [200, 201]: # either created or updated
        print(f"File \"{filename}\" uploaded successfully to {destination_folder}")
    else:
        print(f"Upload of {filename} failed with status code {response.status_code}: {response.content}")

base_server_file_path   = f"/home/{PA_username}/server/data"  # Destination path on the server
files_to_upload = ["leaderboard.json", "global_stats.json"]
today_string = datetime.now().strftime("%Y-%m-%d")

leaderboard_local_path = "leaderboard.json"
globalstats_local_path = "global_stats.json"
lastupdate_local_path  = "last_db_update.txt"

server_data_path = "/home/AcesFullOfKings/server/data"

upload_file(leaderboard_local_path, server_data_path, "leaderboard.json")
upload_file(globalstats_local_path, server_data_path, "global_stats.json")
upload_file(lastupdate_local_path, server_data_path, "last_db_update.txt")

upload_file(leaderboard_local_path, f"{server_data_path}/Leaderboard/", f"{today_string}_leaderboard.json")
upload_file(globalstats_local_path, f"{server_data_path}/Global Stats/", f"{today_string}_global_stats.json")
