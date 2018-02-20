## eLifeArticleToMP3

This script utilises the AWS Polly service to generate MP3's from the text of eLife digests.
It assumes you have AWS CLI installed (see https://aws.amazon.com/cli/)

  `$ python3 server.pyserver.py`
  `$ python3 DigestBot3.py`

Running with no command line arguments will scan the eLife RSS feed for articles
containing Digests.

You can also enter a series of eLife article numbers as command line parameters (no spaces)

**Example:** 

  `$ python3 Digestbot3.py 27014 09410 31640 03641 27798 08709 30212 06487 24232 30490`

Any digests found will be converted to MP3 and saved locally.
