#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# Imports
##

# import pdb

import codecs
import getpass
import os
import subprocess
import sys
import json
import pykeepass

from collections import Counter

##
# Functions
##


def fetch_bitwarden_folders(vault, password):
    print("Fetching folders...")

    if vault is not None:
        return vault['folders']
    else:
        r = subprocess.run(
            ["bw", "list", "folders"],
            input=password.encode('utf-8'),
            stderr=sys.stderr,
            stdout=subprocess.PIPE
        )

        try:
            folders = json.loads(r.stdout)
            return folders
        except json.decoder.JSONDecodeError:
            sys.exit(-1)


def fetch_bitwarden_items(vault, password):
    print("Fetching items...")

    if vault is not None:
        return vault['items']
    else:
        r = subprocess.run(
            ["bw", "list", "items"],
            input=password.encode('utf-8'),
            stderr=sys.stderr,
            stdout=subprocess.PIPE
        )

        try:
            items = json.loads(r.stdout)
            return items
        except json.decoder.JSONDecodeError:
            sys.exit(-1)


def create_keepass_groups(kp, folders_list):
    groups_dict = {}

    for x in folders_list:
        name = x['name'].split('/')

        group = None
        parent = kp.root_group
        for n in name:
            if n == 'No Folder':
                group = kp.root_group
                break

            if n not in groups_dict:
                group = kp.add_group(parent, n)
                groups_dict[n] = group

            parent = groups_dict[n]

        groups_dict[x['id']] = group

    return groups_dict


def _login(item):
    """Handle login entries

        Returns: title, username, password, url, notes (include any extra URLs)

    """
    title = item['name']
    notes = item.get('notes', '') or ''
    url = None

    if len(item['login'].get('uris', [])) > 0:
        urls = [i['uri'] or '' for i in item['login']['uris']]
        url = urls[0]
        if len(urls) > 1:
            notes = "{}\n{}".format(notes, "\n".join(urls[1:]))

    username = item['login'].get('username', '') or ''
    password = item['login'].get('password', '') or ''

    return title, username, password, url, notes


def _card(item):
    """Handle card entries

        Returns: title (append " - Card" to the name,
                 username (Card brand),
                 password (card number),
                 url (none),
                 notes (including all card info)

    """
    notes = item.get('notes', "") or ""
    # Add card info to the notes
    notes = notes + ("\n".join([f"{i}: {j}" for i, j in item.get('card', "").items()]))
    return f"{item['name']} - Card", \
           item.get('card', {}).get('brand', '') or "", \
           item.get('card', {}).get('number', "") or "", \
           "", \
           notes


def _identity(item):
    """Handle identity entries

        Returns: title, username, password, url, notes

    """
    notes = item.get('notes', "") or ""
    # Add identity info to the notes
    notes = notes + ("\n".join([f"{i}: {j}" for i, j in item.get('identity', "").items()]))
    return f"{item['name']} - Identity", "", "", "", notes


def _note(item):
    """Handle secure note entries

        Returns: title, username, password, url, notes

    """
    return f"{item['name']} - Secure Note", "", "", "", item.get('notes', '') or ""


def _input_file(filename):
    """Open input file if given

        Args: filename - string
        Returns: vault - dict

    """
    if not filename:
        return None
    with codecs.open(filename, 'r', 'utf-8') as fname:
        input_str = fname.read()

    try:
        vault = json.loads(input_str)
        if vault['encrypted'] is True:
            print("Unsupported: exported json file is encrypted")
            sys.exit(-1)
    except json.decoder.JSONDecodeError as err:
        print(err)
        sys.exit(-1)
    return vault


def convert(input_file, output):
    if 'BITWARDEN_PASS' in os.environ:
        password = os.environ['BITWARDEN_PASS']
    else:
        password = getpass.getpass('Master Password: ')
    print('')

    kpo = pykeepass.create_database(output, password=password)

    vault = _input_file(input_file) or None
    folders_list = fetch_bitwarden_folders(vault, password)
    groups = create_keepass_groups(kpo, folders_list)

    items_list = fetch_bitwarden_items(vault, password)
    print('')

    seen_entries = Counter({})
    types = {1: _login, 2: _note, 3: _card, 4: _identity}
    for item in items_list:
        group_id = 'root'
        dest_group = kpo.root_group
        if item['folderId'] in groups:
            group_id = item['folderId']
            dest_group = groups[group_id]

        title, username, password, url, notes = types[item['type']](item)

        seen_key = ''.join((group_id or "", title, username if username is not None else ""))
        seen_entries[seen_key] += 1

        if seen_entries[seen_key] > 1:
            title = ''.join((title, ' (', str(seen_entries[seen_key] - 1), ')'))

        kpo.add_entry(
            dest_group,
            title, username, password,
            url=url, notes=notes
        )

    kpo.save()
