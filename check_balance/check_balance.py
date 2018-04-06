#!/usr/bin/env python

import os
import sys
import requests
import datetime
import dateutil.tz
import time
import argparse

def check_http_reply(reply):
    print(reply.status_code)
    print(reply.text)
    print("----------------------------------------------")
    if reply.status_code != 200:
        raise Exception("HTTP call has failed. Status code: {code} - {text}".format(code=reply.status_code, text=reply.text))

def write_status(status_code, status_text):
    script_path = os.path.dirname(os.path.realpath(__file__))
    print(status_text)
    # with open(os.path.join(script_path, "status"), "w") as f:
    #     timestamp = datetime.datetime.now(dateutil.tz.tzoffset(None, -time.altzone)).replace(microsecond=0).isoformat()
    #     f.write(timestamp + ";" + status_code + ";" + status_text)

def test():
    session = requests.session()
    check_http_reply(session.get("https://stats.tis-dialog.ru/"))
    # check_http_reply(session.get("https://stat.sovatelecom.ru/"))

    post_data = {"login": "", "passv": ""}
    check_http_reply(session.post("https://stats.tis-dialog.ru/index.php", data=post_data))
    # post_data = {"LOGIN": "", "PASSWD": "", "URL": "stat.sovatelecom.ru", "domain": "", "subm": "Вход"}
    # check_http_reply(session.post("https://stat.sovatelecom.ru/login_user.htms", data=post_data))

    response = session.get("https://stats.tis-dialog.ru/index.php?phnumber=") #phnumber=login
    # response = session.get("https://stat.sovatelecom.ru/main.htms")
    check_http_reply(response)

    # import ipdb
    # ipdb.set_trace()

def main():
    exit_code = 0
    try:
        parser = argparse.ArgumentParser(description="Custom script to check balance and write status to a file")
        parser.add_argument("status_file_name", help="File to write status information to")
        parser.add_argument("login", help="User name")
        parser.add_argument("password", help="password")
        parser.add_argument('-w', '--warning-balance', dest='warning_balance', type=int, default=200,
            help='Minimal balance to cause warning state (default: %(default)d)')
        parser.add_argument('-c', '--critical-balance', dest='critical_balance', type=int, default=100,
            help='Minimal balance to cause critical state (default: %(default)d)')
        parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
            help='Display verbose debug messages')

        options = parser.parse_args()
        print(options.status_file_name)
        # if options.warning_hours > options.critical_hours:
        #     print("Error: critical threshold cannot be less than warning")
        #     return (STATUS_UNKNOWN)

        # exit_code = check_file(options.status_file_name, options.warning_hours,
        #   options.critical_hours)

    except Exception as e:
        write_status("CRITICAL", "Unhandled exception: {}".format(e))
        exit_code = 1

    return (exit_code)

if __name__ == '__main__':
    sys.exit(main())