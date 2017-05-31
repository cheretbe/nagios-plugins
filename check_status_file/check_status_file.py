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

# String representations of valid valid status codes
STATUS_CODES = {
  "OK":       STATUS_OK,
  "WARNING":  STATUS_WARNING,
  "ERROR":    STATUS_CRITICAL,
  "CRITICAL": STATUS_CRITICAL
}

def print_stdout(string_to_print):
  print(string_to_print)

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

  # Check if status timestamp is naive, we assume that it is in the same timezone as
  # local system. If it contains timezone information, we convert local time to UTC
  # with tzinfo to calculate the difference
  # 
  # http://techblog.thescore.com/2015/11/03/timezones-in-python/
  # http://pytz.sourceforge.net/#localized-times-and-date-arithmetic
  # https://stackoverflow.com/questions/5802108/how-to-check-if-a-datetime-object-is-localized-with-pytz
  if (status_timestamp.tzinfo is None) or (status_timestamp.tzinfo.utcoffset(status_timestamp) is None):
    print("naive")
    # Naive
    status_age = (datetime.datetime.now() - status_timestamp).total_seconds()
  else:
    print("timezone")
    # With timezone
    status_age = (pytz.utc.localize(datetime.datetime.utcnow()) - status_timestamp).total_seconds()

  print(status_age)
  print(status_code)
  print(status_timestamp)
  print(str(status_timestamp))
  print("We are the {:%d, %b %Y}".format(status_timestamp))
  return(STATUS_UNKNOWN)
  # http://techblog.thescore.com/2015/11/03/timezones-in-python/
  # http://pytz.sourceforge.net/#localized-times-and-date-arithmetic

  # import datetime
  # import dateutil.parser
  # import pytz

  # check_date = dateutil.parser.parse("2017-05-30T11:12:05+02:00")
  # local_date = pytz.utc.localize(datetime.datetime.utcnow())
  # (local_date - check_date).total_seconds()

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