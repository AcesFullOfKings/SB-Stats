"""
This file will be run periodically. It will:

* Get a list of all dates that I have an sqlite3 file for
* Get a list of all users for whom I should generate data
* Get a list of all user-date pairs which exist on the server
* For any user-date pairs which I have locally but not on the server, generate and upload the data

"""

import os
import json
import sqlite3
import requests

from time import time, localtime
from config import my_auth_token, sponsorTimes_sql_archive_path

categories = ["filler", "intro", "outro", "sponsor", "selfpromo", "preview", "interaction", "nonmusic"]
expanded_categories = {'s': 'sponsor', 'u': 'selfpromo', 'i': 'intro', 'o': 'outro', 'p': 'preview', 'r': 'interaction', 'h': 'poi_highlight', 'e': 'exclusive_access', 'f': 'filler', 'c': 'chapter', 'n': 'nonmusic'}
expanded_types = {'f': 'full', 's': 'skip', 'm': 'mute', 'p': 'poi', 'c': 'chapter'}


def log(log_text):
	"""
	Takes a string, s, and logs it to a log file on disk with a timestamp. Also prints the string to console.
	"""
	current_time = localtime()
	# year   = str(current_time.tm_year)
	month  = str(current_time.tm_mon ).zfill(2)
	day    = str(current_time.tm_mday).zfill(2)
	hour   = str(current_time.tm_hour).zfill(2)
	minute = str(current_time.tm_min ).zfill(2)
	second = str(current_time.tm_sec ).zfill(2)
	
	log_time = f"{hour}:{minute}:{second}"
	log_text = log_text.replace("\n", "").replace("\r", "") # makes sure each log line is only one line

	print(f"{log_time} - {log_text}")
	with open("upload_userdata_log.txt", "a", encoding="utf-8") as f:
		f.write(log_time + " - " + log_text + "\n")

def create_userdata_template():
	return {"submissions": {"filler": {"mute": 0, "skip": 0}, "intro": {"mute": 0, "skip": 0}, "outro": {"mute": 0, "skip": 0}, "sponsor": {"mute": 0, "skip": 0, "full": 0}, "selfpromo": {"mute": 0, "skip": 0, "full": 0}, "preview": {"mute": 0, "skip": 0}, "interaction": {"mute": 0, "skip": 0}, "nonmusic": {"mute": 0, "skip": 0}, "poi_highlight": 0, "chapter": 0, "exclusive_access": 0}, "time saved": {"filler": 0, "intro": 0, "outro": 0, "sponsor": 0, "selfpromo": 0, "preview": 0, "interaction": 0, "nonmusic": 0}, "views": {"filler": {"mute": 0, "skip": 0}, "intro": {"mute": 0, "skip": 0}, "outro": {"mute": 0, "skip": 0}, "sponsor": {"mute": 0, "skip": 0}, "selfpromo": {"mute": 0, "skip": 0}, "preview": {"mute": 0, "skip": 0}, "interaction": {"mute": 0, "skip": 0}, "nonmusic": {"mute": 0, "skip": 0}}}

def get_server_userdata():
	"""
	returned data looks like: 
	{
	"abcde_userID1": [
	"2024-07-01",
	"2024-07-02",
	"2024-07-03"
	],
	"abcde_userID2": [
	"2024-07-03",
	"2024-07-04"
	]
	}
	"""
	result = requests.get("https://leaderboard.sbstats.uk/checkUserData", headers={"Authorisation":my_auth_token})
	user_data = result.json()
	return user_data

def get_userIDs():
	result = requests.get("https://leaderboard.sbstats.uk/getUserIDs", headers={"Authorisation":my_auth_token})
	#log(f"received userIDs list is: {result.text}")
	user_data = result.json()
	return user_data

def get_local_file_dates():
	filenames = os.listdir(sponsorTimes_sql_archive_path)
	dates = [filename.split("_")[0] for filename in filenames if filename.startswith("2")]
	return dates

def get_userdata_from_db(file_date, userID):
	
	db_path = os.path.join(sponsorTimes_sql_archive_path, f"{file_date}_sponsorTimes_mini.sqlite3")

	userID = int(userID,16)
	
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	cursor.execute(f"SELECT categoryType,startTime,endTime,views FROM sponsorTimes WHERE userID=\"{userID}\"")
	rows = cursor.fetchall()

	user_data = create_userdata_template()

	if rows:
		for row in rows:
			categoryType,startTime,endTime,views = row
			category, segment_type = categoryType

			try:
				category = expanded_categories[category]
			except KeyError:
				log(f"Skipping row due to unrecognised category: {row}")
				continue # skip the whole row if the category is unrecognised

			try:
				segment_type = expanded_types[segment_type]
			except KeyError:
				log(f"Skipping row due to unrecognised type: {row}")
				continue # skip the whole row if the type is unrecognised

			duration = float(endTime) - float(startTime)
			views = int(views)

			if category in ["poi_highlight", "chapter", "exclusive_access"]:
				user_data["submissions"][category] += 1
			else:
				user_data["submissions"][category][segment_type] += 1
				if segment_type != "full":
					user_data["views"][category][segment_type] += views
					user_data["time saved"][category] = round(user_data["time saved"][category] + duration)

		return user_data
	else:
		return {}

def upload_userdata(user_data, userID):
	json_data = json.dumps(user_data)
	#log(f"json_data is: {json_data}")
	url_params = {"userID":userID}
	result = requests.post("https://leaderboard.sbstats.uk/addUserData",params = url_params, headers={"Authorisation":my_auth_token}, json=json_data)
	if result.status_code != 200:
		log(f"Upload failed for {userID}: {result.status_code} {result.text}")

log("Creating file dates..")
local_file_dates = get_local_file_dates()
local_file_dates.sort() # bc the arbitrary order is silly

log("Getting userID list..")
userIDs = get_userIDs()

log("Getting server userData..")
server_userdata = get_server_userdata()

total_starttime = time()

for userID in userIDs:
	log(f"Generating data for userID: {userID}")
	for file_date in local_file_dates:
		if userID in server_userdata and file_date in server_userdata[userID]:
			# already exists on server, do nothing
			pass
		else:
			user_data = dict()
			#log(f"generating userdata: date: {file_date}; userID: {userID}")
			if date_data := get_userdata_from_db(file_date, userID):
				user_data[file_date] = date_data
			#log(f"generated userdata is: {user_data[file_date]}")
	
			if user_data:
				#log(f"user_data is: {user_data}")
				upload_userdata(user_data, userID)
				#log(f"Upload complete for {file_date} - {userID}")
			else:
				log(f"No data for {file_date}")

log(f"Total time taken: {round(time()-total_starttime, 1)} secs")