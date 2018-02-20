import urllib.request, urllib.parse, urllib.error
import os
import sys
from glob import iglob
import shutil
import ssl
import requests
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from elifetools import parseJATS as parser
import feedparser

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

ARGS = sys.argv
CLIENT = boto3.client('polly')


class NewDigest(object):
    def __init__(self, title, content):
        self.title = title
        self.content = content


def changepath(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    os.chdir(path)


# checks if a digest is present in a given elifeTools soup


def hasdigest(item):
    if parser.digest(item):
        title = parser.title(item)
        content = parser.digest(item)
        return NewDigest(title, content)
    else:
        return False


# split the string into 1500 char long sub-strings

def chunkstring(string, length):
    return (string[0 + i:length + i] for i in range(0, len(string), length))


# Call this to save some text as a a temporary mp3 file with an .mpt extension

def makesound(speaktext, articlenumber, chunk):
    filename = str(articlenumber + '-' + str(chunk) + '.mpt')
    try:
        response = CLIENT.synthesize_speech(
            OutputFormat='mp3',
            SampleRate='22050',
            Text=speaktext,
            TextType='text',
            VoiceId='Joanna',
        )

        # Write the audio stream from the response to file until it's done

        f = open(filename, 'wb')
        stream = response['AudioStream']
        while True:
            snippet = stream.read(1024)
            if len(snippet) != 0:
                f.write(snippet)
            else:
                break
        f.close()
    except (BotoCoreError, ClientError) as err:
            print(str(err))


# concatenate all the mpt's we have just created into a final .mp3

def concatenate(articlenumber):
    print('creating mp3 for article ' + str(articlenumber) + '\n')
    destination = open(str(articlenumber) + '.mp3', 'wb')
    for filename in sorted(iglob('*.mpt')):
        shutil.copyfileobj(open(filename, 'rb'), destination)
    destination.close()
    os.system('rm *.mpt')


# does this url exist?

def testurl(url):
    request = requests.get(url)
    return bool(request.status_code == 200)


def geturl(url, filename):
    with urllib.request.urlopen(url, context=CTX) as u, \
            open(filename, 'wb') as f:
        f.write(u.read())


# openelifexml downloads the xml of the latest version of an article to a temp file and looks for a digest.
# if it finds one, it calls makesound() to conver it to an mp3

def openelifexml(articlenumber):
    print('Scanning article for digest: ' + str(articlenumber) + '\r')

    # find the latest version of the article by testing subsequent version URLs
    version = 1
    while testurl('https://cdn.elifesciences.org/articles/' + articlenumber + '/elife-' + articlenumber + '-v' + str(
            version) + '.xml'):
        version += 1
    xmlurl = 'https://cdn.elifesciences.org/articles/' + articlenumber + '/elife-' + articlenumber + '-v' + str(
        version - 1) + '.xml'
    filename = str(articlenumber) + '.xml'

    # Grab the article XML from the latest version's URL and dump it to a file we can then examine

    geturl(xmlurl, filename)
    soup = parser.parse_document(filename)

    # Is there a digest in the XML? If so, get converting.

    currentdigest = hasdigest(soup)
    if currentdigest:
        title = currentdigest.title
        content = currentdigest.content

        # output the title and content. this is the bit where you hook up another output (slack, alexa etc)

        print('Found Digest for article number {} v{} : {}'.format(articlenumber, version - 1, title))
        # print (content)
        content = title + '.\n' + content

        # Amazon's Polly has a 1500char limit per request. chunkstring() takes care of that.
        choppedcontent = chunkstring(content, 1500)
        chunk = 1
        for substring in choppedcontent:
            makesound(substring, articlenumber, chunk)
            chunk += 1
        concatenate(articlenumber)
    os.system('rm ' + filename)


# Scan the eLife RSS feed for digests to convert. Default behaviour if the script is run with no arguments

def scanfeed():
    feed = []
    with urllib.request.urlopen('https://elifesciences.org/rss/recent.xml', context=CTX) as url:
        feed = feedparser.parse(url)
    print('Scanning {} articles in the eLife RSS feed'.format(len(feed['entries'])))

    # scan every item in the feed by extracting the article number

    for entry in feed['entries']:
        articlelink = entry['link']
        articlenumber = articlelink.split('/')[-1]
        openelifexml(articlenumber)


changepath('Digests')
print('eLife Digest to MP3 converter')
print('This work is licensed under a Creative Commons Attribution 4.0 International License')
print('Usage: enter eLife article numbers after the command (without commas), or leave blank for an RSS scan\n')

if len(ARGS) == 1:
    scanfeed()
else:
    for arg in ARGS[1:]:
        openelifexml(arg)
