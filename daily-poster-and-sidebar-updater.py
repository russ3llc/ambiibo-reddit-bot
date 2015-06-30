# Original autpost.py by /u/GoldenSights
# Modified by /u/russ3ll for /r/ambiio
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import datetime
import re

'''USER CONFIGURATION'''

USERNAME  = "USER"
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = "PASS"
#This is the bot's Password. 
USERAGENT = "UA"
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "SUB"
#This is the sub you will make the post in.
WAIT = 180
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

PTIME = "04:00"
#HH:MM Format
#TWENTY-FOUR HOUR STYLE
#UTC TIMEZONE
#http://www.timeanddate.com/time/map/


#The Following Post title and Post text can be customized using the strftime things
#    https://docs.python.org/2/library/time.html#time.strftime
#    Ex: "Daily thread for %A %B %d %Y" = "Daily thread for Tuesday November 04 2014"
#Don't forget that the text will be wrung through reddit Markdown
PTITLE = "DAILY THREAD TITLE %m/%d/%Y"
PTEXT = """
DAILY THREAD TEXT

"""


'''All done!'''


WAITS = str(WAIT)


sql = sqlite3.connect('ambiio.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS posts(ID TEXT, STAMP TEXT, CREATED INT)')
print('Loaded SQL Database')
sql.commit()

print('Logging in')
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

ptime = PTIME.split(':')
ptime = (60*int(ptime[0])) + int(ptime[1])

def dailypost():
	subreddit = r.get_subreddit(SUBREDDIT, fetch=True)
	#I want to ping reddit on every cycle. I've had bots lose their session before
	now = datetime.datetime.now(datetime.timezone.utc)
	daystamp = datetime.datetime.strftime(now, "%d%b%Y")
	cur.execute('SELECT * FROM posts WHERE STAMP=?', [daystamp])
	nowtime = (60*now.hour) + now.minute
	print('Now: ' + str(nowtime) + ' ' + datetime.datetime.strftime(now, "%H:%M"))
	print('Pst: ' + str(ptime) + ' ' + PTIME)
	if not cur.fetchone():
		diff = nowtime-ptime
		if diff > 0:
			print('t+ ' + str(abs(diff)) + ' minutes')
			makepost(now, daystamp)
		else:
			print('t- ' + str(diff) + ' minutes')
	else:
		print("Already made today's post")



def makepost(now, daystamp):
	print('Making post...')
	ptitle = datetime.datetime.strftime(now, PTITLE)
	ptext = datetime.datetime.strftime(now, PTEXT)
	try:			
		newpost = r.submit(SUBREDDIT, ptitle, text=ptext, captcha=None)
		print('Success: ' + newpost.short_link)
		cur.execute('INSERT INTO posts VALUES(?, ?, ?)', [newpost.id, daystamp, newpost.created_utc])
		sql.commit()
		print('Updating sidebar...')
		updatesidebar(newpost)
	except praw.requests.exceptions.HTTPError as e:
		print('ERROR: PRAW HTTP Error.', e)

def updatesidebar(newpost):
    settings = r.get_settings(SUBREDDIT)
    sidebar = settings['description']
    #^^ Get sidebar
    findExp = '(?!#)(\[Daily Haul)(.*?)(?=#)'
    findExp = re.compile(findExp)
    #^ RegEx for replacing old banner link
    now = datetime.datetime.now(datetime.timezone.utc)
    fDate = datetime.datetime.strftime(now, "%m/%d")
    #^^ Get date for link text
    newDaily = "[Daily Haul Megathread "
    newDaily += str(fDate)
    newDaily += "](" + str(newpost.short_link) + ")"
    #^^^ Set the new daily 'text' + 'date' + 'link'
    sidebar = findExp.sub(newDaily,sidebar)
    #^ Replace old sidebar link with new sidebar link
    r.update_settings(r.get_subreddit(SUBREDDIT),description = sidebar)
    #^ Apply changes
    print('Sidebar updated.')


while True:
	try:
		dailypost()
	except Exception as e:
		print("ERROR:", e)
	print('Sleeping ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)
