from bottle import route, template, default_app, request, static_file, request, error, HTTPResponse
from datetime import datetime
from config import data_path, home_folder
import os

@route("/favicon.ico")
def serve_favicon():
	return static_file("LogoSponsorBlockSimple256px.png", root=home_folder)

@route("/")
def leaderboard():
	page_path = os.path.join(home_folder, "leaderboard_page.html")

	last_updated=int(get_last_updated())
	last_updated = datetime.fromtimestamp(last_updated).strftime("%d/%m/%y %H:%M")
	return template(page_path, last_updated=last_updated)

@route("/last_db_update")
def get_last_updated():
	last_update_location = os.path.join(data_path, "last_db_update.txt")
	
	with open(last_update_location, "r") as f:
		return f.read()

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
	
	global_stats_location = os.path.join(data_path, "Global Stats")
	filepath = os.path.join(global_stats_location, file_date + "_global_stats.json")
	
	if os.path.exists(filepath):
		return static_file(filepath, root=data_path)
	else:
		return HTTPResponse(body="Not Found", status=404, headers=None)


@route("/leaderboardStyleLight.css")
def css_light():
	return static_file("leaderboardStyleLight.css", root=home_folder)

@route("/leaderboardStyleDark.css")
def css_dark():
	return static_file("leaderboardStyleDark.css", root=home_folder)

@route("/leaderboardStylePink.css")
def css_pink():
	return static_file("leaderboardStylePink.css", root=home_folder)

application = default_app()

"""
if __name__ == "__main__":
	application.run(host="localhost", port=8080), debug=True, reloader=True)
"""