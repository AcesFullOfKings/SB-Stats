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
ignored_votes = 0

for segment in segment_reader:
	votes         = int(segment["votes"])
	hidden        = int(segment["hidden"])
	shadowHidden  = int(segment["shadowHidden"])
	endTime       = float(segment["endTime"])
	startTime     = float(segment["startTime"])
	views         = int(segment["views"])
	userID        = segment["userID"]
	actionType    = segment["actionType"] # can be skip, mute, full, poi, or chapter
	timeSubmitted = int(segment["timeSubmitted"])/1000 #the db encodes this in milliseconds, but I want it in seconds.

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
	else:
		ignored_votes += 1

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

if current_platform != "Windows":
	os.system(f"sudo cp leaderboard.json {today_leaderboard_filename}")
	os.system(f"sudo cp global_stats.json {today_globalstats_filename}")
else:
	os.system(f"copy leaderboard.json {today_leaderboard_filename}")
	os.system(f"copy global_stats.json {today_globalstats_filename}")

print("Done!")