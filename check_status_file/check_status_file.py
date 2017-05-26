#!/usr/bin/env python

import sys
import os
import argparse
import dateutil.parser

# Nagios status codes
STATUS_UNKNOWN  = -1
STATUS_OK       =  0
STATUS_WARNING  =  1
STATUS_CRITICAL =  2

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
  # Status can be one of the following values: OK, WARNING, ERROR
  with open(status_file_name, "r") as f:
    status_data = f.read().split(";")
  print(status_data)
  if len(status_data) != 3:
    print_stdout("CRITICAL: wrong status data in'{}'".format(status_file_name))
    return(STATUS_CRITICAL)

  print(status_data)
  return(STATUS_UNKNOWN)

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
    exit_code = check_file(options.status_file_name, options.warning_hours,
      options.critical_hours)

  except Exception as e:
    print("Unhandled exception: {}".format(e))
    exit_code = STATUS_CRITICAL

  return (exit_code)

if __name__ == '__main__':
  sys.exit(main())