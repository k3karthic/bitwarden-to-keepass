"""Test convert.py

"""
import os
import tempfile
import unittest
from unittest.mock import patch

import pykeepass

import convert

__MASTER_PASS__ = '123456'

def validate_keepass(self):
    # Load KeePass
    kpo = pykeepass.PyKeePass(self.output, password=__MASTER_PASS__)

    # Validate folder1 group
    folder1 = kpo.find_groups(name='folder1', first=True)
    self.assertIsNotNone(folder1)
    self.assertEqual(len(folder1.entries), 1)

    pass1 = kpo.find_entries(title='pass1', first=True, group=folder1)
    self.assertIsNotNone(pass1)

    self.assertEqual(pass1.username, 'admin')
    self.assertEqual(pass1.password, '123456')
    self.assertEqual(pass1.url, 'https://localhost')

    # Validate folder2 group
    folder2 = kpo.find_groups(name='folder2', first=True)
    self.assertIsNotNone(folder2)
    self.assertEqual(len(folder2.entries), 2)

    pass1 = kpo.find_entries(title='pass1', first=True, group=folder2)
    self.assertIsNotNone(pass1)

    self.assertEqual(pass1.username, 'admin')
    self.assertEqual(pass1.password, '123457')
    self.assertEqual(pass1.url, 'https://localhost2')

    pass2 = kpo.find_entries(title='pass2', first=True, group=folder2)
    self.assertIsNotNone(pass2)

    self.assertEqual(pass2.username, 'admin2')
    self.assertEqual(pass2.password, '123458')
    self.assertEqual(pass2.url, 'https://localhost3')

class InteractiveTest(unittest.TestCase):
    def setUp(self):
        del os.environ['BITWARDEN_PASS']

        _, output = tempfile.mkstemp()
        self.output = output

    @patch("getpass.getpass", create=True)
    def test_convert(self, getpass_func):
        input_file = os.path.join('test', 'test.json')
        getpass_func.return_value = __MASTER_PASS__

        convert.convert(input_file, self.output)

        validate_keepass(self)

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)

class NonInteractiveTest(unittest.TestCase):
    def setUp(self):
        os.environ['BITWARDEN_PASS'] = __MASTER_PASS__

        _, output = tempfile.mkstemp()
        self.output = output

    def test_convert(self):
        input_file = os.path.join('test', 'test.json')

        convert.convert(input_file, self.output)

        validate_keepass(self)

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)

class DuplicateTest(unittest.TestCase):
    def setUp(self):
        os.environ['BITWARDEN_PASS'] = __MASTER_PASS__

        _, output = tempfile.mkstemp()
        self.output = output

    def test_convert(self):
        input_file = os.path.join('test', 'test_duplicate.json')

        convert.convert(input_file, self.output)

        # Load KeePass
        kpo = pykeepass.PyKeePass(self.output, password=__MASTER_PASS__)

        # Validate folder2 group
        folder2 = kpo.find_groups(name='folder2', first=True)
        self.assertIsNotNone(folder2)
        self.assertEqual(len(folder2.entries), 2)

        pass1 = kpo.find_entries(title='pass1', first=True, group=folder2)
        self.assertIsNotNone(pass1)

        pass1_ = kpo.find_entries(title='pass1 (1)', first=True, group=folder2)
        self.assertIsNotNone(pass1_)

        self.assertEqual(pass1_.username, 'admin')
        self.assertEqual(pass1_.password, '123458')
        self.assertEqual(pass1_.url, 'https://localhost3')

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)


if __name__ == '__main__':
    unittest.main()
