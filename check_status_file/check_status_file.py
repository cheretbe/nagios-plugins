#!/usr/bin/env python

import sys
import os
import argparse
import datetime
import dateutil.parser
import pytz

# Nagios status codes
STATUS_UNKNOWN  = -1
STATUS_OK       =  0
STATUS_WARNING  =  1
STATUS_CRITICAL =  2

# String representations of valid status codes
STATUS_CODES = {
    "OK":       STATUS_OK,
    "WARNING":  STATUS_WARNING,
    "ERROR":    STATUS_CRITICAL,
    "CRITICAL": STATUS_CRITICAL
}

def print_stdout(string_to_print):
    print(string_to_print)

def get_timedelta_from_now(other_timestamp):
    # If other timestamp is naive, we assume that it is in the same timezone as
    # local system. If it contains timezone information, we convert local time to UTC
    # with tzinfo to calculate the difference
    #
    # http://techblog.thescore.com/2015/11/03/timezones-in-python/
    # http://pytz.sourceforge.net/#localized-times-and-date-arithmetic
    # https://stackoverflow.com/questions/5802108/how-to-check-if-a-datetime-object-is-localized-with-pytz
    if (other_timestamp.tzinfo is None) or (other_timestamp.tzinfo.utcoffset(other_timestamp) is None):
        # Naive
        return((datetime.datetime.now() - other_timestamp).total_seconds())
    else:
        # With timezone
        return((pytz.utc.localize(datetime.datetime.utcnow()) - other_timestamp).total_seconds())


def check_file(status_file_name, warning_hours, critical_hours):
    if not(os.path.isfile(status_file_name)):
        print_stdout("CRITICAL: status file '{}' does not exist".format(status_file_name))
        return(STATUS_CRITICAL)

    # Status data is expected as a single semicolon-delimited line in the
    # following format:
    # <timestamp>;<status>;<text description>
    # Timestamp is in ISO 8601 format.
    # Status can be one of the following values: OK, WARNING, ERROR, CRITICAL
    with open(status_file_name, "r") as f:
        status_data = f.readline().split(";")

    if len(status_data) != 3:
        print_stdout("CRITICAL: wrong status data in '{}'".format(status_file_name))
        return(STATUS_CRITICAL)

    try:
        status_timestamp = dateutil.parser.parse(status_data[0])
    except ValueError as e:
        print_stdout("Wrong date/time format in file '{}': {}".format(status_file_name, status_data[0]))
        return(STATUS_CRITICAL)

    try:
        status_code = STATUS_CODES[status_data[1].upper()]
    except KeyError as e:
        print_stdout("Wrong status code in file '{}': {}".format(status_file_name, status_data[1]))
        return(STATUS_CRITICAL)

    status_age = get_timedelta_from_now(status_timestamp)
    status_age_hours_str = "{:.2f} hour(s)".format(status_age / 3600)

    return_value = STATUS_UNKNOWN

    if status_age <= datetime.timedelta(hours=warning_hours).seconds:
        # Last status change is under the warning threshold
        if status_code == STATUS_OK:
            print_stdout("OK - {} [{}, {} ago]".format(status_data[2],
                status_data[0], status_age_hours_str))
            return_value = STATUS_OK
        elif status_code == STATUS_WARNING:
            print_stdout("WARNING - {} [{}, {} ago]".format(status_data[2],
                status_data[0], status_age_hours_str))
            return_value = STATUS_WARNING
        else:
            print_stdout("CRITICAL - {} [{}, {} ago]".format(status_data[2],
                status_data[0], status_age_hours_str))
            return_value = STATUS_CRITICAL
    elif status_age <= datetime.timedelta(hours=critical_hours).seconds:
        # Last status change is over the warning threshold, but not over the critical
        if status_code == STATUS_OK:
            print_stdout("WARNING - {} since last status update is over the limit of {} hour(s) [{} - {}]".format(
                status_age_hours_str, warning_hours, status_data[0], status_data[2]))
            return_value = STATUS_WARNING
        elif status_code == STATUS_WARNING:
            print_stdout("WARNING - {} since last status update is over the limit of {} hour(s) [{} - {}]".format(
                status_age_hours_str, warning_hours, status_data[0], status_data[2]))
            return_value = STATUS_WARNING
        else:
            print_stdout("WARNING+CRITICAL - {} since last status update is over the limit of {} hour(s) [{} - {}]".format(
                status_age_hours_str, warning_hours, status_data[0], status_data[2]))
            return_value = STATUS_CRITICAL
    else:
        # Last status change is over the critical threshold
        print_stdout("CRITICAL - {} since last status update is over the limit of {} hour(s) [{} - {}]".format(
            status_age_hours_str, critical_hours, status_data[0], status_data[2]))
        return_value = STATUS_CRITICAL

    return(return_value)

def main():
    exit_code = STATUS_UNKNOWN
    try:
        parser = argparse.ArgumentParser(description="Nagios plugin to report status from custom file")
        parser.add_argument("status_file_name", help="File to read status information from")
        parser.add_argument('-w', '--warning-hours', dest='warning_hours', type=int, default=25,
          help='Number of hours since last change to cause warning state (default: %(default)d)')
        parser.add_argument('-c', '--critical-hours', dest='critical_hours', type=int, default=49,
          help='Number of hours since last change to cause critical state (default: %(default)d)')

        options = parser.parse_args()
        if options.warning_hours > options.critical_hours:
            print("Error: critical threshold cannot be less than warning")
            return (STATUS_UNKNOWN)

        exit_code = check_file(options.status_file_name, options.warning_hours,
          options.critical_hours)

    except Exception as e:
        print("Unhandled exception: {}".format(e))

    return (exit_code)

if __name__ == '__main__':
    sys.exit(main())
