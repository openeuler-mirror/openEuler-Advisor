#!/usr/bin/env python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
#
# ******************************************************************************/
"""
Test cases for advisors/atomgit.py
These tests can run independently without actual API calls.

Run from project root directory:
    python3 -m unittest tests.test_atomgit -v

Or run directly:
    python3 tests/test_atomgit.py
"""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime

# Add parent directory to path to import advisors module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advisors.atomgit import Atomgit


class TestAtomgitSingleton(unittest.TestCase):
    """Test singleton pattern of Atomgit class"""

    def test_singleton_instance(self):
        """Test that Atomgit is a singleton"""
        # Mock token file to avoid actual file reading
        mock_token_data = json.dumps({
            "access_token": "test_token",
            "user": "test_user"
        })

        # Mock helper file responses
        import base64
        mock_helper_content = base64.b64encode(b'{"test": "data"}').decode()

        with patch('builtins.open', mock_open(read_data=mock_token_data)):
            with patch('advisors.atomgit.Atomgit._Atomgit__get_json') as mock_get_json:
                # Mock all helper file responses
                mock_get_json.return_value = {"content": mock_helper_content}

                instance1 = Atomgit()
                instance2 = Atomgit()

                self.assertIs(instance1, instance2, "Atomgit should return same instance")


class TestAtomgitStaticMethods(unittest.TestCase):
    """Test static methods of Atomgit class"""

    def test_get_gitee_datetime(self):
        """Test datetime parsing from gitee time string"""
        # Test normal case
        time_str = "2023-10-15T14:30:25+08:00"
        result = Atomgit.get_atomgit_datetime(time_str)
        expected = datetime(2023, 10, 15, 14, 30, 25)
        self.assertEqual(result, expected)

        # Test another timezone
        time_str = "2023-10-15T14:30:25-05:00"
        result = Atomgit.get_atomgit_datetime(time_str)
        expected = datetime(2023, 10, 15, 14, 30, 25)
        self.assertEqual(result, expected)

        # Test invalid format should raise ValueError
        with self.assertRaises(ValueError):
            Atomgit.get_atomgit_datetime("invalid format")


class TestAtomgitHelperInfoLoading(unittest.TestCase):
    """Test helper info loading in Atomgit.__init__"""

    def setUp(self):
        """Set up mock token file and network responses"""
        # Reset singleton state before each test
        if hasattr(Atomgit, '_instance'):
            delattr(Atomgit, '_instance')
        Atomgit._first_init = True

        self.mock_token_data = json.dumps({
            "access_token": "test_token",
            "user": "test_user"
        })

        # Mock helper file contents
        self.specfile_exceptions = {"test_pkg": {"dir": "dir1", "file": "file1.spec"}}
        self.version_exceptions = {"exceptions": ["pkg1", "pkg2"]}
        self.upgrade_branches = {"branches": [{"name": "master"}, {"name": "openEuler-22.03-LTS"}]}
        self.reviewer_checklist = {"checklist": ["item1", "item2"]}

        # Encode as base64 like the real API would
        import base64
        self.specfile_exceptions_b64 = base64.b64encode(
            json.dumps(self.specfile_exceptions).encode()
        ).decode()
        self.version_exceptions_b64 = base64.b64encode(
            json.dumps(self.version_exceptions).encode()
        ).decode()
        self.upgrade_branches_b64 = base64.b64encode(
            json.dumps(self.upgrade_branches).encode()
        ).decode()
        self.reviewer_checklist_b64 = base64.b64encode(
            json.dumps(self.reviewer_checklist).encode()
        ).decode()

    def test_helper_info_loading(self):
        """Test that helper info is loaded correctly during initialization"""
        # Mock sequence of API responses for helper files
        mock_responses = [
            # specfile_exceptions.yaml
            {"content": self.specfile_exceptions_b64},
            # version_exceptions.yaml
            {"content": self.version_exceptions_b64},
            # upgrade_branches.yaml
            {"content": self.upgrade_branches_b64},
            # reviewer_checklist.yaml
            {"content": self.reviewer_checklist_b64},
        ]

        with patch('builtins.open', mock_open(read_data=self.mock_token_data)):
            with patch('advisors.atomgit.Atomgit._Atomgit__get_json') as mock_get_json:
                mock_get_json.side_effect = mock_responses

                # Create instance - should load helper info
                atomgit = Atomgit()

                # Check that helper info was loaded correctly
                self.assertEqual(atomgit.helper_info["specfile_excepts"], self.specfile_exceptions)
                self.assertEqual(atomgit.helper_info["version_excepts"], self.version_exceptions)
                self.assertEqual(atomgit.helper_info["upgrade_branches"], self.upgrade_branches)
                self.assertEqual(atomgit.helper_info["reviewer_checklist"], self.reviewer_checklist)

    def test_helper_info_loading_failure(self):
        """Test initialization failure when helper file is missing"""
        with patch('builtins.open', mock_open(read_data=self.mock_token_data)):
            with patch('advisors.atomgit.Atomgit._Atomgit__get_json') as mock_get_json:
                with patch('builtins.print') as mock_print:  # Suppress error print
                    # Return empty list for first file - should raise NameError
                    # __get_json returns [] when it fails
                    mock_get_json.return_value = []

                    with self.assertRaises(NameError):
                        Atomgit()

                    # Verify error was printed
                    mock_print.assert_called()


class TestAtomgitMethods(unittest.TestCase):
    """Test various methods of Atomgit class"""

    def setUp(self):
        """Set up a Atomgit instance with mocked helper info"""
        self.mock_token_data = json.dumps({
            "access_token": "test_token",
            "user": "test_user"
        })

        # Mock helper info
        self.helper_info = {
            "specfile_excepts": {"test_pkg": {"dir": "dir1", "file": "file1.spec"}},
            "version_excepts": {"exceptions": ["pkg1", "pkg2"]},
            "upgrade_branches": {
                "branches": [
                    {"name": "master", "description": "Main branch"},
                    {"name": "openEuler-22.03-LTS", "description": "LTS branch"}
                ]
            },
            "reviewer_checklist": {"items": ["Check 1", "Check 2"]}
        }

        # Patch the __init__ to skip actual network calls and set helper info directly
        self.init_patcher = patch.object(Atomgit, '__init__', lambda self: None)
        self.init_patcher.start()

        # Create instance and set attributes manually
        self.atomgit = Atomgit()
        self.atomgit.token = json.loads(self.mock_token_data)
        self.atomgit.helper_info = self.helper_info
        self.atomgit.headers = {'User-Agent': 'test'}
        self.atomgit.src_openeuler_url = "https://api.atomgit.com/api/v5/repos/src-openeuler/{repo}/contents/"
        self.atomgit.advisor_url = "https://api.atomgit.com/api/v5/repos/openeuler/openEuler-Advisor/contents/"

    def tearDown(self):
        """Clean up patches"""
        self.init_patcher.stop()

    def test_get_branch_info(self):
        """Test get_branch_info method"""
        # Mock print to suppress warning output
        with patch('builtins.print') as mock_print:
            # Test existing branch
            result = self.atomgit.get_branch_info("master")
            expected = {"name": "master", "description": "Main branch"}
            self.assertEqual(result, expected)

            # Test another existing branch
            result = self.atomgit.get_branch_info("openEuler-22.03-LTS")
            expected = {"name": "openEuler-22.03-LTS", "description": "LTS branch"}
            self.assertEqual(result, expected)

            # Test non-existent branch
            result = self.atomgit.get_branch_info("non-existent")
            self.assertEqual(result, "")

            # Verify warning was printed for non-existent branch
            mock_print.assert_called()

    def test_get_spec_exception(self):
        """Test get_spec_exception method"""
        # Test package with exception
        result = self.atomgit.get_spec_exception("test_pkg")
        expected = {"dir": "dir1", "file": "file1.spec"}
        self.assertEqual(result, expected)

        # Test package without exception
        result = self.atomgit.get_spec_exception("unknown_pkg")
        self.assertEqual(result, "")

    def test_get_version_exception(self):
        """Test get_version_exception method"""
        result = self.atomgit.get_version_exception()
        expected = {"exceptions": ["pkg1", "pkg2"]}
        self.assertEqual(result, expected)

    def test_get_reviewer_checklist(self):
        """Test get_reviewer_checklist method"""
        result = self.atomgit.get_reviewer_checklist()
        expected = {"items": ["Check 1", "Check 2"]}
        self.assertEqual(result, expected)

    def test_create_issue_title_generation(self):
        """Test that create_issue generates correct title"""
        with patch.object(self.atomgit, 'post_issue') as mock_post_issue:
            self.atomgit.create_issue("test_pkg", "1.2.3", "master")

            # Check that post_issue was called with correct title
            mock_post_issue.assert_called_once()
            call_args = mock_post_issue.call_args[0]
            title = call_args[1]  # title is second argument

            expected_title = "Upgrade test_pkg to 1.2.3 in master"
            self.assertEqual(title, expected_title)


class TestAtomgitURLBuilding(unittest.TestCase):
    """Test URL building methods"""

    def setUp(self):
        """Set up a Atomgit instance"""
        self.mock_token_data = json.dumps({
            "access_token": "test_token",
            "user": "test_user"
        })

        # Patch the __init__ to skip actual network calls
        self.init_patcher = patch.object(Atomgit, '__init__', lambda self: None)
        self.init_patcher.start()

        self.atomgit = Atomgit()
        self.atomgit.token = json.loads(self.mock_token_data)
        self.atomgit.headers = {'User-Agent': 'test'}

    def tearDown(self):
        """Clean up patches"""
        self.init_patcher.stop()

    def test_fork_repo_url(self):
        """Test fork_repo URL building"""
        with patch.object(self.atomgit, '_Atomgit__post_atomgit') as mock_post:
            mock_post.return_value = '{"id": 123}'

            self.atomgit.fork_repo("test_repo", owner="src-openeuler")

            # Check URL was built correctly
            mock_post.assert_called_once()
            url = mock_post.call_args[0][0]
            self.assertIn("https://api.atomgit.com/api/v5/repos/src-openeuler/test_repo/forks", url)

    def test_create_pr_url_and_params(self):
        """Test create_pr URL and parameter building"""
        with patch.object(self.atomgit, 'get_reviewers') as mock_get_reviewers:
            with patch.object(self.atomgit, '_Atomgit__post_atomgit') as mock_post:
                # Mock reviewers response
                mock_get_reviewers.return_value = json.dumps([
                    {"login": "reviewer1"},
                    {"login": "reviewer2"}
                ])
                mock_post.return_value = '{"id": 456}'

                self.atomgit.create_pr("test_pkg", "1.2.3", "master", owner="src-openeuler")

                # Check URL
                url = mock_post.call_args[0][0]
                self.assertIn("https://api.atomgit.com/api/v5/repos/src-openeuler/test_pkg/pulls", url)

                # Check parameters
                values = mock_post.call_args[0][1]
                self.assertEqual(values["title"], "Upgrade test_pkg to 1.2.3")
                self.assertEqual(values["head"], "test_user:master")
                self.assertEqual(values["base"], "master")
                self.assertEqual(values["assignees"], "reviewer1,reviewer2")

    def test_get_pr_comments_all_pagination(self):
        """Test get_pr_comments_all pagination logic"""
        with patch.object(self.atomgit, '_Atomgit__get_json') as mock_get_json:
            # Mock 3 pages of comments
            mock_get_json.side_effect = [
                [{"id": 1}, {"id": 2}],  # Page 1
                [{"id": 3}, {"id": 4}],  # Page 2
                [],  # Page 3 - empty, should stop
            ]

            result = self.atomgit.get_pr_comments_all("src-openeuler", "test_repo", 123)

            # Should have 4 comments total
            self.assertEqual(len(result), 4)
            self.assertEqual([c["id"] for c in result], [1, 2, 3, 4])

            # Should have been called 3 times
            self.assertEqual(mock_get_json.call_count, 3)


if __name__ == "__main__":
    # Run tests when file is executed directly
    unittest.main()
