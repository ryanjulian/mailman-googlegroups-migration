#!/usr/bin/python
#
# Copyright 2014 Pioneers in Engineering
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Migrate Mailman mbox archives to Google Groups for Business using the
Google Groups Migration API.

Usage:
  $ python migrate.py

You can also get help on all the command-line flags the program understands
by running:

  $ python migrate.py --help
"""

__author__ = 'Ryan Julian <ryanjulian@pioneers.berkeley.edu>'

import os
from argparse import ArgumentParser
from mailbox import mbox
import click
import time
import threading
from itertools import islice

import pprint
import sys
import logging
from apiclient.discovery import build
from apiclient.http import MediaInMemoryUpload
from apiclient.errors import MediaUploadSizeError
from apiclient.errors import HttpError
import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools

# MAX_QPS, the maximum queries per second allowed by the API
MAX_QPS = 10

# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
CLIENT_SECRETS = 'client_secrets.json'

# CREDENTIAL_FILE, name of a file where the script will automatically store
# OAuth 2.0 credentials obtained during the authorization process.
CREDENTIAL_FILE = 'credentials.dat'

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this script run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console <https://code.google.com/apis/console>.

""" % os.path.join(os.path.dirname(__file__), CLIENT_SECRETS)

# Rate limiting decorator
def rate_limited(max_per_second):
  '''
  Decorator that make functions not be called faster than
  '''
  lock = threading.Lock()
  minInterval = 1.0 / float(max_per_second)
  def decorate(func):
    lastTimeCalled = [0.0]
    def rateLimitedFunction(args,*kargs):
      lock.acquire()
      elapsed = time.clock() - lastTimeCalled[0]
      leftToWait = minInterval - elapsed

      if leftToWait>0:
        time.sleep(leftToWait)

      lock.release()

      ret = func(args,*kargs)
      lastTimeCalled[0] = time.clock()
      return ret
    return rateLimitedFunction
  return decorate

# Helper for progress bar
def show_subject(msg):
  if msg is not None:
    return '%s' % msg['subject'][:39]

# Helper for media upload
@rate_limited(MAX_QPS)
def qps_limit(item):
  return item

def main(argv):
  """Migrates email messages from Mailman mbox archives to Google Group using 
     the Groups Migration API."""
  parser = ArgumentParser(parents=[tools.argparser])
  parser.add_argument('--group',
                      help='Group email address',
                      required=True)
  parser.add_argument('--mbox',
                      help='Mailman archive file (.mbox)',
                      required=True)
  parser.add_argument('--resume',
                      type=int,
                      default=1,
                      help='Resume from the specified offset')
  args = parser.parse_args()
  
  # Setup logging
  logging.basicConfig()
  logger = logging.getLogger("migrate")
  logger.setLevel(getattr(logging, args.logging_level))

  settings = {}

  # Set up a Flow object to be used if we need to authenticate.
  FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
      scope='https://www.googleapis.com/auth/apps.groups.migration',
      message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage(CREDENTIAL_FILE)
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    print 'invalid credentials'
    # Save the credentials in storage to be used in subsequent runs.
    credentials = tools.run_flow(FLOW, storage, args)

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with our good Credentials.
  http = httplib2.Http()
  http = credentials.authorize(http)

  # Load the archive file
  logger.info('Importing mbox file %s...', args.mbox)
  messages = mbox(args.mbox)

  logger.info('%s contains %d messages.', args.mbox, len(messages))

  service = build('groupsmigration', 'v1', http=http)
  archive = service.archive()
  
  # Upload messages
  remaining_messages = islice(iter(messages), args.resume-1, None) # Only process messages after the resume point (if any)
  with click.progressbar(messages,
                         label='Migrating %s' % os.path.basename(args.mbox), 
                         fill_char=click.style('#', fg='green'),
                         show_pos=True,
                         item_show_func=show_subject) as msgs:
    pos = 1
    for msg in msgs:
      if pos < args.resume:
        continue

      try:
        media = MediaInMemoryUpload(msg.as_string(), mimetype='message/rfc822')
        result = qps_limit(archive.insert(groupId=args.group, media_body=media).execute())
        if result['responseCode'] != 'SUCCESS':
          logger.error('Message %d failed!', pos)
          logger.error('Subject: "%s"', msg['subject'])
          logger.error('Response: "%s"', result)
      except Exception, e:
          logger.error('Message %d failed!', pos)
          logger.error('Subject: "%s"', msg['subject'])
          logger.error('Response: %s', e)

      pos = pos + 1

if __name__ == '__main__':
  main(sys.argv)
