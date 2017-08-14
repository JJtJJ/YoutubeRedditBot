# A reddit bot to give info on a youtube channel when invoked.
# Extracted using youtube's data api.
# Created by /u/JeffJefftyJeffJeff
# Licence: MIT Licence

import praw
import time
import re
import requests
import bs4
import os

commented_path = os.path.join(os.getcwd(),"commented.txt")
apikey_path = os.path.join(os.getcwd(),"apikey.txt")

channel_api_url = 'https://www.googleapis.com/youtube/v3/channels'
list_api_url = 'https://www.googleapis.com/youtube/v3/search'

header = '#**Top videos for channel {}**\n'
video_line = '* [{}](https://youtube.com/watch?v={})\n'
footer = '\n*---Bot created by /u/JeffJefftyJeffJeff | [Source Code](https://github.com/JJtJJ/YoutubeRedditBot)*'

def authenticate():
	# Authenticate this bot
	print('Authenticating...\n')
	reddit = praw.Reddit('YoutubeRedditBot', user_agent = 'web:youtube-reddit-bot:v0.1 (by /u/JeffJefftyJeffJeff)')
	print('Authenticated as {}\n'.format(reddit.user.me()))
	return reddit

def getYoutubeData(channel_name):
	key = getApiKey()

	params = {'key': key, 'part': 'id', 'forUsername': channel_name}
	r = requests.get(channel_api_url, params=params)
	channel_json = r.json()
	channel_id = channel_json["items"][0]["id"]

	params = {'key': key, 'channelId': channel_id, 'order': 'viewCount', 'part': 'snippet', 'type': 'video'}
	r = requests.get(list_api_url, params=params)
	list_json = r.json()
	return list_json

def parseData(channel_data):
	items = channel_data["items"][:5]
	return items

def getApiKey():
	with open(apikey_path) as file:
		for line in file:
			name, var = line.partition(":")[::2]
			if name == 'key':
				return var

def prettifyItem(item):
	s = video_line.format(item["snippet"]["title"], item["id"]["videoId"])
	return s

def buildComment(channel_name, items):
	s = header.format(channel_name) + '---\n'
	for item in items:
		s += item
	s += footer
	return s


def run_bot(reddit):
	data = getYoutubeData('GameGrumps')
	data = map(prettifyItem, parseData(data))
	reply = buildComment('GameGrumps', data)
	print(reply)


def main():
	reddit = 0#authenticate()
	run_bot(reddit)

if __name__ == '__main__':
	main()