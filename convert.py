#!/usr/bin/env python3
"""Export BitWarden vault to a KeePass database"""
# -*- coding: utf-8 -*-

##
# Imports
##

import argparse
import getpass
import json
import os
import subprocess
import sys
from collections import Counter

import pykeepass

##
# Classes
##


class BitWarden:
    """Interact with the BitWarden CLI or JSON vault"""

    def __init__(self, vault, password):
        self.vault = vault
        self.password = password

        self.folders = None
        self.items = None

    def sync(self):
        """Sync BitWarden vault using cli"""

        subprocess.run(
            ["bw", "sync"],
            input=self.password.encode("utf-8"),
            capture_output=True,
            check=False,
        )

    def fetch_bitwarden_folders(self):
        """List folders from bw cli or provided vault"""

        if self.vault is not None:
            self.folders = self.vault["folders"]
            return self.folders

        run_out = subprocess.run(
            ["bw", "list", "folders"],
            input=self.password.encode("utf-8"),
            capture_output=True,
            check=False,
        )

        try:
            self.folders = json.loads(run_out.stdout)
            return self.folders
        except json.decoder.JSONDecodeError:
            sys.exit(-1)

    def fetch_bitwarden_items(self):
        """List items from bw cli or provided vault"""

        if self.vault is not None:
            self.items = self.vault["items"]
            return self.items

        run_out = subprocess.run(
            ["bw", "list", "items"],
            input=self.password.encode("utf-8"),
            capture_output=True,
            check=False,
        )

        try:
            self.items = json.loads(run_out.stdout)
            return self.items
        except json.decoder.JSONDecodeError:
            sys.exit(-1)

    def export_json(self, output):
        """Export JSON vault"""

        with open(os.path.expanduser(output), "w", encoding="utf-8") as f_handle:
            f_handle.write(json.dumps({
                "encrypted": False,
                "folders": self.folders,
                "items": self.items
            }))


class KeePassConvert:
    """Convert BitWarden items to KeePass entries"""

    def __init__(self, output, password):
        self.kp_db = pykeepass.create_database(output, password=password)
        self.groups = None

    @staticmethod
    def __convert_login(item):
        title = item["name"]
        notes = item.get("notes", "") or ""
        url = None

        if len(item["login"].get("uris", [])) > 0:
            urls = [i["uri"] or "" for i in item["login"]["uris"]]
            url = urls[0]

            if len(urls) > 1:
                notes = "{}\n{}".format(notes, "\n".join(urls[1:]))

        username = item["login"].get("username", "") or ""
        password = item["login"].get("password", "") or ""

        return title, username, password, url, notes

    @staticmethod
    def __convert_note(item):
        return f"{item['name']} - Secure Note", "", "", "", item.get("notes", "") or ""

    @staticmethod
    def __convert_card(item):
        notes = item.get("notes", "") or ""

        # Add card info to the notes
        notes = notes + (
            "\n".join([f"{i}: {j}" for i, j in item.get("card", "").items()])
        )

        return (
            f"{item['name']} - Card",
            item.get("card", {}).get("brand", "") or "",
            item.get("card", {}).get("number", "") or "",
            "",
            notes,
        )

    @staticmethod
    def __convert_identity(item):
        notes = item.get("notes", "") or ""

        # Add identity info to the notes
        notes = notes + (
            "\n".join([f"{i}: {j}" for i, j in item.get("identity", "").items()])
        )

        return f"{item['name']} - Identity", "", "", "", notes

    @classmethod
    def __item_to_entry(cls, item):
        """Call the appropriate helper function based on the item type"""

        item_type = item["type"]

        if item_type == 1:
            return cls.__convert_login(item)

        if item_type == 2:
            return cls.__convert_note(item)

        if item_type == 3:
            return cls.__convert_card(item)

        if item_type == 4:
            return cls.__convert_identity(item)

        raise Exception(f"Unknown item type: {item_type}")

    def folders_to_groups(self, folders_list):
        """Create KeePass folder structure based on BitWarden folders"""

        groups_dict = {}

        for folder in folders_list:
            names = folder["name"].split("/")

            group = None
            parent = self.kp_db.root_group
            for name in names:
                if name == "No Folder":
                    group = self.kp_db.root_group
                    break

                if name not in groups_dict:
                    group = self.kp_db.add_group(parent, name)
                    groups_dict[name] = group

                parent = groups_dict[name]

            groups_dict[folder["id"]] = group

        self.groups = groups_dict

    def items_to_entries(self, items_list):
        """Convert BitWarden item to KeePass entry"""

        if self.groups is None:
            raise Exception("Run folders_to_groups before running items_to_entries")

        seen_entries = Counter({})

        for item in items_list:
            group_id = "root"
            dest_group = self.kp_db.root_group
            if item["folderId"] in self.groups:
                group_id = item["folderId"]
                dest_group = self.groups[group_id]

            title, username, password, url, notes = self.__item_to_entry(item)

            # The combination of group_id, title & username must be unique
            seen_key = "".join(
                (group_id or "", title, username if username is not None else "")
            )
            seen_entries[seen_key] += 1

            # Add a suffix in the following format for duplicate entries
            #   <title> (<count>) e.g., pass1 (2)
            if seen_entries[seen_key] > 1:
                title = "".join((title, " (", str(seen_entries[seen_key] - 1), ")"))

            self.kp_db.add_entry(
                dest_group, title, username, password, url=url, notes=notes
            )

    def save(self):
        """Save the KeePass database"""

        self.kp_db.save()


##
# Functions
##


def parse_input_json(filename):
    """Parse input json file if provided"""

    if not filename:
        return None

    with open(os.path.expanduser(filename), "r", encoding="utf-8") as fname:
        input_str = fname.read()

        try:
            vault = json.loads(input_str)
            if vault["encrypted"] is True:
                print("Unsupported: exported json file is encrypted")
                sys.exit(-1)
        except json.decoder.JSONDecodeError as err:
            print(err)
            sys.exit(-1)

        return vault


def convert(params):
    """Main entrypoint for the script"""

    if "BITWARDEN_PASS" in os.environ:
        password = os.environ["BITWARDEN_PASS"]
    else:
        password = getpass.getpass("Master Password: ")

    print("")

    kp_db = KeePassConvert(params["output"], password)
    bw_vault = BitWarden(parse_input_json(params["input"]) or None, password)

    if params["sync"] is True:
        print("Syncing vault...")
        bw_vault.sync()

    print("Fetching folders...")
    kp_db.folders_to_groups(bw_vault.fetch_bitwarden_folders())

    print("Fetching items...")
    kp_db.items_to_entries(bw_vault.fetch_bitwarden_items())

    print("")

    kp_db.save()

    if len(params["json"]) > 0:
        bw_vault.export_json(params["json"])


##
# Main
##

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i", "--input", required=False, help="BitWarden unencrypted JSON file"
    )

    parser.add_argument("-o", "--output", required=True, help="Output kdbx file path")

    parser.add_argument(
        "-r",
        "--replace",
        required=False,
        type=bool,
        default=False,
        help="Ignore replace file warning",
    )

    parser.add_argument(
        "-j",
        "--json",
        required=False,
        type=str,
        default='',
        help="Export BitWarden vault as a JSON file",
    )

    parser.add_argument(
        "-s",
        "--sync",
        required=False,
        type=bool,
        default=False,
        help="Sync BitWarden vault using cli",
    )

    args = parser.parse_args()

    if args.replace is False and os.path.exists(os.path.expanduser(args.output)):
        res = input(f"Output file {args.output} exists. Replace? (n/Y)")
        if res not in ["Y", "y"]:
            sys.exit()

    convert(vars(args))

if __name__ == "__main__":
    main()