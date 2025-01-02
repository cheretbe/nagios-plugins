#!/usr/bin/env python3

import argparse
import sys
import datetime
import traceback
import locale
import requests
import json
import types

# Nagios status codes
STATUS_UNKNOWN = -1
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_NAMES = {
    STATUS_OK: "OK",
    STATUS_WARNING: "WARNING",
    STATUS_CRITICAL: "CRITICAL",
    STATUS_UNKNOWN: "UNKNOWN",
}

locale.setlocale(locale.LC_ALL, "")


def print_with_timestamp(msg):
    print("{} {}".format(datetime.datetime.now().strftime("%x %X"), msg))


def print_verbose(verbose, verbose_msg):
    if verbose:
        print_with_timestamp(verbose_msg)


def check_http_reply(reply):
    if reply.status_code != 200:
        raise Exception(
            "HTTP call has failed. Status code: {code} - {text}".format(
                code=reply.status_code, text=reply.text
            )
        )


def get_expiry_dates(args):
    result = types.SimpleNamespace(services=[], status_string="")

    session = requests.session()

    if args.provider == "pureservers":
        # https://docs.pureservers.org/
        post_data = json.dumps(
            {"region": "BY", "email": args.login, "password": args.password}
        )
        login_response = session.post(
            "https://cp.pureservers.org/api/auth/login",
            headers={"Content-Type": "application/json"},
            data=post_data,
        )
        check_http_reply(login_response)
        server_list_response = session.get(
            "https://cp.pureservers.org/api/servers/list",
            headers={"session": login_response.headers["session"]},
        )
        check_http_reply(server_list_response)
        for server in server_list_response.json():
            service_obj = types.SimpleNamespace()
            # [!] 'expires_at' is in milliseconds, dividing it by 1000
            service_obj.expires_at = datetime.date.fromtimestamp(
                server["expires_at"] / 1000
            )
            service_obj.days_left = (
                service_obj.expires_at - datetime.date.today()
            ).days
            service_obj.description = "{id} ({ip}): {date} ({days} day(s))".format(
                id=server["num_id"],
                ip=server["primary_ipv4"],
                date=service_obj.expires_at.strftime("%Y-%m-%d"),
                days=service_obj.days_left,
            )
            result.services.append(service_obj)
            print_verbose(verbose=args.verbose, verbose_msg=service_obj)

    elif args.provider == "62yun":
        import playwright.sync_api

        p = playwright.sync_api.sync_playwright().start()
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://62yun.ru/")

        page.locator(".header__container_user_button-group_button").click()
        page.locator(".modal-auth-email").fill(args.login)
        page.locator(".modal-auth-password").fill(args.password)

        page.get_by_role("button", name="Войти по email").click()
        # https://playwright.dev/python/docs/api/class-frame#frame-wait-for-url
        playwright.sync_api.expect(page.get_by_text("Мои серверы")).to_be_visible()

        page.get_by_text("Мои серверы").click()
        playwright.sync_api.expect(
            page.locator(".myservers__servers-group")
        ).to_be_visible()

        service_data_locator = page.locator(".myservers__server").filter(
            has_not_text="Заказать Сервер"
        )
        for i in range(service_data_locator.count()):
            # Expected data:
            # IP:193.17.183.102\nvpn-es\n19.01.2025\netc..
            service_data = service_data_locator.nth(i).inner_text().split("\n")
            service_expiry_data = service_data[2].split(".")

            service_obj = types.SimpleNamespace()
            service_obj.expires_at = datetime.date(
                year=int(service_expiry_data[2]),
                month=int(service_expiry_data[1]),
                day=int(service_expiry_data[0]),
            )
            service_obj.days_left = (
                service_obj.expires_at - datetime.date.today()
            ).days
            service_obj.description = "{id} ({ip}): {date} ({days} day(s))".format(
                id=service_data[1],
                ip=service_data[0],
                date=service_obj.expires_at.strftime("%Y-%m-%d"),
                days=service_obj.days_left,
            )
            result.services.append(service_obj)
            print_verbose(verbose=args.verbose, verbose_msg=service_obj)

        page.locator(".header__container_user_button-group > div:nth-child(2)").click()
        playwright.sync_api.expect(
            page.get_by_role("button", name="Выйти из аккаунта")
        ).to_be_visible()
        page.get_by_role("button", name="Выйти из аккаунта").click()

    result.status_string = "; ".join(x.description for x in result.services)
    return result


def main(args):
    check_status = STATUS_OK
    if args.warning_threshold < args.critical_threshold:
        check_status = STATUS_UNKNOWN
        print("Error: warning threshold cannot be less than critical")

    print_verbose(
        verbose=args.verbose,
        verbose_msg="Checking expiration dates for user {} on {}".format(
            args.login, args.provider
        ),
    )

    # expiry_dates = types.SimpleNamespace(
    #     services=[
    #         types.SimpleNamespace(
    #             # year, month, day
    #             expires_at=datetime.date(2025, 1, 21),
    #             description="Custom debug date",
    #         )
    #     ],
    #     status_string="Custom debug date",
    # )
    # expiry_dates.services[0].days_left = (
    #     expiry_dates.services[0].expires_at - datetime.date.today()
    # ).days
    # print(expiry_dates)
    expiry_dates = get_expiry_dates(args)

    min_days_left = expiry_dates.services[0].days_left
    for service in expiry_dates.services:
        if service.days_left < min_days_left:
            min_days_left = service.days_left

    if min_days_left < args.critical_threshold:
        check_status = STATUS_CRITICAL
    elif min_days_left < args.warning_threshold:
        check_status = STATUS_WARNING

    if min_days_left < 0:
        print(f"Expired {abs(min_days_left)} day(s) ago. {expiry_dates.status_string}")
    else:
        print(f"Expires in {min_days_left} day(s). {expiry_dates.status_string}")
    return check_status


if __name__ == "__main__":
    exit_code = STATUS_OK
    try:
        parser = argparse.ArgumentParser(
            exit_on_error=False,
            description="Custom script to check expiration date of a service",
        )

        parser.add_argument("login", help="User name")
        parser.add_argument("password", help="password")
        parser.add_argument(
            "-p",
            "--provider",
            dest="provider",
            default="pureservers",
            choices=["pureservers", "62yun"],
            help="Service provider (default: %(default)s)",
        )
        parser.add_argument(
            "-w",
            "--warning-threshold",
            dest="warning_threshold",
            type=int,
            default=10,
            help="Minimal days to cause warning state (default: 10 days)",
        )
        parser.add_argument(
            "-c",
            "--critical-threshold",
            dest="critical_threshold",
            type=int,
            default=5,
            help="Minimal days to cause critical state (default: 5 days)",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            default=False,
            help="Display verbose debug messages",
        )

        args = parser.parse_args()
        exit_code = main(args)
    except Exception as e:
        if args.verbose if "args" in globals() else False:
            print(traceback.format_exc())
        print("Unhandled exception: {}".format(e))
        exit_code = STATUS_CRITICAL

    print_verbose(
        verbose=(args.verbose if "args" in globals() else False),
        verbose_msg=(f"Status: {STATUS_NAMES[exit_code]}"),
    )
    sys.exit(exit_code)
