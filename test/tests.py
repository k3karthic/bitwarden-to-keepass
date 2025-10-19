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

from bitwarden_to_keepass import convert

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

    return kpo


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


class StdinTest(unittest.TestCase):
    """Test if convert.py can handle json from stdin"""

    def setUp(self):
        os.environ["BITWARDEN_PASS"] = __MASTER_PASS__

        _, output = tempfile.mkstemp()
        self.output = output

    @patch("sys.stdin", create=True)
    def test_convert(self, stdin_mock):
        """Entrypoint for test case"""

        input_file = os.path.join(os.path.dirname(__file__), "resources", "test.json")
        with open(input_file, "r", encoding="utf-8") as f_handle:
            stdin_mock.read.return_value = f_handle.read()

        convert.convert({"sync": False, "input": "-", "output": self.output, "json": ""})

        validate_keepass(self)

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)


class StdinSyncFailTest(unittest.TestCase):
    """Test that using --sync with stdin input fails"""

    def setUp(self):
        os.environ["BITWARDEN_PASS"] = __MASTER_PASS__
        _, self.output = tempfile.mkstemp()

    def test_convert_fails(self):
        """Test that convert() exits when --sync and --input - are used"""
        params = {"sync": True, "input": "-", "output": self.output, "json": ""}
        with self.assertRaises(SystemExit) as cm:
            convert.convert(params)
        self.assertEqual(cm.exception.code, 1)

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
                self.assertEqual(len(obj["items"]), 5)
            except json.decoder.JSONDecodeError as err:
                self.fail(err)

        kpo = validate_keepass(self)

        # Validate totp
        totp = kpo.find_entries(title="totp test", first=True)
        self.assertIsNotNone(totp)

        self.assertEqual(totp.username, "username@example.com")
        self.assertEqual(totp.password, "testpasword!")
        self.assertEqual(totp.url, "https://account.proton.me/login")
        self.assertEqual(totp.otp, "otpauth://totp/totp test:username@example.com?secret=XY7MXDNK5ZEKJT4Y")

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)


class NoFolderTest(unittest.TestCase):
    """Test if convert.py can handle vault with no folders"""

    def setUp(self):
        os.environ["BITWARDEN_PASS"] = __MASTER_PASS__

        _, output = tempfile.mkstemp()
        self.output = output

    def test_convert(self):
        """Entrypoint for test case"""

        input_file = os.path.join(os.path.dirname(__file__), "resources", "test_no_folders.json")

        convert.convert({"sync": False, "input": input_file, "output": self.output, "json": ""})

        # Load KeePass
        kpo = pykeepass.PyKeePass(self.output, password=__MASTER_PASS__)

        pass1 = kpo.find_entries(title="totp test", first=True)
        self.assertIsNotNone(pass1)

        self.assertEqual(pass1.username, "username@example.com")
        self.assertEqual(pass1.password, "testpasword!")
        self.assertEqual(pass1.url, "https://account.proton.me/login")

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)


class TestSSHKeyConversion(unittest.TestCase):
    """Test conversion of Bitwarden SSH key items"""

    def test_full_ssh_key(self):
        """Tests conversion of a standard SSH key item."""
        item = {
            "name": "test_ssh",
            "type": 5,
            "notes": "Initial notes.",
            "sshKey": {
                "privateKey": "PRIVATE_KEY_DATA",
                "publicKey": "PUBLIC_KEY_DATA",
                "keyFingerprint": "FINGERPRINT_DATA",
            },
        }
        title, username, password, url, notes, totp = convert.KeePassConvert._KeePassConvert__item_to_entry(item)
        self.assertEqual(title, "test_ssh - SSH Key")
        self.assertEqual(username, "")
        self.assertEqual(password, "PRIVATE_KEY_DATA")
        self.assertEqual(url, "")
        expected_notes = "Initial notes.\nFingerprint: FINGERPRINT_DATA\nPublic Key: PUBLIC_KEY_DATA"
        self.assertEqual(notes, expected_notes)
        self.assertEqual(totp, "")

    def test_ssh_key_no_notes(self):
        """Tests conversion of an SSH key item with no initial notes."""
        item = {
            "name": "test_ssh_no_notes",
            "type": 5,
            "notes": None,
            "sshKey": {
                "privateKey": "PRIVATE_KEY_DATA",
                "publicKey": "PUBLIC_KEY_DATA",
                "keyFingerprint": "FINGERPRINT_DATA",
            },
        }
        title, username, password, url, notes, totp = convert.KeePassConvert._KeePassConvert__item_to_entry(item)
        self.assertEqual(title, "test_ssh_no_notes - SSH Key")
        self.assertEqual(password, "PRIVATE_KEY_DATA")
        expected_notes = "Fingerprint: FINGERPRINT_DATA\nPublic Key: PUBLIC_KEY_DATA"
        self.assertEqual(notes, expected_notes)

    def test_ssh_key_missing_public_key(self):
        """Tests conversion of an SSH key item missing a public key."""
        item = {
            "name": "test_ssh_no_public",
            "type": 5,
            "notes": "Some notes.",
            "sshKey": {"privateKey": "PRIVATE_KEY_DATA", "keyFingerprint": "FINGERPRINT_DATA"},
        }
        title, username, password, url, notes, totp = convert.KeePassConvert._KeePassConvert__item_to_entry(item)
        self.assertEqual(title, "test_ssh_no_public - SSH Key")
        self.assertEqual(password, "PRIVATE_KEY_DATA")
        expected_notes = "Some notes.\nFingerprint: FINGERPRINT_DATA"
        self.assertEqual(notes, expected_notes)

    def test_ssh_key_missing_fingerprint(self):
        """Tests conversion of an SSH key item missing a fingerprint."""
        item = {
            "name": "test_ssh_no_fingerprint",
            "type": 5,
            "notes": "Some notes.",
            "sshKey": {"privateKey": "PRIVATE_KEY_DATA", "publicKey": "PUBLIC_KEY_DATA"},
        }
        title, username, password, url, notes, totp = convert.KeePassConvert._KeePassConvert__item_to_entry(item)
        self.assertEqual(title, "test_ssh_no_fingerprint - SSH Key")
        self.assertEqual(password, "PRIVATE_KEY_DATA")
        expected_notes = "Some notes.\nPublic Key: PUBLIC_KEY_DATA"
        self.assertEqual(notes, expected_notes)

    def test_ssh_key_missing_private_key(self):
        """Tests conversion of an SSH key item missing a private key."""
        item = {
            "name": "test_ssh_no_private",
            "type": 5,
            "notes": "Some notes.",
            "sshKey": {"publicKey": "PUBLIC_KEY_DATA", "keyFingerprint": "FINGERPRINT_DATA"},
        }
        title, username, password, url, notes, totp = convert.KeePassConvert._KeePassConvert__item_to_entry(item)
        self.assertEqual(title, "test_ssh_no_private - SSH Key")
        self.assertEqual(password, "")
        expected_notes = "Some notes.\nFingerprint: FINGERPRINT_DATA\nPublic Key: PUBLIC_KEY_DATA"
        self.assertEqual(notes, expected_notes)

    def test_ssh_key_empty_sshkey_object(self):
        """Tests conversion of an SSH key item with an empty sshKey object."""
        item = {"name": "test_ssh_empty", "type": 5, "notes": "Some notes.", "sshKey": {}}
        title, username, password, url, notes, totp = convert.KeePassConvert._KeePassConvert__item_to_entry(item)
        self.assertEqual(title, "test_ssh_empty - SSH Key")
        self.assertEqual(password, "")
        self.assertEqual(notes, "Some notes.")


##
# Main
##


if __name__ == "main":
    unittest.main()
