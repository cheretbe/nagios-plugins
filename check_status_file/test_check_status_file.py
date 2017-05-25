import mock
import unittest

import check_status_file

@mock.patch("os.path.isfile")
# @mock.patch("builtins.print")
# @mock.patch("builtins.print",autospec=True,side_effect=print)
# @mock.patch('check_status_file.print', create=True)
@mock.patch("check_status_file.print_stdout")
class check_file_UnitTests(unittest.TestCase):
  """Unit tests for 'check_file' function"""

  def test_aaa(self, print_stdout_mock, os_path_isfile_mock):
    """Should return critical status if status file doesn't exist"""
    os_path_isfile_mock.return_value = False
    ret_val = check_status_file.check_file("file_name", 10, 20)
    self.assertEqual(ret_val, 2)
    print_stdout_mock.assert_called_with("CRITICAL: status file 'file_name' does not exist")