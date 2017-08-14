# A reddit bot to give info on a youtube channel when invoked.
# Extracted using youtube's data api.
# Created by /u/JeffJefftyJeffJeff
# Licence: MIT Licence

import praw
import time
import re
import requests
import os

commented_path = os.path.join(os.getcwd(),"commented.txt")
apikey_path = os.path.join(os.getcwd(),"apikey.txt")

channel_api_url = 'https://www.googleapis.com/youtube/v3/channels'
search_api_url = 'https://www.googleapis.com/youtube/v3/search'

header = '#**Top videos for channel {}**\n'
video_line = '* [{}](https://youtube.com/watch?v={})\n'
footer = '\n---\n^(Bot created by /u/JeffJefftyJeffJeff | )[^(Source Code)](https://github.com/JJtJJ/YoutubeRedditBot)'

def authenticate():
	# Authenticate this bot
	print('Authenticating...\n')
	reddit = praw.Reddit('YoutubeRedditBot', user_agent = 'web:youtube-reddit-bot:v0.1 (by /u/JeffJefftyJeffJeff)')
	print('Authenticated as {}\n'.format(reddit.user.me()))
	return reddit

def getYoutubeData(channel_name):
	key = getApiKey()

	params = {'key': key, 'part': 'snippet', 'type': 'channel', 'q': channel_name, 'maxResults': '1'}
	r = requests.get(search_api_url, params=params)
	channel_json = r.json()
	snippet = channel_json["items"][0]["snippet"]
	channel_id = snippet["channelId"]
	channel_name = snippet["title"]

	params = {'key': key, 'channelId': channel_id, 'order': 'viewCount', 'part': 'snippet', 'type': 'video'}
	r = requests.get(search_api_url, params=params)
	list_json = r.json()
	return channel_name, list_json

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
	print("Getting 250 comments...\n")

	for comment in reddit.subreddit('test').comments(limit = 250):
		match = re.findall("!youtube\s+.*", comment.body)
		if match:
			print("Found invocation in comment id: " + comment.id)
			inv = match[0]
			channel_name = inv.partition(' ')[-1]

			comment_file_r = open(commented_path, 'r')
			commented = True

			if comment.id not in comment_file_r.read().splitlines():
				print('new invocation; running...\n')
				
				try:
					title, data = getYoutubeData(channel_name)
				except:
					print('Exception!!!')
					commented = False
				else:
					data = map(prettifyItem, parseData(data))
					reply = buildComment(title, data)
					print(reply)

					try:
						comment.reply(reply)
					except praw.exceptions.APIException as err:
						print(err.error_type)
						if err.error_type == 'RATELIMIT':
							commented = False
			else:
				print('already replied\n')
				commented = False

			comment_file_r.close()

			if commented:
				comment_file_w = open(commented_path, 'a+')
				comment_file_w.write(comment.id + '\n')
				comment_file_w.close()

			time.sleep(10)

	print('waiting 60s...')
	time.sleep(60)


def main():
	reddit = authenticate()
	while True:
		run_bot(reddit)

if __name__ == '__main__':
	main()