import sys
import time
import re
import datetime
import sqlite3

class User_data:
	''' Checks for valid youtube link '''
	def __init__(self):
		self.url = ""
		self.user_link(self.url)

	def __str__(self):
		return "{self.url}".format(self=self)

	def user_link(self, url):
		''' Error message for invalid link. '''
		message = '''To create an entry we need the channel url.
		\n\nHere is an example using Google's youtube channel: https://www.youtube.com/channel/UCK8sQmJBp8GCxrOtXWBpyEA''' 

		for c in message:
			sys.stdout.write(c)
			sys.stdout.flush()
			time.sleep(.009)
		self.url = input("\n\nPlease provide a similar link: ")
		self.validate_link()

	def validate_link(self):
		''' Validate if this is a url by sending a request to the url. '''
		regex = re.compile(r"(youtube.com/channel/UC)(.{22})")
		mo = regex.search(self.url)

		if mo == None:
			print("~~~~~~~~~~~~~~~\n\n\nThat is not the link we are looking for.\n")
			self.user_link(self.url)
		else:
			# https://www.youtube.com/feeds/videos.xml?channel_id=UCuXy5tCgEninup9cGplbiFw
			self.url = mo.group()[20::]
			print(self.url)

def insert_data(*args):
	# Inserts data from parse_ytrss()
	insert_Sql = "INSERT INTO ytadl (channel_title, channel_id, uploads_id, video_id, video_date, video_title, description, downloaded) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
	conn = sqlite3.connect('ytadl.db')
	c = conn.cursor()
	try:
		c.execute(insert_Sql, args)
	except sqlite3.IntegrityError:
		pass
	conn.commit()
	c.close()
	conn.close()

def create_db():
	# Creates a database if it does not exist.
	table_sql = "CREATE TABLE IF NOT EXISTS ytadl (channel_title TEXT, channel_id TEXT, uploads_id TEXT, \
	video_id TEXT NOT NULL UNIQUE, video_date TEXT, video_title TEXT, description TEXT, downloaded TEXT)"

	conn = sqlite3.connect('ytadl.db')
	c = conn.cursor()
	c.execute(table_sql)
	c.close()
	conn.close()

def query_db():
	# Returns values from database.
	conn = sqlite3.connect("ytadl.db")
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	c.execute("SELECT channel_title, channel_id, uploads_id, video_id, video_date, video_title, downloaded FROM ytadl where downloaded != '0';")
	selected = [tuple(row) for row in c.fetchall()]
	c.close()
	conn.close()
	return selected

def mark_downloaded(video_id):
	# marks videos as downloaded.
	conn = sqlite3.connect("ytadl.db")
	c = conn.cursor()
	c.execute("UPDATE ytadl SET downloaded = 0 WHERE video_id = ?", (video_id,))
	conn.commit()
	c.close()
	conn.close()


if __name__ == "__main__":
	User_data()