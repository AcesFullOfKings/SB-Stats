"""
sponsortimes.csv: videoID,startTime,endTime,votes,locked,incorrectVotes,UUID,userID,timeSubmitted,
				  views,category,actionType,service,videoDuration,hidden,reputation,shadowHidden,
				  hashedVideoID,userAgent,description
				  16.7M rows

usernames.csv:    userID,userName,locked
				  315k rows
"""

import os
import csv
import json
import base64
import platform

from sys      import argv
from time     import time
from config   import data_path
from datetime import datetime

try:
	sponsorTimes_path = argv[1]
except IndexError:
	sponsorTimes_path = "download/sponsorTimes.csv"
	
try:
	userNames_path = argv[2]
except IndexError:
	userNames_path = "download/userNames.csv"

auto_upvotes_endtime = 1598989542
sponsorblock_epoch   = 1564088876 # the timestamp of the first submitted segment. All segs are after this time.
start_time=time()

# overall global stats:
overall_users       = 0
contributing_users  = 0
overall_submissions = 0
overall_time_saved  = 0
overall_skips       = 0
removed_submissions = 0

# set up segs reader:
sponsortimes = open(sponsorTimes_path, "r", encoding="utf-8")
first_row = sponsortimes.readline() # discard this so it's not processed in the loop below
del first_row

sponsortimes_field_names = ["videoID","startTime","endTime","votes","locked","incorrectVotes","UUID","userID","timeSubmitted","views","category","actionType","service","videoDuration","hidden","reputation","shadowHidden","hashedVideoID","userAgent","description"]
segment_reader = csv.DictReader(sponsortimes, fieldnames=sponsortimes_field_names)

def hex_to_base64(hex_string):
	try:
		# SOME UUIDs contain a version number. Sometimes it's at the beginning, and sometimes at the end.
		# The number makes the hex an odd-length. odd-length is invalid hex.
		# Rather than try to remove it (difficult!), I just zero-pad and encode the zero and the version
		# Thank you hmmm for the idea!
		if len(hex_string)%2 != 0:
			hex_string = "0" + hex_string

		byte_data = hex_string.replace("-", "")
		byte_data = bytes.fromhex(byte_data)
		b64_data = base64.b64encode(byte_data).decode('ascii')
		return b64_data.replace("=", "") # there is usually an = on the end, which is just padding. The b64 won't decode without it though, so append it to convert back to hex
	except:
		print(f"cannot convert hex: {hex_string}")
		return hex_string

# set up mini sponsorTimes writer:
mini_file = open("sponsorTimes_mini.csv", "w")
mini_writer = csv.writer(mini_file)
mini_writer.writerow(["UUID", "userID", "videoID", "startTime", "endTime", "categoryType", "votes", "hiddenShadowHiddenLocked","timeSubmitted"])

mini_categories = {"sponsor":"s", "selfpromo":"u", "intro":"i", "outro":"o", 
				   "preview":"p", "interaction":"r", "poi_highlight":"h", 
				   "exclusive_access":"e", "filler":"f", "chapter":"c",
				   "music_offtopic":"n"}
mini_types = {"full":"f", "skip":"s", "mute":"m", "poi":"p", "chapter":"c"}

#set up users reader:
usernames = open(userNames_path, "r", encoding="utf-8")
first_row = usernames.readline() # discard this so it's not processed in the loop below
del first_row

usernames_field_names = ["userID","userName","locked"]
username_reader = csv.DictReader(usernames, fieldnames=usernames_field_names)

users = dict() # format -> {userID:{username:"", submissions:0, skips:0, time_saved:0, votes:0},}
line_num = 0

print("Processing sponsorTimes.csv..")

contributing_users = set()
active_users = 0

for segment in segment_reader:
	# Stuff for stats:
	votes         = int(segment["votes"])
	hidden        = int(segment["hidden"])
	shadowHidden  = int(segment["shadowHidden"])
	endTime       = float(segment["endTime"])
	startTime     = float(segment["startTime"])
	views         = int(segment["views"])
	userID        = segment["userID"]
	actionType    = segment["actionType"] # can be skip, mute, full, poi, or chapter
	timeSubmitted = int(int(segment["timeSubmitted"])/1000) #the db encodes this in milliseconds, but I want it in seconds.

	# Extra stuff to keep for mini file:
	videoID  = segment["videoID"]
	category = segment["category"]
	UUID     = segment["UUID"]
	locked   = int(segment["locked"])

	mini_category = mini_categories.get(category, "?")
	if mini_category == "?": print(f"unknown category on seg {UUID}: {category}")
	mini_type = mini_types.get(actionType, "?")
	if mini_type == "?": print(f"unknown actionType: {actionType}")
	mini_starttime = round(startTime, 2)
	mini_endtime = round(endTime, 2)
	mini_UUID = hex_to_base64(UUID)
	mini_userID = hex_to_base64(userID)

	mini_HSL = 4*hidden + 2*shadowHidden + locked # packs the three bools into a single binary number 000-111 (saved as 0-7).

	mini_timeSubmitted = timeSubmitted - sponsorblock_epoch # make all timestamps relative to the first segment. Saves digits!

	mini_writer.writerow([mini_UUID, mini_userID, videoID, mini_starttime, mini_endtime, mini_category+mini_type, votes, mini_HSL, mini_timeSubmitted])
	overall_submissions += 1

	if userID not in users:
		users[userID] = {"submissions":0, "total_skips":0, "time_saved":0, "username":userID, "total_votes":0}

	# don't count removed/shadowbanned submissions
	if ((votes > -2) and (not shadowHidden)):
		contributing_users.add(userID)
		users[userID]["submissions"] += 1

		if actionType=="skip":
			users[userID]["total_skips"] += views
			overall_skips += views

			duration = endTime-startTime
			time_saved = (duration*views)
			users[userID]["time_saved"]  += time_saved
			overall_time_saved += time_saved

	if timeSubmitted > auto_upvotes_endtime:
		users[userID]["total_votes"] += votes
	#else:
	#	ignored_votes += 1

	if votes <= -2 or shadowHidden or hidden:
		removed_submissions += 1

	line_num += 1

	if not line_num%1_000_000:
		print(f"Processing line {line_num}")

sponsortimes.close() # finished with this file now
end_time=time()

contributing_users = len(contributing_users)
active_users = len(users)

print(f"Time taken: {round(end_time-start_time,1)}")
print("Processing usernames.csv..")

line_num=0

for user_row in username_reader:
	userID    = user_row["userID"]
	user_name = user_row["userName"]
	#locked    = user_row["locked"]

	if userID != user_name and userID in users:
		users[userID]["username"] = user_name
	
	line_num += 1

	if not line_num%100000:
		print(f"Processing user {line_num}")

usernames.close() # finished with this

#convert dict to list of tuples (for easier sorting below)
user_tuples=[]
while users:
	user_id, user_info = users.popitem() # returns and deletes the next item from users as a tuple of (key, value)
	user_tuple = (user_id, user_info["username"], user_info["submissions"], user_info["total_skips"], user_info["time_saved"], user_info["total_votes"])
	user_tuples.append(user_tuple)

del users

top_submissions = sorted(user_tuples, key=lambda x: x[2], reverse=True)[:200]
top_skips       = sorted(user_tuples, key=lambda x: x[3], reverse=True)[:200]
top_time_saved  = sorted(user_tuples, key=lambda x: x[4], reverse=True)[:200]
top_votes       = sorted(user_tuples, key=lambda x: x[5], reverse=True)[:200]

del user_tuples

# Merge the users from each top list into a set to prevent counting any user more than once
top_users = set(top_submissions + top_skips + top_time_saved + top_votes)

print("Writing output to file..")
line_num = 0

leaderboard = []

for user in top_users:
	user_id     = user[0]
	username    = user[1].replace(",", "") # no commas, bad
	submissions = user[2]
	skips       = user[3]
	time_saved  = round(user[4])
	votes       = user[5]

	user_data = {
		"ID":user_id,
		"name":username,
		"submissions":submissions,
		"skips":skips,
		"saved":time_saved,
		"votes":votes,
		}
	
	leaderboard.append(user_data)
	
with open("leaderboard.json", "w") as f:
	json.dump(leaderboard, f)

global_stats = {
	"contributing_users" : contributing_users,
	"overall_submissions": overall_submissions ,
	"overall_time_saved" : overall_time_saved,
	"overall_skips"      : overall_skips,
	"removed_submissions": removed_submissions,
	"active_users"       : active_users,
}

with open("global_stats.json", "w") as f:
	json.dump(global_stats, f)

today_string = datetime.now().strftime("%Y-%m-%d")

leaderboard_history_folder = os.path.join(data_path, "leaderboard")
globalstats_history_folder = os.path.join(data_path, "Global Stats")

today_leaderboard_filename = os.path.join(leaderboard_history_folder, f"{today_string}_leaderboard.json")
today_globalstats_filename = os.path.join(globalstats_history_folder, f"{today_string}_global_stats.json")

current_platform = platform.system()

if current_platform != "Windows":
	os.system(f'sudo cp leaderboard.json "{today_leaderboard_filename}"')
	os.system(f'sudo cp global_stats.json "{today_globalstats_filename}"')
else:
	os.system(f"copy leaderboard.json {today_leaderboard_filename}")
	os.system(f"copy global_stats.json {today_globalstats_filename}")

print("Done!")