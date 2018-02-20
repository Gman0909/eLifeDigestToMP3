**eLifeArticleToMP3**

This script utilises the AWS Polly service to generate MP3's from the text of eLife digests.
It assumes you have AWS CLI installed (see https://aws.amazon.com/cli/)

- Run server.py
- Run DigestBot3.py

Running with no command line arguments will scan the eLife RSS feed for articles
containing Digests.

You can also enter a series of eLife article numbers as command line parameters (no spaces)

_Example: python3 Digestbot3.py 32481_

Any digests found will be converted to MP3 and saved locally.
