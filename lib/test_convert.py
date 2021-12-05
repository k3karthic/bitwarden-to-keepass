import os
import pykeepass
import tempfile

import unittest
from unittest.mock import patch

import lib

__MASTER_PASS__ = '123456'

def validate_keepass(self):
    ## Load KeePass
    kp = pykeepass.PyKeePass(self.output, password=__MASTER_PASS__)

    ## Validate folder1 group
    folder1 = kp.find_groups(name='folder1', first=True)
    self.assertIsNotNone(folder1)
    self.assertEqual(len(folder1.entries), 1)

    pass1 = kp.find_entries(title='pass1', first=True, group=folder1)
    self.assertIsNotNone(pass1)

    self.assertEqual(pass1.username, 'admin')
    self.assertEqual(pass1.password, '123456')
    self.assertEqual(pass1.url, 'https://localhost')

    ## Validate folder2 group
    folder2 = kp.find_groups(name='folder2', first=True)
    self.assertIsNotNone(folder2)
    self.assertEqual(len(folder2.entries), 2)

    pass1 = kp.find_entries(title='pass1', first=True, group=folder2)
    self.assertIsNotNone(pass1)

    self.assertEqual(pass1.username, 'admin')
    self.assertEqual(pass1.password, '123457')
    self.assertEqual(pass1.url, 'https://localhost2')

    pass2 = kp.find_entries(title='pass2', first=True, group=folder2)
    self.assertIsNotNone(pass2)

    self.assertEqual(pass2.username, 'admin2')
    self.assertEqual(pass2.password, '123458')
    self.assertEqual(pass2.url, 'https://localhost3')

class InteractiveTest(unittest.TestCase):
    def setUp(self):
        del os.environ['BITWARDEN_PASS']

        (h, output) = tempfile.mkstemp()
        self.h = h
        self.output = output

    @patch("getpass.getpass", create=True)
    def test_convert(self, getpass_func):
        input_file = os.path.join(os.path.dirname(__file__), '..', 'resources', 'test.json')
        getpass_func.return_value = __MASTER_PASS__

        lib.convert(input_file, self.output)

        validate_keepass(self)

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)

class NonInteractiveTest(unittest.TestCase):
    def setUp(self):
        os.environ['BITWARDEN_PASS'] = __MASTER_PASS__

        (h, output) = tempfile.mkstemp()
        self.h = h
        self.output = output

    def test_convert(self):
        input_file = os.path.join(os.path.dirname(__file__), '..', 'resources', 'test.json')

        lib.convert(input_file, self.output)

        validate_keepass(self)

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)

class DuplicateTest(unittest.TestCase):
    def setUp(self):
        os.environ['BITWARDEN_PASS'] = __MASTER_PASS__

        (h, output) = tempfile.mkstemp()
        self.h = h
        self.output = output

    def test_convert(self):
        input_file = os.path.join(os.path.dirname(__file__), '..', 'resources', 'test_duplicate.json')

        self.assertRaisesRegex(Exception, "already exists", lib.convert, input_file, self.output)

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)

if __name__ == 'main':
    unittest.main()
