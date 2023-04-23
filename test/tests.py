#!/usr/bin/env python3
"""Unit test for convert.py"""
# -*- coding: utf-8 -*-

##
# Imports
##

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import pykeepass

import convert

##
# Globals
##

__MASTER_PASS__ = "123456"


##
# Functions
##


def validate_keepass(self):
    """Validate if the KeePass database has all the necessary entries"""

    # Load KeePass
    kpo = pykeepass.PyKeePass(self.output, password=__MASTER_PASS__)

    # Validate folder1 group
    folder1 = kpo.find_groups(name="folder1", first=True)
    self.assertIsNotNone(folder1)
    self.assertEqual(len(folder1.entries), 1)

    pass1 = kpo.find_entries(title="pass1", first=True, group=folder1)
    self.assertIsNotNone(pass1)

    self.assertEqual(pass1.username, "admin")
    self.assertEqual(pass1.password, "123456")
    self.assertEqual(pass1.url, "https://localhost")

    # Validate folder2 group
    folder2 = kpo.find_groups(name="folder2", first=True)
    self.assertIsNotNone(folder2)
    self.assertEqual(len(folder2.entries), 2)

    pass1 = kpo.find_entries(title="pass1", first=True, group=folder2)
    self.assertIsNotNone(pass1)

    self.assertEqual(pass1.username, "admin")
    self.assertEqual(pass1.password, "123457")
    self.assertEqual(pass1.url, "https://localhost2")

    pass2 = kpo.find_entries(title="pass2", first=True, group=folder2)
    self.assertIsNotNone(pass2)

    self.assertEqual(pass2.username, "admin2")
    self.assertEqual(pass2.password, "123458")
    self.assertEqual(pass2.url, "https://localhost3")


##
# Tests
##


class InteractiveTest(unittest.TestCase):
    """Test if convert.py can handle password submitted from stdin"""

    def setUp(self):
        del os.environ["BITWARDEN_PASS"]

        _, output = tempfile.mkstemp()
        self.output = output

    @patch("getpass.getpass", create=True)
    def test_convert(self, getpass_func):
        """Entrypoint for test case"""

        input_file = os.path.join(os.path.dirname(__file__), "resources", "test.json")
        getpass_func.return_value = __MASTER_PASS__

        convert.convert({"sync": False, "input": input_file, "output": self.output, "json": ""})

        validate_keepass(self)

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)


class NonInteractiveTest(unittest.TestCase):
    """Test if convert.py can handle password defined in the BITWARDEN_PASS environment variable"""

    def setUp(self):
        os.environ["BITWARDEN_PASS"] = __MASTER_PASS__

        _, output = tempfile.mkstemp()
        self.output = output

    def test_convert(self):
        """Entrypoint for test case"""

        input_file = os.path.join(os.path.dirname(__file__), "resources", "test.json")

        convert.convert({"sync": False, "input": input_file, "output": self.output, "json": ""})

        validate_keepass(self)

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)


class DuplicateTest(unittest.TestCase):
    """Test if convert.py can handle multiple entries with the same title and username"""

    def setUp(self):
        os.environ["BITWARDEN_PASS"] = __MASTER_PASS__

        _, output = tempfile.mkstemp()
        self.output = output

    def test_convert(self):
        """Entrypoint for test case"""

        input_file = os.path.join(os.path.dirname(__file__), "resources", "test_duplicate.json")

        convert.convert({"sync": False, "input": input_file, "output": self.output, "json": ""})

        # Load KeePass
        kpo = pykeepass.PyKeePass(self.output, password=__MASTER_PASS__)

        # Validate folder2 group
        folder2 = kpo.find_groups(name="folder2", first=True)
        self.assertIsNotNone(folder2)
        self.assertEqual(len(folder2.entries), 2)

        pass1 = kpo.find_entries(title="pass1", first=True, group=folder2)
        self.assertIsNotNone(pass1)

        pass1_ = kpo.find_entries(title="pass1 (1)", first=True, group=folder2)
        self.assertIsNotNone(pass1_)

        self.assertEqual(pass1_.username, "admin")
        self.assertEqual(pass1_.password, "123458")
        self.assertEqual(pass1_.url, "https://localhost3")

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)


class ExportTest(unittest.TestCase):
    """Test if convert.py can handle password submitted from stdin"""

    def setUp(self):
        os.environ["BITWARDEN_PASS"] = __MASTER_PASS__

        _, output = tempfile.mkstemp()
        self.output = output

    def test_convert(self):
        """Entrypoint for test case"""

        input_file = os.path.join(os.path.dirname(__file__), "resources", "test.json")
        _, json_output = tempfile.mkstemp()

        convert.convert({"sync": False, "input": input_file, "output": self.output, "json": json_output})

        self.assertTrue(os.path.exists(json_output))
        with open(os.path.expanduser(json_output), "r", encoding="utf-8") as f_handle:
            try:
                obj = json.loads(f_handle.read())

                self.assertFalse(obj["encrypted"])
                self.assertEqual(len(obj["folders"]), 2)
                self.assertEqual(len(obj["items"]), 4)
            except json.decoder.JSONDecodeError as err:
                self.fail(err)

        validate_keepass(self)

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)


##
# Main
##


if __name__ == "main":
    unittest.main()
