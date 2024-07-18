import os
import json
import random
import sqlite3

from time       import sleep, localtime
from bottle     import route, template, default_app, request, static_file, request, error, HTTPResponse, response
from config     import data_path, home_folder, server_folder, auth_token
from datetime   import datetime
from contextlib import suppress

db_path = os.path.join(data_path, "userdata.sqlite3")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS userdata (
    userID TEXT,
    date TEXT,
    json_data TEXT,
    PRIMARY KEY (userID, date)
)
''')

# Create an index on the userID column
cursor.execute("CREATE INDEX IF NOT EXISTS idx_userID ON userdata(userID);")

VIPs_filepath = os.path.join(data_path, "vipUsers.csv")
with open(VIPs_filepath, "r") as f:
	VIPs = set(f.read().split("\n"))
	with suppress(KeyError):
		VIPs.remove("userID")

server_log_path = os.path.join(server_folder, "server_log.txt")

def log(log_text):
	"""
	Takes a string, s, and logs it to a log file on disk with a timestamp. Also prints the string to console.
	"""
	current_time = localtime()
	# year   = str(current_time.tm_year)
	# month  = str(current_time.tm_mon ).zfill(2)
	# day    = str(current_time.tm_mday).zfill(2)
	hour   = str(current_time.tm_hour).zfill(2)
	minute = str(current_time.tm_min ).zfill(2)
	second = str(current_time.tm_sec ).zfill(2)

	log_time = f"{hour}:{minute}:{second}"
	log_text = log_text.replace("\n", "").replace("\r", "") # makes sure each log line is only one line

	#print(f"{log_time} - {log_text}")
	with open(server_log_path, "a", encoding="utf-8") as f:
		f.write(log_time + " - " + log_text + "\n")

@route("/favicon.ico")
def serve_favicon():
	return static_file("LogoSponsorBlockSimple256px.png", root=home_folder)

@route("/")
def leaderboard():
	page_path = os.path.join(server_folder, "leaderboard_page.html")

	last_updated=int(get_last_updated())
	last_updated = datetime.fromtimestamp(last_updated).strftime("%d/%m/%y %H:%M")
	return template(page_path, last_updated=last_updated)

@route("/beta")
def leaderboard():
	page_path = os.path.join(server_folder, "leaderboard_page_beta.html")

	last_updated=int(get_last_updated())
	last_updated = datetime.fromtimestamp(last_updated).strftime("%d/%m/%y %H:%M")
	return template(page_path, last_updated=last_updated)

@route("/last_db_update")
def get_last_updated():
	last_update_location = os.path.join(data_path, "last_db_update.txt")

	try:
		with open(last_update_location, "r") as f:
			return f.read()
	except FileNotFoundError:
		return "0"

@route("/leaderboard.json")
def serve_leaderboard():
	try:
		file_date = request.headers["file-date"]
	except KeyError:
		# no file date requested - send today's file
		#return static_file("leaderboard.json", root=data_path)
		leaderboard_path = os.path.join(data_path, "leaderboard.json")
		with open(leaderboard_path, "r") as f:
			leaderboard = json.load(f)

		for user in leaderboard:
			user["vip"] = user["ID"] in VIPs

		response.content_type = 'application/json'
		return json.dumps(leaderboard)


	filename = file_date + "_leaderboard.json"
	leaderboard_location = os.path.join(data_path, "Leaderboard")
	filepath = os.path.join(leaderboard_location, filename)

	if os.path.exists(filepath):
		return static_file(filename, root=leaderboard_location)
	else:
		return HTTPResponse(body="Not Found", status=404, headers=None)

@route("/global_stats.json")
def serve_global_stats():
	try:
		file_date = request.headers["file-date"]
	except KeyError:
		# no file date requested - send today's file
		return static_file("global_stats.json", root=data_path)

	filename = file_date + "_global_stats.json"
	globalstats_location = os.path.join(data_path, "Global Stats")
	filepath = os.path.join(globalstats_location, filename)

	if os.path.exists(filepath):
		return static_file(filename, root=globalstats_location)
	else:
		return HTTPResponse(body="Not Found", status=404, headers=None)

def get_dates_from_filenames(directory, suffix):
	"""Helper function to extract dates from filenames in a given directory with a specific suffix."""
	files = os.listdir(directory)
	dates = set()
	for file in files:
		if file.endswith(suffix):
			date_str = file.split('_')[0]
			dates.add(date_str)
	return dates

@route("/available_dates.json")
def serve_available_dates():
	global_stats_path = os.path.join(data_path, "Global Stats")
	leaderboard_path = os.path.join(data_path, "Leaderboard")

	# Get dates from filenames
	global_stats_dates = get_dates_from_filenames(global_stats_path, "_global_stats.json")
	leaderboard_dates = get_dates_from_filenames(leaderboard_path, "_leaderboard.json")

	# Find the intersection of dates
	available_dates = sorted(global_stats_dates & leaderboard_dates)

	# Serve the available dates as JSON
	response.content_type = 'application/json'
	return json.dumps(available_dates)

@route("/leaderboardStyleLight.css")
def css_light():
	return static_file("leaderboardStyleLight.css", root=server_folder)

@route("/leaderboardStyleDark.css")
def css_dark():
	return static_file("leaderboardStyleDark.css", root=server_folder)

@route("/leaderboardStylePink.css")
def css_pink():
	return static_file("leaderboardStylePink.css", root=server_folder)

@route("/addUserData", method="POST")
def add_user_data():
	if "Authorisation" not in request.headers:
		log("Request to add user data denied: no authorisation provided")
		sleep(random.random())
		return HTTPResponse(status=403, body="Not Authorised")

	if request.headers["Authorisation"] != auth_token:
		log("Request to add user data denied: unauthorised")
		sleep(random.random())
		return HTTPResponse(status=401, body="Not Authorised")

	try:
		user_data = json.loads(request.json)
	except Exception as ex:
		log(f"Request to add user data denied: Malformed json data. Exception is: {ex}")
		return HTTPResponse(status=400, body=f"Malformed json data.")

	try:
		userID = request.query["userID"]
	except Exception as ex:
		log(f"Request to add user data denied: No userID provided. Exception is: {ex}")
		return HTTPResponse(status=400, body=f"No userID provided.")

	if len(userID) != 64:
		log(f"Request to add user data denied: incorrect length on userID {userID}")
		return HTTPResponse(status=400, body=f"UserID should be 64 characters.")

	try:
		int(userID, 16)
	except:
		log(f"Request to add user data denied: malformed userID (should be hex, was {userID}")
		return HTTPResponse(status=400, body=f"UserID should be hexadecimal.")


	validated_data = dict()

	for datestamp in user_data:
		try:
			year, month, day = datestamp.split("-")
			assert len(day)==2
			assert len(month)==2
			assert len(year)==4
		except ValueError:
			log(f"Failed to add data: malformed JSON keys - {datestamp}")
			return HTTPResponse(status=400, body=f"Malformed date {datestamp} - date should be in the format YYYY-MM-DD")
		except AssertionError:
			log(f"Failed to add data: incorrect date format - {datestamp}")
			return HTTPResponse(status=400, body=f"Malformed date {datestamp}")

		validated_data[datestamp] = user_data[datestamp]

	for datestamp in validated_data:
		json_string = json.dumps(validated_data[datestamp]) # dump json dict back to string for storage
		cursor.execute('''
			INSERT INTO userdata
			VALUES (?, ?, ?)
			ON CONFLICT(userID, date) DO UPDATE SET
				json_data = excluded.json_data
    		''', (userID, datestamp, json_string))
		conn.commit()

	return HTTPResponse(status=200, body="ok")

@route("/getUserData", method="GET")
def get_user_data():
	try:
		userID = request.query["userID"]
	except:
		return HTTPResponse(status=400, body=f"No userID provided.")

	cursor.execute("SELECT date,json_data FROM userdata WHERE userID=?", (userID,))
	user_data = cursor.fetchall()

	if not user_data:
		return HTTPResponse(status=404, body=f"No data for userID {userID}")

	json_data = dict()

	for row in user_data:
		date, data = row
		json_data[date]=json.loads(data)

	response.content_type = 'application/json'
	return json.dumps(json_data)

@route("/checkUserData", method="GET")
def check_user_data():
	if "Authorisation" not in request.headers:
		sleep(random.random())
		return HTTPResponse(status=403, body="Not Authorised")

	if request.headers["Authorisation"] != auth_token:
		sleep(random.random())
		return HTTPResponse(status=401, body="Not Authorised")

	cursor.execute("SELECT userID,date FROM userdata")
	json_data = dict()

	for row in cursor.fetchall():
		userID, date = row
		if userID in json_data:
			json_data[userID].append(date)
		else:
			json_data[userID] = [date]

	response.content_type = 'application/json'
	return json.dumps(json_data)

@route("/getUserIDs", method="GET")
def get_userIDs():
	userIDs_filepath = os.path.join(data_path, "userData_IDs.txt")
	if "Authorisation" not in request.headers:
		sleep(random.random())
		return HTTPResponse(status=403, body="Not Authorised")

	if request.headers["Authorisation"] != auth_token:
		sleep(random.random())
		return HTTPResponse(status=401, body="Not Authorised")

	with open(userIDs_filepath, "r") as f:
		userIDs = f.read().split("\n")

	response.content_type = 'application/json'
	return json.dumps(userIDs)

@route("/userdata", method="GET")
def userdata_page():
	try:
		userID = request.query["userID"]
	except:
		return HTTPResponse(status=400, body=f"No userID provided.")

	if len(userID) != 64:
		return HTTPResponse(status=400, body=f"UserID must be 64 characters.")

	try:
		int(userID, 16)
	except ValueError:
		return HTTPResponse(status=400, body=f"UserID must be hexadecimal.")


	cursor.execute("SELECT date,json_data FROM userdata WHERE userID=?", (userID,))

	raw_data_list = cursor.fetchall()

	if not raw_data_list:
		addUser(userID)
		return HTTPResponse(status=404, body=f"Data for this userID is being generated - please check back later.")

	response_data = dict()

	for key, data in raw_data_list:
		response_data[key] = json.loads(data)

	return HTTPResponse(body=response_data, status=200, headers={"Content-Type": "application/json"})

# Call this func if a userID page is loaded which I have no data for
def addUser(new_userID):
	assert len(new_userID) == 64, "userID length should be 64"

	userIDs_filepath = os.path.join(data_path, "userData_IDs.txt")

	with open(userIDs_filepath, "r") as f:
		userIDs = f.read().split("\n")

	if new_userID not in userIDs:
		with open(userIDs_filepath, "a") as f:
			f.write("\n" + new_userID)

@route("/sponsorTimes_mini_schema.txt", method="GET")
def get_user_data():
	return static_file("sponsorTimes_mini_schema.txt", root=server_folder)

application = default_app()

if __name__ == "__main__":
	application.run(host="localhost", port=8080)#, debug=True, reloader=True)