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

    open_mock.side_effect = [mock.mock_open(read_data="11;22;33").return_value]
    # open_mock.side_effect = "11;22;33"
    check_status_file.check_file("file_name", 10, 20)
    # open_mock.side_effect = (mock.mock_open().return_value,)
    # check_status_file.check_file("file_name", 10, 20)