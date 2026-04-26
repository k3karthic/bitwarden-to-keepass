#!/usr/bin/env python3
"""Export BitWarden vault to a KeePass database"""

# -*- coding: utf-8 -*-

##
# Imports
##

import argparse
import base64
import getpass
import json
import os
import subprocess
import sys
import uuid
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

        self.env = os.environ.copy()
        if self.vault is None:
            self.env["BW_PASSWORD"] = self.password

    def unlock_and_get_session(self):
        """Unlock the vault and export the session key to the environment."""
        try:
            run_out = subprocess.run(
                ["bw", "unlock", "--passwordenv", "BW_PASSWORD", "--raw"],
                capture_output=True,
                check=True,
                text=True,
                env=self.env,
            )
            session_key = run_out.stdout.strip()
            if not session_key:
                print("Failed to get session key from Bitwarden CLI.", file=sys.stderr)
                sys.exit(1)
            self.env["BW_SESSION"] = session_key
            del self.env["BW_PASSWORD"]
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(
                f"Failed to unlock Bitwarden vault. Is 'bw' installed and in your PATH?",
                file=sys.stderr,
            )
            if hasattr(e, "stderr") and e.stderr:
                print(f"Error from bw: {e.stderr.strip()}", file=sys.stderr)
            sys.exit(1)

    def sync(self):
        """Sync BitWarden vault using cli"""

        subprocess.run(
            ["bw", "sync"],
            capture_output=True,
            check=False,
            text=True,
            env=self.env,
        )

    def fetch_bitwarden_folders(self):
        """List folders from bw cli or provided vault"""

        if self.vault is not None:
            self.folders = self.vault.get("folders", [])
            return self.folders

        run_out = subprocess.run(
            ["bw", "list", "folders"],
            capture_output=True,
            check=False,
            text=True,
            env=self.env,
        )

        try:
            self.folders = json.loads(run_out.stdout)
            return self.folders
        except json.decoder.JSONDecodeError as e:
            print(f"Failed to parse folders from Bitwarden: {e}", file=sys.stderr)
            print(f"Received: {run_out.stdout}", file=sys.stderr)
            sys.exit(-1)

    def fetch_bitwarden_items(self):
        """List items from bw cli or provided vault"""

        if self.vault is not None:
            self.items = self.vault["items"]
            return self.items

        run_out = subprocess.run(
            ["bw", "list", "items"],
            capture_output=True,
            check=False,
            text=True,
            env=self.env,
        )

        try:
            self.items = json.loads(run_out.stdout)
            return self.items
        except json.decoder.JSONDecodeError as e:
            print(f"Failed to parse items from Bitwarden: {e}", file=sys.stderr)
            print(f"Received: {run_out.stdout}", file=sys.stderr)
            sys.exit(-1)

    def export_json(self, output):
        """Export JSON vault"""

        with open(os.path.expanduser(output), "w", encoding="utf-8") as f_handle:
            f_handle.write(
                json.dumps(
                    {"encrypted": False, "folders": self.folders, "items": self.items}
                )
            )


class KeePassConvert:
    """Convert BitWarden items to KeePass entries"""

    PASSKEY_TAG = "Passkey"
    PASSKEY_CREDENTIAL_ID = "KPEX_PASSKEY_CREDENTIAL_ID"
    PASSKEY_PRIVATE_KEY_PEM = "KPEX_PASSKEY_PRIVATE_KEY_PEM"
    PASSKEY_RELYING_PARTY = "KPEX_PASSKEY_RELYING_PARTY"
    PASSKEY_USERNAME = "KPEX_PASSKEY_USERNAME"
    PASSKEY_USER_HANDLE = "KPEX_PASSKEY_USER_HANDLE"

    def __init__(self, output, password):
        self.kp_db = pykeepass.create_database(output, password=password)
        self.groups = None

    @staticmethod
    def __convert_login(item):
        title = item["name"]
        notes = item.get("notes", "") or ""
        url = None

        if len(item["login"].get("uris", []) or []) > 0:
            urls = [i["uri"] or "" for i in item["login"]["uris"]]
            url = urls[0]

            if len(urls) > 1:
                notes = "{}\n{}".format(notes, "\n".join(urls[1:]))

        username = item["login"].get("username", "") or ""
        password = item["login"].get("password", "") or ""
        totp = item["login"].get("totp", "") or ""

        return title, username, password, url, notes, totp

    @staticmethod
    def __convert_note(item):
        return (
            f"{item['name']} - Secure Note",
            "",
            "",
            "",
            item.get("notes", "") or "",
            "",
        )

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
            "",
        )

    @staticmethod
    def __convert_identity(item):
        notes = item.get("notes", "") or ""

        # Add identity info to the notes
        notes = notes + (
            "\n".join([f"{i}: {j}" for i, j in item.get("identity", "").items()])
        )

        return f"{item['name']} - Identity", "", "", "", notes, ""

    @staticmethod
    def __convert_ssh_key(item):
        notes = item.get("notes", "") or ""
        ssh_key_info = item.get("sshKey", {})
        public_key = ssh_key_info.get("publicKey", "") or ""
        fingerprint = ssh_key_info.get("keyFingerprint", "") or ""

        note_parts = []
        if notes:
            note_parts.append(notes)
        if fingerprint:
            note_parts.append(f"Fingerprint: {fingerprint}")
        if public_key:
            note_parts.append(f"Public Key: {public_key}")

        notes = "\n".join(note_parts)

        return (
            f"{item['name']} - SSH Key",
            "",  # username
            ssh_key_info.get("privateKey", "") or "",  # password
            "",  # url
            notes,
            "",  # totp
        )

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

        if item_type == 5:
            return cls.__convert_ssh_key(item)

        raise Exception(f"Unknown item type: {item_type}")

    @classmethod
    def __get_passkeys(cls, item):
        """Return Bitwarden FIDO2 credentials for a login item."""

        if item.get("type") != 1:
            return []

        return item.get("login", {}).get("fido2Credentials") or []

    @staticmethod
    def __base64url_decode(value):
        """Decode Bitwarden's unpadded base64url strings."""

        if value is None:
            return b""

        value = str(value).replace("-", "+").replace("_", "/")
        value += "=" * (-len(value) % 4)
        return base64.b64decode(value)

    @classmethod
    def __bitwarden_key_to_pem(cls, key_value):
        """Convert a Bitwarden PKCS#8 base64url private key to PEM (KeePassXC format)."""

        der = cls.__base64url_decode(key_value)
        pem_body = base64.b64encode(der).decode("ascii")
        return f"-----BEGIN PRIVATE KEY-----{pem_body}-----END PRIVATE KEY-----"

    @classmethod
    def __bitwarden_credential_id_to_kp(cls, credential_id):
        """Convert Bitwarden credentialId to KeePassXC format.

        Bitwarden exports credentialId as a UUID string (e.g.
        'a3e15f8b-27c1-42ae-90cf-a615ad87854f'). KeePassXC expects the raw
        bytes encoded as base64url without padding.
        """
        if not credential_id:
            return ""

        # Bitwarden exports credentialId as a UUID string
        if len(credential_id) == 36 and credential_id.count("-") == 4:
            try:
                raw_bytes = uuid.UUID(credential_id).bytes
                return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("ascii")
            except ValueError:
                pass

        # Fallback: already base64url-encoded raw bytes
        uuid_bytes = cls.__base64url_decode(credential_id)
        if len(uuid_bytes) == 16:
            return base64.urlsafe_b64encode(uuid_bytes).rstrip(b"=").decode("ascii")
        return credential_id

    @classmethod
    def __apply_passkey(cls, entry, passkey):
        """Store a Bitwarden passkey using KeePassXC-compatible attributes."""

        if not passkey:
            return

        key_value = passkey.get("keyValue")
        credential_id = passkey.get("credentialId")
        rp_id = passkey.get("rpId")

        if not key_value or not credential_id or not rp_id:
            return

        username = (
            passkey.get("userName")
            or passkey.get("userDisplayName")
            or entry.username
            or ""
        )
        user_handle = passkey.get("userHandle") or ""

        entry.set_custom_property(cls.PASSKEY_USERNAME, username)
        entry.set_custom_property(
            cls.PASSKEY_CREDENTIAL_ID,
            cls.__bitwarden_credential_id_to_kp(credential_id),
            protect=True,
        )
        entry.set_custom_property(
            cls.PASSKEY_PRIVATE_KEY_PEM,
            cls.__bitwarden_key_to_pem(key_value),
            protect=True,
        )
        entry.set_custom_property(cls.PASSKEY_RELYING_PARTY, rp_id)
        entry.set_custom_property(cls.PASSKEY_USER_HANDLE, user_handle, protect=True)

        tags = list(entry.tags or [])
        if cls.PASSKEY_TAG not in tags:
            tags.append(cls.PASSKEY_TAG)
            entry.tags = tags

    def __add_entry(
        self,
        dest_group,
        title,
        username,
        password,
        url,
        notes,
        otp_value,
        passkey=None,
    ):
        """Add a KeePass entry and attach passkey metadata when present."""

        entry = self.kp_db.add_entry(
            dest_group,
            title,
            username,
            password,
            url=url,
            notes=notes,
            otp=otp_value,
        )
        self.__apply_passkey(entry, passkey)
        return entry

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
            if (
                "folderId" in item
                and item["folderId"] in self.groups
                and self.groups[item["folderId"]] is not None
            ):
                group_id = item["folderId"]
                dest_group = self.groups[group_id]

            title, username, password, url, notes, totp = self.__item_to_entry(item)

            # The combination of group_id, title & username must be unique
            seen_key = "".join(
                (group_id or "", title, username if username is not None else "")
            )
            seen_entries[seen_key] += 1

            # Add a suffix in the following format for duplicate entries
            #   <title> (<count>) e.g., pass1 (2)
            if seen_entries[seen_key] > 1:
                title = "".join((title, " (", str(seen_entries[seen_key] - 1), ")"))

            otp_value = None
            if len(totp) > 0:
                if totp.startswith("otpauth://"):
                    otp_value = totp
                else:
                    otp_value = f"otpauth://totp/{title}:{username}?secret={totp}"

            passkeys = self.__get_passkeys(item)
            self.__add_entry(
                dest_group,
                title,
                username,
                password,
                url,
                notes,
                otp_value,
                passkeys[0] if passkeys else None,
            )

            for passkey in passkeys[1:]:
                seen_entries[seen_key] += 1
                passkey_title = "".join(
                    (title, " (", str(seen_entries[seen_key] - 1), ")")
                )
                self.__add_entry(
                    dest_group,
                    passkey_title,
                    username,
                    password,
                    url,
                    notes,
                    otp_value,
                    passkey,
                )

    def apply_patch(self, patch_path, patch_password):
        """
        Apply entries from a patch kdbx into the current database.

        An entry from the patch is added only if no entry with the same
        (group name, title, username) already exists in the destination db.
        Groups present in the patch but missing in the destination are created.

        Returns a tuple (added, skipped) with counts.
        """
        print(f"Applying patch from: {patch_path}")

        try:
            patch_db = pykeepass.PyKeePass(patch_path, password=patch_password)
        except Exception as e:
            print(f"Failed to open patch file: {e}", file=sys.stderr)
            sys.exit(1)

        # Build a set of (group_name, title, username) that already exist
        existing = set()
        for entry in self.kp_db.entries:
            group_name = entry.group.name if entry.group else ""
            existing.add((group_name, entry.title or "", entry.username or ""))

        added = 0
        skipped = 0

        for entry in patch_db.entries:
            patch_group_name = entry.group.name if entry.group else ""
            key = (patch_group_name, entry.title or "", entry.username or "")

            if key in existing:
                print(
                    f"  SKIP (already exists): [{patch_group_name}] {entry.title} / {entry.username}"
                )
                skipped += 1
                continue

            dest_group = self._get_or_create_group(patch_group_name)

            added_entry = self.kp_db.add_entry(
                dest_group,
                entry.title or "",
                entry.username or "",
                entry.password or "",
                url=entry.url,
                notes=entry.notes,
                otp=entry.otp if entry.otp else None,
                tags=list(entry.tags or []),
            )

            for prop_key, prop_value in entry.custom_properties.items():
                added_entry.set_custom_property(
                    prop_key,
                    prop_value,
                    protect=entry.is_custom_property_protected(prop_key),
                )

            print(f"  ADD: [{patch_group_name}] {entry.title} / {entry.username}")
            existing.add(key)
            added += 1

        print(f"Patch applied: {added} added, {skipped} skipped.")
        return added, skipped

    def _get_or_create_group(self, group_name):
        """Return the root group if group_name is empty/root, otherwise find or create a top-level group."""
        if not group_name or group_name == self.kp_db.root_group.name:
            return self.kp_db.root_group

        existing = self.kp_db.find_groups(name=group_name, first=True)
        if existing:
            return existing

        return self.kp_db.add_group(self.kp_db.root_group, group_name)

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

    if filename == "-":
        input_str = sys.stdin.read()
    else:
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

    if params.get("input") == "-" and params.get("sync"):
        print("Cannot use --sync with stdin input.", file=sys.stderr)
        sys.exit(1)

    if "BITWARDEN_PASS" in os.environ:
        password = os.environ["BITWARDEN_PASS"]
    else:
        password = getpass.getpass("Master Password: ")

    print("")

    kp_db = KeePassConvert(params["output"], password)
    bw_vault = BitWarden(parse_input_json(params["input"]) or None, password)

    if params.get("input") is None:
        print("Unlocking vault...")
        bw_vault.unlock_and_get_session()

    if params["sync"] is True:
        print("Syncing vault...")
        bw_vault.sync()

    print("Fetching folders...")
    kp_db.folders_to_groups(bw_vault.fetch_bitwarden_folders())

    print("Fetching items...")
    kp_db.items_to_entries(bw_vault.fetch_bitwarden_items())

    print("")

    # --- Patch step ---
    patch_path = params.get("patch")
    if patch_path:
        patch_path = os.path.expanduser(patch_path)
        if not os.path.exists(patch_path):
            print(f"Patch file not found: {patch_path}", file=sys.stderr)
            sys.exit(1)

        patch_password_env = params.get("patch_password_env") or "PATCH_PASS"
        if patch_password_env in os.environ:
            patch_password = os.environ[patch_password_env]
        else:
            patch_password = getpass.getpass(
                f"Password for patch file ({os.path.basename(patch_path)}): "
            )

        print("")
        kp_db.apply_patch(patch_path, patch_password)
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
        "-i",
        "--input",
        required=False,
        help="BitWarden unencrypted JSON file. Use '-' for stdin.",
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
        default="",
        help="Export BitWarden vault as a JSON file",
    )

    parser.add_argument(
        "-s",
        "--sync",
        required=False,
        default=False,
        action="store_true",
        help="Sync BitWarden vault using cli",
    )

    parser.add_argument(
        "-p",
        "--patch",
        required=False,
        type=str,
        default=None,
        help=(
            "Path to a KeePass (.kdbx) patch file whose entries will be merged "
            "into the output. Entries that already exist (same group + title + username) "
            "are skipped. Password is read from the env var PATCH_PASS or prompted interactively."
        ),
    )

    parser.add_argument(
        "--patch-password-env",
        required=False,
        type=str,
        default="PATCH_PASS",
        dest="patch_password_env",
        help="Environment variable holding the patch kdbx password (default: PATCH_PASS)",
    )

    args = parser.parse_args()

    if args.replace is False and os.path.exists(os.path.expanduser(args.output)):
        res = input(f"Output file {args.output} exists. Replace? (n/Y)")
        if res not in ["Y", "y"]:
            sys.exit()

    convert(vars(args))


if __name__ == "__main__":
    main()
