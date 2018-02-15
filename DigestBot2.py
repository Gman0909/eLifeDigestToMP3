from elifetools import parseJATS as parser
import feedparser
import urllib
import requests
import os
import sys
from glob import iglob
import shutil
import time
from optparse import OptionParser
from slacker import Slacker

global soup
input_articles = None
args = None
cli = None
slack = Slacker('')

class newdigest(object):
	def  __init__(self, title,content):
		self.title = title
		self.content = content

#checks if a digest is present given an elifeTools soup

def hasdigest(item):
    if parser.digest(item):
        title = parser.title(item)
        content = parser.digest(item)
        return newdigest(title,content)
    else:
        return False

#split the string into 1500 char long sub-strings

def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))

#Call this to save some text as an mp3

def makesound(speaktext,articlenumber,chunk):
    #tts = gTTS(text=speaktext, lang='en')
    #tts.save("digest.mp3")
    #print 'creating mp3 for article '+str(articlenumber+'-'+str(chunk)+'.mp3')
    os.system('aws polly synthesize-speech --output-format mp3 --voice-id Joanna --text \''+speaktext+'\' '+str(articlenumber+'-'+str(chunk)+'.mpt | echo '''))

def concatenate(articlenumber):
    print 'creating mp3 for article '+str(articlenumber)+'\n'
    destination = open(str(articlenumber)+'-final.mp3', 'wb')
    for filename in iglob(os.path.join('*.mpt')):
        shutil.copyfileobj(open(filename, 'rb'), destination)
    destination.close()
    os.system('rm *.mpt')

# does this url exist?

def testurl(url):
    request = requests.get(url)
    if request.status_code == 200:
        return True
    else:
        return False

#openelifexml downloads the xml of the latest version of an article to a temp file and looks for a digest. if it finds one, it calls makesound() to conver it to an mp3

def openelifexml(articlenumber):
    print 'Scanning article for digest: '+str(articlenumber)+'\r'
    version = 1
    while testurl('https://cdn.elifesciences.org/articles/'+articlenumber+'/elife-'+articlenumber+'-v'+str(version)+'.xml'):
        version += 1
    xmlurl = 'https://cdn.elifesciences.org/articles/'+articlenumber+'/elife-'+articlenumber+'-v'+str(version-1)+'.xml'
    tempfile = urllib.urlretrieve(xmlurl, 'temp.xml')
    soup = parser.parse_document('temp.xml')

    currentdigest = hasdigest(soup)
    if currentdigest:
        title = currentdigest.title.encode('utf-8','ignore')
        content = currentdigest.content.encode('utf-8','ignore')

#output the title and content. this is the bit where you hook up another output (slack, alexa etc)

        print 'Digest for article number '+articlenumber+' v'+str(version-1)+', '+title+':'
        print content
        content = title +'.\n'+content
        choppedcontent = chunkstring(content,1500)
        chunk = 1
        for substring in choppedcontent:
            makesound(substring,articlenumber,chunk)
            chunk +=1
        concatenate(articlenumber)

def scanfeed():
    articlenumber = '00000'
    feed = feedparser.parse('https://elifesciences.org/rss/recent.xml')
    print 'Scanning %s articles in the eLife RSS feed' % (len(feed['entries']))

# scan every item in the feed by extracting the article number

    for entry in feed['entries']:
        articlelink = entry['link']
        articlenumber = articlelink.split('/')[-1]
        openelifexml(articlenumber)

# prompt the user to enter a list of article numbers
def get_input_parameters():
    global input_articles
    global args
    input_articles = raw_input("Enter article numbers to convert (separated by a comma) or 'r' to scan RSS feed:")
    args = input_articles.split(',')

args = sys.argv
print 'eLife Digest to MP3 converter'
print 'This work is licensed under a Creative Commons Attribution 4.0 International License'
print 'Usage: enter eLife article numbers after the command (without commas), or leave blank for an RSS scan\n'
if len(args) == 1:
    scanfeed()
else:
    for arg in args[1:]:
        openelifexml(arg)
