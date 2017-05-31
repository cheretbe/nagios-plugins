import sys
import mock
import unittest

import check_status_file

if sys.version_info >= (3,0,0):
  BUILTIN_OPEN_NAME = "builtins.open"
else:
  BUILTIN_OPEN_NAME = "__builtin__.open"

@mock.patch("os.path.isfile")
@mock.patch("check_status_file.print_stdout")
class check_file_UnitTests(unittest.TestCase):
  """Unit tests for 'check_file' function"""

  def test_file_doesnt_exist(self, print_stdout_mock, os_path_isfile_mock):
    """Should return critical status if status file doesn't exist"""
    os_path_isfile_mock.return_value = False
    ret_val = check_status_file.check_file("file_name", 10, 20)
    self.assertEqual(ret_val, 2)
    print_stdout_mock.assert_called_with("CRITICAL: status file 'file_name' does not exist")

  # Mocked readline fails on empty file (https://github.com/testing-cabal/mock/issues/382)
  # Because of that we test empty file condition only in functional test
  @mock.patch(BUILTIN_OPEN_NAME, new_callable=mock.mock_open, read_data="wrong_data")
  def test_file_exists_wrong_data(self, open_mock, print_stdout_mock, os_path_isfile_mock):
    """Should return critical status if status file doesn't contain valid data"""
    os_path_isfile_mock.return_value = True

    self.assertEqual(check_status_file.check_file("file_name", 10, 20), 2)
    print_stdout_mock.assert_called_with("CRITICAL: wrong status data in 'file_name'")

    open_mock.side_effect = [mock.mock_open(read_data="wrong_date;status;description").return_value]
    self.assertEqual(check_status_file.check_file("file_name", 10, 20), 2)
    print_stdout_mock.assert_called_with("Wrong date/time format in file 'file_name': wrong_date")

    open_mock.side_effect = [mock.mock_open(read_data="2017-05-30T11:12:05+02:00;wrong_status;description").return_value]
    self.assertEqual(check_status_file.check_file("file_name", 10, 20), 2)
    print_stdout_mock.assert_called_with("Wrong status code in file 'file_name': wrong_status")

    # Both upper and lowercase are fine
    open_mock.side_effect = [mock.mock_open(read_data="2017-05-30T11:12:05+02:00;OK;description").return_value]
    self.assertEqual(check_status_file.check_file("file_name", 10, 20), -1)
    # print_stdout_mock.assert_called_with("Wrong status code in file 'file_name': wrong_status")
    open_mock.side_effect = [mock.mock_open(read_data="2017-05-30T11:12:05+02:00;ok;description").return_value]
    self.assertEqual(check_status_file.check_file("file_name", 10, 20), -1)

    open_mock.side_effect = [mock.mock_open(read_data="2017-05-30T11:12:05;ok;description").return_value]
    self.assertEqual(check_status_file.check_file("file_name", 10, 20), -1)




    # open_mock.side_effect = (mock.mock_open().return_value,)
    # check_status_file.check_file("file_name", 10, 20)


# 2Check
# https://stackoverflow.com/questions/4199700/python-how-do-i-make-temporary-files-in-my-test-suite
# https://docs.pytest.org/en/latest/tmpdir.html