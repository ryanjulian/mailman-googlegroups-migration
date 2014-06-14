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

import pprint
import sys
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
CREDENTIAL_FILE = 'migrate_credentials.dat'

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console <https://code.google.com/apis/console>.

""" % os.path.join(os.path.dirname(__file__), CLIENT_SECRETS)


def access_settings(service, groupId, settings):
  """Retrieves a group's settings and updates the access permissions to it.

  Args:
    service: object service for the Group Settings API.
    groupId: string identifier of the group@domain.
    settings: dictionary key-value pairs of properties of group.
  """

  # Get the resource 'group' from the set of resources of the API.
  # The Group Settings API has only one resource 'group'.
  group = service.groups()

  # Retrieve the group properties
  g = group.get(groupUniqueId=groupId).execute()
  print '\nGroup properties for group %s\n' % g['name']
  pprint.pprint(g)

  # If dictionary is empty, return without updating the properties.
  if not settings.keys():
    print '\nGive access parameters to update group access permissions\n'
    return

  body = {}

  # Settings might contain null value for some keys(properties). 
  # Extract the properties with values and add to dictionary body.
  for key in settings.iterkeys():
    if settings[key] is not None:
      body[key] = settings[key]

  # Update the properties of group
  g1 = group.update(groupUniqueId=groupId, body=body).execute()

  print '\nUpdated Access Permissions to the group\n'
  pprint.pprint(g1)


def main(argv):
  """Migrates email messages from Mailman mbox archives to Google Group using 
     the Groups Migration API."""
  usage = 'usage: %prog [options]'
  parser = ArgumentParser(parents=[tools.argparser], usage=usage)
  parser.add_argument('--group',
                      help='Group email address')
  args = parser.parse_args()
  
  if args.group is None:
    print 'Give the address of the group'
    parser.print_help()
    return

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

  #service = build('groupssettings', 'v1', http=http)

  #access_settings(service=service, groupId=options.groupId, settings=settings)

if __name__ == '__main__':
  main(sys.argv)
