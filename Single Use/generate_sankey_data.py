"""
videoID,startTime,endTime,votes,locked,incorrectVotes,UUID,userID,timeSubmitted,views,category,actionType,service,videoDuration,hidden,reputation,shadowHidden,hashedVideoID,userAgent,description

FfgT6zx4k3Q,446.51013,513.39233,225,0,1,96150fa0-a28a-11e9-b210-99c885575bb9,38e7c2af-09f4-4492-bf49-75e443962ccd,1564088876715,3222,sponsor,skip,YouTube,0,1,0,0,0bfebefdc667735b19d5f2630e7e83a5f7fdddb880534ef57091e1761d9ea789,"",""

fBxtS9BpVWs,41,53,116,0,1,b2465943-1313-449c-b75c-08b14756ac0a,38e7c2af-09f4-4492-bf49-75e443962ccd,1564088876715,724,sponsor,skip,YouTube,0,0,0,0,bdd81b2b8192683242fe3608c45d5b958ddc71e9b2981a30d9ab584c580a3df7,"",""
"""

import csv

# set up segs reader:
sponsortimes = open("download/sponsorTimes.csv", "r")
first_row = sponsortimes.readline() # discard this so it's not processed in the loop below
del first_row

sponsortimes_field_names = ["videoID","startTime","endTime","votes","locked","incorrectVotes","UUID","userID","timeSubmitted","views","category","actionType","service","videoDuration","hidden","reputation","shadowHidden","hashedVideoID","userAgent","description"]
segment_reader = csv.DictReader(sponsortimes, fieldnames=sponsortimes_field_names)

total_segments = 0

live	= 0
removed = 0

skip	= 0
mute	= 0
poi	    = 0
full	= 0
chapter = 0

by_vote = 0
by_hide = 0

sponsor	    = 0
selfpromo   = 0
interaction = 0
preview	    = 0
intro	    = 0
outro	    = 0
filler	    = 0
nonmusic	= 0

count_hidden   = 0
count_shadow   = 0

for segment in segment_reader:

	votes		= int(segment["votes"])
	hidden	   = int(segment["hidden"])
	shadowHidden = int(segment["shadowHidden"])
	endTime	  = float(segment["endTime"])
	startTime	= float(segment["startTime"])
	views		= int(segment["views"])
	userID	   = segment["userID"]
	actionType   = segment["actionType"]
	category	 = segment["category"]

	total_segments += 1

	if votes <= -2 or hidden or shadowHidden:
		removed += 1
		if votes <= -2:
			by_vote += 1
		else:
			by_hide += 1
			if shadowHidden:
				count_shadow += 1
			else:
				count_hidden += 1
	else:
		live += 1

		if actionType == "skip":
			skip += 1
		elif actionType == "mute":
			mute += 1
		elif actionType == "poi":
			poi += 1
		elif actionType == "full":
			full += 1
		elif actionType == "chapter":
			chapter += 1

		if category == "sponsor":
			sponsor += 1
		elif category == "preview":
			preview += 1
		elif category == "selfpromo":
			selfpromo += 1
		elif category == "intro":
			intro += 1
		elif category == "outro":
			outro += 1
		elif category == "filler":
			filler += 1
		elif category == "interaction":
			interaction += 1
		elif category == "music_offtopic":
			nonmusic += 1

	if not(total_segments % 500000):
		print(f"Processing line {total_segments}")

"""
print(f"total_segments: {total_segments}")

print(f"live: {live}")
print(f"removed: {removed}")

print(f"skip: {skip}")
print(f"mute: {mute}")
print(f"poi: {poi}")
print(f"full: {full}")
print(f"chapter: {chapter}")

print(f"by_vote: {by_vote}")
print(f"by_hide: {by_hide}")

print(f"count_hidden: {count_hidden}")
print(f"count_shadow: {count_shadow}")

print(f"sponsor: {sponsor}")
print(f"selfpromo: {selfpromo}")
print(f"interaction: {interaction}")
print(f"preview: {preview}")
print(f"intro: {intro}")
print(f"outro: {outro}")
print(f"filler: {filler}")
print(f"nonmusic: {nonmusic}")
"""

output_file_path = "sankey.txt"

with open(output_file_path, "w") as file:
	file.write(f"Segments [{live}] Live\n")
	file.write(f"Segments [{removed}] Removed\n\n")
	
	file.write(f"Live [{skip}] Skip\n")
	file.write(f"Live [{mute}] Mute\n")
	file.write(f"Live [{poi}] Poi\n")
	file.write(f"Live [{full}] Full\n")
	file.write(f"Live [{chapter}] Chapter\n\n")
	
	file.write(f"Skip [{sponsor}] Sponsor\n")
	file.write(f"Skip [{selfpromo}] Selfpromo\n")
	file.write(f"Skip [{preview}] Preview\n")
	file.write(f"Skip [{interaction}] Interaction\n")
	file.write(f"Skip [{intro}] Intro\n")
	file.write(f"Skip [{outro}] Outro\n")
	file.write(f"Skip [{filler}] Filler\n")
	file.write(f"Skip [{nonmusic}] Nonmusic\n\n")
	
	file.write(f"Removed [{by_vote}] By Vote\n")
	file.write(f"Removed [{by_hide}] By Hiding\n\n")
	
	file.write(f"By Hiding [{count_hidden}] Hidden\n")
	file.write(f"By Hiding [{count_shadow}] Shadowhidden\n\n")
	
	file.write(f"// You can set a Node's color, like this:\n")
	file.write(f":Filler #7300FF\n")
	file.write(f":Sponsor #00d400\n")
	file.write(f":Selfpromo #ffff00\n")
	file.write(f":Interaction #cc00ff\n")
	file.write(f":Outro #0202ed\n")
	file.write(f":Intro #00ffff\n")
	file.write(f":Preview #008fd6\n")
	file.write(f":Poi #ff1684\n")
	file.write(f":Chapter #ffd679\n")

print(f"Done. Saved results to {output_file_path}")
