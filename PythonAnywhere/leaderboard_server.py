from bottle import route, template, default_app, request, static_file, request, error, HTTPResponse, response
from datetime import datetime
from config import data_path, home_folder, server_folder
import os
import json

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
		return static_file("leaderboard.json", root=data_path)

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

application = default_app()

if __name__ == "__main__":
	application.run(host="localhost", port=8080, debug=True, reloader=True)