import os
import requests

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

def restart_webserver():
    domain_name = "leaderboard.sbstats.uk"
    url = f"https://eu.pythonanywhere.com/api/v0/user/{PA_username}/webapps/{domain_name}/reload/"
    headers = {"Authorization": f"Token {PA_token}"}

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        print("Webserver has been restarted.")
    else:
        print(f"Response was: {response.status_code}; message is: {response.text}")

file_list = []
#file_list.append("leaderboard_page_beta.html")
#file_list.append("leaderboard_page.html")
#file_list.append("leaderboard_server.py")
#file_list.append("leaderboardStyleDark.css")
#file_list.append("leaderboardStyleLight.css")
#file_list.append("leaderboardStylePink.css")

server_path = "/home/AcesFullOfKings/server"

for filename in file_list:
    filepath = os.path.join("PythonAnywhere", filename)
    upload_file(filepath, server_path, filename)

restart_webserver()

print("Done!")