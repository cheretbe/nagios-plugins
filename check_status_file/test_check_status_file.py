import mock
import unittest

import check_status_file

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

  @mock.patch("__builtin__.open", new_callable=mock.mock_open, read_data="")
  def test_file_exists_wrong_data(self, open_mock, print_stdout_mock, os_path_isfile_mock):
    """Should return critical status if status file doesn't contain valid data"""
    os_path_isfile_mock.return_value = True

    self.assertEqual(check_status_file.check_file("file_name", 10, 20), 2)
    print_stdout_mock.assert_called_with("CRITICAL: wrong status data in'file_name'")

    open_mock.side_effect = [mock.mock_open(read_data="11;22;33").return_value]
    # open_mock.side_effect = "11;22;33"
    check_status_file.check_file("file_name", 10, 20)
    # open_mock.side_effect = (mock.mock_open().return_value,)
    # check_status_file.check_file("file_name", 10, 20)