"""
Guide for getting details from youtube videos for future reference.
 https://developers.google.com/youtube/v3/guides/implementation/videos
 TODO: Allow users to see which videos have been downloaded.
 TODO: Allow users to play video from terminal. Possibly use mplayer?
 TODO: Allow users to set what time task is scheduled. Unsure how to implement this. Would prefer crossplatform, so crontab may be out of the picture.
 TODO: Allow users to download videos from search.
 TODO: Show thumbnails in search.
 TODO: Export data
 TODO: Allow user to specify arguments for youtubel-dl, for example whether or not to use aria2.

 CHANGELOG: Sorta? idk? This is is what I am going to keep track of what has been changed.
 1.) Created new function to parse channel rss feeds instead of calling the youtube api.
 2.) It should be illegal to use this many ansi escape codes. I'll have to clean this up later.
 3.) Decreased visible clutter while running the program.
 4.) Started using aria2 to increase speeds of downloads.
 5.) Updated database with description column, and downloaded column. Queries marked as downloaded will not be returned from query_db()
 6.) Added mark_downloaded query. This will reduce queried results returned, and number of requests to youtube.
 7.) Added kickass ascii art.
"""


import os
import argparse
import requests
import subprocess
import feedparser
from validation import *
from apikey import apikey

matrixgreen = "\u001b[38;5;46m"
removecolor = "\u001b[0m"
underline = "\u001b[4m"


def main():
	parser = argparse.ArgumentParser(description="Download Youtube Videos Automatically")
	parser.add_argument("-new", 
			    action='store_true', 
			    help="Add a youtube creator to the database.")
	
	parser.add_argument("-d", 
			    action='store_true', 
			    help="Checks database and downloads videos automatically")
	
	parser.add_argument("-channels", 
			    action='store_true', 
			    help="Shows you all channels that have been added to the database.")
	parser.add_argument("-search", 
			    action='store_true', 
			    help="Search youtube")
	
	args = parser.parse_args()

	if args.new:
		# Only creates database and inserts new entry.
		#TODO: Show confirmation messages which displays which channel was added to database.
		#TODO: Allow users to add channel by name.
		
		url = User_data()
		create_db()
		parse_ytrss(url)
	
	elif args.d:
		# Query the database, create a set of unique ids, send a request for each unique id.
		
		uploads = query_db()
		uid_set = set()

		for upload in uploads:
			uid_set.add(upload[1])
		for item in uid_set:
			parse_ytrss(item)

		download_video()

	elif args.search:
		search_results()

	elif args.channels:
		print(f"{underline} {matrixgreen} Your Channels: {removecolor}")
		channel_set = set()
		data = query_db()

		for i in data:
			channel_set.add(i[0])
		print([f"{matrixgreen} {i} {removecolor}\n\n" for i in channel_set])
	else:
		print(f"{matrixgreen} You did not specify arguments. ",
		      f"Type ytautodl.py -h for more information on how to run this program\n{removecolor}",
		     sep="\n")

	#TODO: Create argument that will allow you to add from CSV.
	#TODO: Show related after videos are done downloading.

def request_uploads(playlist_id):
	# Deprecated. Reserving this method just in case youtube gets rid of their rss feed.
	params = {
		"part": "snippet",
		"playlistId": playlist_id,
		"key": api_key
		}


	link = "https://www.googleapis.com/youtube/v3/playlistItems"
	r = requests.get(link, params=params)
	responses = r.json()["items"]
	for response in responses:
		channel_title = response["snippet"]["channelTitle"]
		channel_id = response["snippet"]["channelId"]
		uploads_id = response["snippet"]["playlistId"]
		video_id = response["snippet"]["resourceId"]["videoId"]
		video_date = response["snippet"]["publishedAt"][0:10]
		video_title = response["snippet"]["title"]
		
		insert_data(channel_title, 
			    channel_id, 
			    uploads_id, 
			    video_id, 
			    video_date, 
			    video_title)

def parse_ytrss(rss_link):
	# New function will parse youtube rss feeds to reduce api requests.
	#TODO: Skip videos which have been marked as downloaded.
	rss_link = f"https://www.youtube.com/feeds/videos.xml?channel_id={rss_link}"

	resp = requests.get(rss_link)
	page = resp.text

	d = feedparser.parse(page)
	entries = d.entries

	for entry in entries:
		channel_title = entry['authors'][0]['name'] 
		channel_id = entry['yt_channelid'] 
		uploads_id = "UU" + channel_id[2::]
		video_id = entry['yt_videoid'] 
		video_date = entry['published'][0:10]
		video_title = entry['title'] 
		description = entry['summary']
		downloaded = '0'
		insert_data(channel_title,
			    channel_id,
			    uploads_id,
			    video_id,
			    video_date,
			    video_title,
			    description,
			    downloaded)


def search_results():
	videos = []
	search_query = input("Search: ")
	search_query  = search_query.replace(' ', '%20')
	linesep = f"*{'-'*90}"
	params = {
		"part": "snippet",
		"maxResults": 5,
		"q": search_query,
		"key": api_key
	}
	link = "https://www.googleapis.com/youtube/v3/search"
	r = requests.get(link, params=params)
	response = r.json()
	count = 0
	for i in response["items"]:
		count = count + 1
		channel_title = i["snippet"]["channelTitle"]
		video_title = i["snippet"]["title"]
		description = i["snippet"]["description"]
		publish_time = i["snippet"]["publishTime"]
		try:
			video_id = i["id"]["videoId"]
			videos.append(video_id)
			print(f"\n\n{linesep.replace("*", str(count))}",
			     f"| Channel: {channel_title}",
			     f"| Video: {video_title}",
			     sep="\n")
			
			if description == "":
				print("| Description: None")
			else:
				print("| Description:", description)
			print("| Uploaded:", publish_time)
			print(linesep)
		except KeyError:
			count -= 1
			pass

	print("totalResults:", response["pageInfo"]["totalResults"])
	print("resultsPerPage:", response["pageInfo"]["resultsPerPage"])
	choose_video = int(input("Enter a number to select which video you would like to see: "))
	choose_video -= 1
	print(choose_video)
	try:
		print("https://www.youtube.com/watch?v=" + videos[choose_video])
	except IndexError:
		print("Not a valid number")
	print(videos)

def download_video():
	print("Searching for content...")
	uploads = query_db()
	ytprefix = "https://www.youtube.com/watch?v="
	for i in uploads:
		channel_title = i[0]
		video_id = i[3]
		video_date = i[4]
		video_title = i[5]
		path = os.getcwd() + "/" + channel_title
		download = ytprefix + video_id
		if not os.path.isdir(path):
				os.mkdir(path)
				print (f"Directory {path} created")
		clearline = "\033[K"
		moveup = "\033[1A"
		movedown = "\033[1B"
		returnhome = "\u001b[1000D"
		save = "\u001b[s"
		sreturn = "\033[K"

		os.chdir(path)
		sys.stdout.write(save + matrixgreen + "Video: %s \nChannel: %s" % (video_title, channel_title) + sreturn + removecolor)
		sys.stdout.flush()
		sys.stdout.write(returnhome)
		sys.stdout.write(clearline)
		sys.stdout.write(moveup)
		sys.stdout.write(clearline)
		fetch = subprocess.run(["youtube-dl", "--no-warnings", "-o", "%(uploader)s - %(title)s.%(ext)s", "--external-downloader", "aria2c", "--external-downloader-args", "'-x 8 -s 8 -k 1m'", download], stdout=subprocess.DEVNULL)
		os.chdir("..")
		print(fetch.returncode)
		if fetch.returncode == 0:
			mark_downloaded(video_id)

if __name__ == "__main__":
	ytadl = '''                                                                              
                                                                              
                     mm         db      `7MM"""Yb. `7MMF'                     
                     MM        ;MM:       MM    `Yb. MM                       
        `7M'   `MF'mmMMmm     ,V^MM.      MM     `Mb MM                       
          VA   ,V    MM      ,M  `MM      MM      MM MM                       
           VA ,V     MM      AbmmmqMA     MM     ,MP MM      ,                
            VVV      MM     A'     VML    MM    ,dP' MM     ,M                
            ,V       `Mbmo.AMA.   .AMMA..JMMmmmdP' .JMMmmmmMMM                
           ,V                              made by Sean Pedigo                         
        OOb"                                                                   
                                                                              
'''
	sys.stdout.write(matrixgreen + ytadl + removecolor)
	main()
	print(matrixgreen + "Thank you for using ytautodl...\n\n" + removecolor)
