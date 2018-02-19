from elifetools import parseJATS as parser
import feedparser
import urllib
import requests
import os
import sys
from glob import iglob
import shutil
import boto3

global soup
input_articles = None
args = sys.argv
cli = None
client = boto3.client('polly')


class newdigest(object):
    def __init__(self, title, content):
        self.title = title
        self.content = content


# checks if a digest is present given an elifeTools soup


def changepath(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    os.chdir(path)


def hasdigest(item):
    if parser.digest(item):
        title = parser.title(item)
        content = parser.digest(item)
        return newdigest(title, content)
    else:
        return False


# split the string into 1500 char long sub-strings

def chunkstring(string, length):
    return (string[0 + i:length + i] for i in range(0, len(string), length))


# Call this to save some text as a a temporary mp3 file with an .mpt extension

def makesound(speaktext, articlenumber, chunk):
    speaktext = speaktext.replace("'", "")
    filename = str(articlenumber + '-' + str(chunk) + '.mpt')

    response = client.synthesize_speech(
        OutputFormat='mp3',
        SampleRate='22050',
        Text=speaktext,
        TextType='text',
        VoiceId='Joanna',
    )

# Write the audio stream from the response to file until it's done

    f = file(filename, 'w')
    stream = response['AudioStream']
    while True:
        snippet = stream.read(1024)
        if len(snippet) != 0:
            f.write(snippet)
        else:
            break
    f.close()


# concatenate all the mpt's we have just created into a final .mp3

def concatenate(articlenumber):
    print 'creating mp3 for article ' + str(articlenumber) + '\n'
    destination = open(str(articlenumber) + '.mp3', 'wb')
    for filename in sorted(iglob('*.mpt')):
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


# openelifexml downloads the xml of the latest version of an article to a temp file and looks for a digest. if it finds one, it calls makesound() to conver it to an mp3

def openelifexml(articlenumber):
    # type: (object) -> object
    print 'Scanning article for digest: ' + str(articlenumber) + '\r'
    version = 1
    while testurl('https://cdn.elifesciences.org/articles/' + articlenumber + '/elife-' + articlenumber + '-v' + str(
            version) + '.xml'):
        version += 1
    xmlurl = 'https://cdn.elifesciences.org/articles/' + articlenumber + '/elife-' + articlenumber + '-v' + str(
        version - 1) + '.xml'
    filename = str(articlenumber) + '.xml'
    tempfile = urllib.urlretrieve(xmlurl, filename)
    soup = parser.parse_document(filename)
    currentdigest = hasdigest(soup)
    if currentdigest:
        title = currentdigest.title.encode('ascii', 'ignore')
        content = currentdigest.content.encode('ascii', 'ignore')

        # output the title and content. this is the bit where you hook up another output (slack, alexa etc)

        print 'Digest for article number ' + articlenumber + ' v' + str(version - 1) + ', ' + title + ':'
        print content
        content = title + '.\n' + content
        choppedcontent = chunkstring(content, 1500)
        chunk = 1
        for substring in choppedcontent:
            makesound(substring, articlenumber, chunk)
            chunk += 1
        concatenate(articlenumber)
    os.system('rm ' + filename)


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


changepath('Digests')
print 'eLife Digest to MP3 converter'
print 'This work is licensed under a Creative Commons Attribution 4.0 International License'
print 'Usage: enter eLife article numbers after the command (without commas), or leave blank for an RSS scan\n'

if len(args) == 1:
    scanfeed()
else:
    for arg in args[1:]:
        openelifexml(arg)
