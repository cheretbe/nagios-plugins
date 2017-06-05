import sys
import mock
import unittest
import datetime
import freezegun
import dateutil.tz

import check_status_file

if sys.version_info >= (3,0,0):
    BUILTIN_OPEN_NAME = "builtins.open"
else:
    BUILTIN_OPEN_NAME = "__builtin__.open"

class get_timedelta_from_now_UnitTests(unittest.TestCase):
    """Unit tests for 'get_timedelta_from_now' function"""

    # freeze_time sets UTC time
    # Here local time is 16:21, UTC time is 18:21
    @freezegun.freeze_time("2017-01-14 18:21:34", tz_offset=-2)
    def test_timestamp_is_naive(self):
        """Should compare dates correctly when timestamp doesn't contain timezone information"""

        ret_val = check_status_file.get_timedelta_from_now(datetime.datetime(
            year=2017, month=1, day=14, hour=16, minute=21, second=34))
        self.assertEqual(ret_val, 0)

        # 4*3600 + 21*60 + 24 = 15684
        ret_val = check_status_file.get_timedelta_from_now(datetime.datetime(
            year=2017, month=1, day=14, hour=12, minute=0, second=10))
        self.assertEqual(ret_val, 15684)

    # freeze_time sets UTC time
    # Here local time is 2017-01-01 02:15:11, UTC time is 2016-12-31 22:15:11
    @freezegun.freeze_time("2016-12-31 22:15:11", tz_offset=+4)
    def test_timestamp_with_timezone(self):
        """Should compare dates correctly when timestamp contains timezone information"""

        # their time: 2017-01-01T02:15:11+04:00 (same as local)
        ret_val = check_status_file.get_timedelta_from_now(datetime.datetime(
            year=2017, month=1, day=1, hour=2, minute=15, second=11,
            tzinfo=dateutil.tz.tzoffset(None, +14400)))
        self.assertEqual(ret_val, 0)

        # their time: 2016-12-31T22:15:11+00:00 (same as UTC local)
        ret_val = check_status_file.get_timedelta_from_now(datetime.datetime(
            year=2016, month=12, day=31, hour=22, minute=15, second=11,
            tzinfo=dateutil.tz.tzoffset('UTC', 0)))
        self.assertEqual(ret_val, 0)

        # their time: 2016-12-31T21:25:30+00:30 (2016-12-31T20:55:30 UTC, 2017-01-01T00:55:30 local)
        # 1*3600 + 19*60 + 41 = 4781
        ret_val = check_status_file.get_timedelta_from_now(datetime.datetime(
            year=2016, month=12, day=31, hour=21, minute=25, second=30,
            tzinfo=dateutil.tz.tzoffset(None, +1800)))
        self.assertEqual(ret_val, 4781)


@mock.patch("os.path.isfile")
@mock.patch("check_status_file.print_stdout")
@mock.patch("check_status_file.get_timedelta_from_now")
class check_file_UnitTests(unittest.TestCase):
    """Unit tests for 'check_file' function"""

    def test_file_doesnt_exist(self, get_timedelta_from_now_mock, print_stdout_mock,
            os_path_isfile_mock):
        """Should return critical status if status file doesn't exist"""
        os_path_isfile_mock.return_value = False
        ret_val = check_status_file.check_file("file_name", 10, 20)
        self.assertEqual(ret_val, 2)
        print_stdout_mock.assert_called_with("CRITICAL: status file 'file_name' does not exist")

    # Mocked readline fails on empty file (https://github.com/testing-cabal/mock/issues/382)
    # Because of that we test empty file condition only in functional test
    @mock.patch(BUILTIN_OPEN_NAME, new_callable=mock.mock_open, read_data="wrong_data")
    @freezegun.freeze_time("2012-01-14 03:21:34", tz_offset=-4)
    def test_file_exists_wrong_data(self, open_mock, get_timedelta_from_now_mock,
            print_stdout_mock, os_path_isfile_mock):
        """Should return critical status if status file doesn't contain valid data"""

        os_path_isfile_mock.return_value = True
        get_timedelta_from_now_mock.return_value = 3600 # 1 hour

        self.assertEqual(check_status_file.check_file("file_name", 10, 20), 2)
        print_stdout_mock.assert_called_with("CRITICAL: wrong status data in 'file_name'")

        open_mock.side_effect = [mock.mock_open(read_data="wrong_date;status;description").return_value]
        self.assertEqual(check_status_file.check_file("file_name", 10, 20), 2)
        print_stdout_mock.assert_called_with("Wrong date/time format in file 'file_name': wrong_date")

        open_mock.side_effect = [mock.mock_open(read_data="2017-05-30T11:12:05+02:00;wrong_status;description").return_value]
        self.assertEqual(check_status_file.check_file("file_name", 10, 20), 2)
        print_stdout_mock.assert_called_with("Wrong status code in file 'file_name': wrong_status")

        # Both upper and lowercase codes are fine
        open_mock.side_effect = [mock.mock_open(read_data="2017-05-30T11:12:05+02:00;OK;description").return_value]
        self.assertEqual(check_status_file.check_file("file_name", 10, 20), 0)
        open_mock.side_effect = [mock.mock_open(read_data="2017-05-30T11:12:05+02:00;ok;description").return_value]
        self.assertEqual(check_status_file.check_file("file_name", 10, 20), 0)



# 2Check
# https://stackoverflow.com/questions/4199700/python-how-do-i-make-temporary-files-in-my-test-suite
# https://docs.pytest.org/en/latest/tmpdir.html
