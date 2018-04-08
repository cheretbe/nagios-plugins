#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import requests
import datetime
import dateutil.tz
import time
import argparse
import locale
import lxml.etree

locale.setlocale(locale.LC_ALL, '')

options = None

def print_with_timestamp(msg):
    print (u"{} {}".format(datetime.datetime.now().strftime("%x %X"), msg))

def print_debug(debug_msg):
    if options.debug:
        print_with_timestamp(debug_msg)

def check_http_reply(reply):
    if reply.status_code != 200:
        raise Exception("HTTP call has failed. Status code: {code} - {text}".format(code=reply.status_code, text=reply.text))

def write_status(status_code, status_text):
    print_with_timestamp("Status {} - {}".format(status_code,status_text))

    if not options is None:
        with open(options.status_file_name, "w") as f:
            timestamp = datetime.datetime.now(dateutil.tz.tzoffset(None, -time.altzone)).replace(microsecond=0).isoformat()
            f.write(timestamp + ";" + status_code + ";" + status_text)

def do_check_balance():
    session = requests.session()
    if (options.provider == "dialog"):
        check_http_reply(session.get("https://stats.tis-dialog.ru/"))
        post_data = {"login": options.login, "passv": options.password}
        check_http_reply(session.post("https://stats.tis-dialog.ru/index.php", data=post_data))
        response = session.get("https://stats.tis-dialog.ru/index.php?phnumber={}".format(options.login))
        check_http_reply(response)
        # Fix encoding
        response.encoding = response.apparent_encoding
        # Easy way to find xpath is to save reply as html, open in Chrome and
        # use "Inspect" > right click "Copy" > "Copy XPath"
        balance_str = lxml.etree.HTML(response.text).xpath('/html/body/div/main/div[2]/table[1]/tr[6]/td[2]')[0].text
        balance = float(balance_str.replace(u" руб. ", u"").replace(u",", u"."))
    else:
        check_http_reply(session.get("https://stat.sovatelecom.ru/"))
        post_data = {"LOGIN": options.login, "PASSWD": options.password,
          "URL": "stat.sovatelecom.ru", "domain": "", "subm": "Вход"}
        check_http_reply(session.post("https://stat.sovatelecom.ru/login_user.htms", data=post_data))
        response = session.get("https://stat.sovatelecom.ru/main.htms")
        check_http_reply(response)
        balance_str = lxml.etree.HTML(response.text).xpath('//*[@id="onyma_stat_main_fin"]/table[1]/tr[2]/td[1]/table[2]/tr[1]/td[1]/table[1]/tr[4]/td[2]')[0].text
        balance = float(balance_str.replace(u"Остаток\xa0:\xa0", u"").replace(u" RUB", u""))

    # import ipdb
    # ipdb.set_trace()

    print_debug(u"Balance as string: {}".format(balance_str))
    print_debug("Balance: {}".format(balance))

    if balance < options.critical_balance:
        write_status("CRITICAL", "Balance {} is less than critical threshold of {}".format(balance, options.critical_balance))
    elif balance < options.warning_balance:
        write_status("WARNING", "Balance {} is less than warning threshold of {}".format(balance, options.warning_balance))
    else:
        write_status("OK", "Balance is {}".format(balance))

def main():
    exit_code = 0
    try:
        parser = argparse.ArgumentParser(description="Custom script to check balance and write status to a file")
        parser.add_argument("status_file_name", help="File to write status information to")
        parser.add_argument("login", help="User name")
        parser.add_argument("password", help="password")
        parser.add_argument('-p', '--provider', dest='provider', default="dialog",
            choices=["dialog", "sovatel"], help='ISP type (default: %(default)s)')
        parser.add_argument('-w', '--warning-balance', dest='warning_balance', type=int, default=200,
            help='Minimal balance to cause warning state (default: %(default)d)')
        parser.add_argument('-c', '--critical-balance', dest='critical_balance', type=int, default=100,
            help='Minimal balance to cause critical state (default: %(default)d)')
        parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
            help='Display verbose debug messages')

        global options
        options = parser.parse_args()
        if options.warning_balance < options.critical_balance:
            write_status("UNKNOWN", "Error: warning threshold cannot be less than critical")

        print_with_timestamp("Checking balance for user {} on {}".format(options.login, options.provider))
        print_debug("Status file name: {}".format(options.status_file_name))

        do_check_balance()

    except Exception as e:
        write_status("CRITICAL", "Unhandled exception: {}".format(e))
        exit_code = 1

    return (exit_code)

if __name__ == '__main__':
    sys.exit(main())