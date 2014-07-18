mailman-googlegroups-migration
==============================

Simple scripts which migrate Mailman archives to Google Groups for Business using the Groups Migration API

# Install Dependencies
    pip install click
    pip install google-api-python-client

# Example
    $ ./migrate.py --noauth_local_webserver --group migration-test@example.com --mbox ~/archives/example.mbox
    
# Documentation
    $ ./migrate.py --help
    usage: migrate.py [-h] [--auth_host_name AUTH_HOST_NAME]
                      [--noauth_local_webserver]
                      [--auth_host_port [AUTH_HOST_PORT [AUTH_HOST_PORT ...]]]
                      [--logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                      --group GROUP --mbox MBOX

    optional arguments:
      -h, --help            show this help message and exit
      --auth_host_name AUTH_HOST_NAME
                            Hostname when running a local web server.
      --noauth_local_webserver
                            Do not run a local web server.
      --auth_host_port [AUTH_HOST_PORT [AUTH_HOST_PORT ...]]
                            Port web server should listen on.
      --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            Set the logging level of detail.
      --group GROUP         Group email address
      --mbox MBOX           Mailman archive file (.mbox)
