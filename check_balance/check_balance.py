#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import requests
import datetime
import dateutil.relativedelta
import dateutil.tz
import time
import argparse
import locale
import traceback
import lxml.etree

locale.setlocale(locale.LC_ALL, '')

options = None

def print_with_timestamp(msg):
    print (u"{} {}".format(datetime.datetime.now().strftime("%x %X"), msg))

def print_verbose(verbose_msg):
    if options.verbose:
        print_with_timestamp(verbose_msg)

def check_http_reply(reply):
    if reply.status_code != 200:
        raise Exception("HTTP call has failed. Status code: {code} - {text}".format(code=reply.status_code, text=reply.text))

def write_status(status_code, status_text):
    print_with_timestamp("Status {} - {}".format(status_code,status_text))

    if not options is None:
        with open(options.status_file_name, "w") as f:
            timestamp = datetime.datetime.now(dateutil.tz.tzoffset(None, -time.altzone)).replace(microsecond=0).isoformat()
            f.write(timestamp + ";" + status_code + ";" + status_text)

def get_next_withdrawal_date():
    if datetime.date.today().day >= options.withdrawal_day:
        month_offset = 1
    else:
        month_offset = 0
    return datetime.date.today() + dateutil.relativedelta.relativedelta(months=month_offset, day=options.withdrawal_day)

def do_check_balance():
    session = requests.session()
    if (options.provider in ["dialog", "dialog-new"]):
        check_http_reply(session.get("https://stats.tis-dialog.ru/"))
        post_data = {"login": options.login, "passv": options.password}
        check_http_reply(session.post("https://stats.tis-dialog.ru/index.php", data=post_data))
        response = session.get("https://stats.tis-dialog.ru/index.php?phnumber={}".format(options.login))
        check_http_reply(response)
        # Fix encoding
        response.encoding = response.apparent_encoding
        # Easy way to find xpath is to save reply as html, open in Chrome and
        # use "Inspect" > right click "Copy" > "Copy XPath"
        balance_str = lxml.etree.HTML(response.text).xpath('/html/body/div/main/div[2]/table[1]/tr[4]/td[2]')[0].text
        print_verbose(u"Balance as string: {}".format(balance_str))
        balance = float(balance_str.replace(u" руб.", u"").replace(u",", u"."))
        if options.provider == "dialog-new":
            response = session.get("https://stats.tis-dialog.ru/index.php?mod=payments")
            check_http_reply(response)
            response.encoding = response.apparent_encoding
            if options.verbose:
                print_verbose("Deposits and withdrawals:")
                for table_row in lxml.etree.HTML(response.text).xpath('/html/body/div/main/div[2]/table[1]/tr'):
                    print(u"    " + u"; ".join(i.text for i in table_row.getchildren()))
            # lxml.etree.tostring(lxml.etree.HTML(response.text).xpath('/html/body/div/main/div[2]/table[1]/tr[td[1][text() = "07.07.2023"]]')[2])
            # import ipdb
            # ipdb.set_trace()
            todays_withdrawal_entry = lxml.etree.HTML(response.text).xpath(
                '/html/body/div/main/div[2]/table[1]/tr[td[1][text() = "{}"] and td[2][text() = "{}"]]'.format(
                    # "07.07.2023",
                    # .today()?
                    datetime.datetime.now().strftime("%d.%m.%Y"),
                    "-{},00".format("{:,d}".format(options.withdrawal_amount).replace(",", " "))
                )
            )
            todays_withdrawal = len(todays_withdrawal_entry) != 0
        session.get("https://stats.tis-dialog.ru/index.php?mod=exit")
    else:
        check_http_reply(session.get("https://stat.sovatelecom.ru/"))
        post_data = {"LOGIN": options.login, "PASSWD": options.password,
          "URL": "stat.sovatelecom.ru", "domain": "", "subm": "Вход"}
        check_http_reply(session.post("https://stat.sovatelecom.ru/login_user.htms", data=post_data))
        response = session.get("https://stat.sovatelecom.ru/main.htms")
        check_http_reply(response)
        balance_str = lxml.etree.HTML(response.text).xpath('//*[@id="onyma_stat_main_fin"]/table[1]/tr[2]/td[1]/table[2]/tr[1]/td[1]/table[1]/tr[last()]/td[2]')[0].text
        print_verbose(u"Balance as string: {}".format(balance_str))
        balance = float(balance_str.replace(u"Остаток\xa0:\xa0", u"").replace(u" RUB", u"").replace(u",", u""))

    # DEBUG
    # # balance = 3.0
    # balance = 454
    # todays_withdrawal = False
    # # todays_withdrawal = True

    print_verbose("Balance: {}".format(balance))

    if options.provider == "dialog-new":
        next_withdrawal_date = get_next_withdrawal_date()
        if datetime.datetime.today().day == options.withdrawal_day:
            if not todays_withdrawal:
                next_withdrawal_date = datetime.datetime.today().date()
        if balance < 0:
            next_withdrawal_date = datetime.datetime.today().date()
        days_until_withdrawal = (next_withdrawal_date - datetime.date.today()).days

        status_text = "Balance: {}, next withdrawal: {} (in {} day(s)), account: {}, amount: {}".format(
            balance,
            next_withdrawal_date,
            days_until_withdrawal,
            options.login,
            options.withdrawal_amount
        )
        if balance < options.withdrawal_amount:
            if days_until_withdrawal < options.critical_threshold:
                write_status("CRITICAL", status_text)
            elif days_until_withdrawal < options.warning_threshold:
                write_status("WARNING", status_text)
            else:
                write_status("OK", status_text)
    else:
        if balance < options.critical_threshold:
            write_status("CRITICAL", "Balance {} is less than critical threshold of {}".format(balance, options.critical_threshold))
        elif balance < options.warning_threshold:
            write_status("WARNING", "Balance {} is less than warning threshold of {}".format(balance, options.warning_threshold))
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
            choices=["dialog", "dialog-new", "sovatel"], help='ISP type (default: %(default)s)')
        parser.add_argument('-w', '--warning-threshold', dest='warning_threshold', type=int, default=200,
            help='Minimal balance/days to cause warning state (default: 200₽ or 10 days)')
        parser.add_argument('-c', '--critical-threshold', dest='critical_threshold', type=int, default=100,
            help='Minimal balance/days to cause critical state (default: 100₽ or 5 days)')
        parser.add_argument('-d', '--withdrawal-day', dest='withdrawal_day', type=int, default=1,
            help='Day of monthly withdrawal (dialog-new only, default: %(default)d)')
        parser.add_argument('-a', '--withdrawal-amount', dest='withdrawal_amount', type=int, default=455,
            help='Amount of monthly withdrawal (dialog-new only, default: %(default)d)')
        parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
            help='Display verbose debug messages')

        global options
        options = parser.parse_args()
        if options.warning_threshold < options.critical_threshold:
            write_status("UNKNOWN", "Error: warning threshold cannot be less than critical")

        if options.provider == "dialog-new":
            if options.warning_threshold == 200:
                options.warning_threshold = 10
            if options.critical_threshold == 100:
                options.critical_threshold = 5

        print_with_timestamp("Checking balance for user {} on {}".format(options.login, options.provider))
        print_verbose("Status file name: {}".format(options.status_file_name))

        do_check_balance()

    except Exception as e:
        if options.verbose:
            print(traceback.format_exc())
        write_status("CRITICAL", "Unhandled exception: {}".format(e))
        exit_code = 1

    return (exit_code)

if __name__ == '__main__':
    sys.exit(main())