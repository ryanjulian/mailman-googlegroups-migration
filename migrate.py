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

import pprint
import sys
import logging
from apiclient.discovery import build
import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools

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
  
  for msg in messages:
    logger.info('Uploading "%s"...', msg['subject'])
    import pdb; pdb.set_trace()
    archive.insert(groupId=args.group, body=msg.as_string())  

if __name__ == '__main__':
  main(sys.argv)
