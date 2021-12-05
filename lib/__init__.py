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


def convert(input_file, output):
    if 'BITWARDEN_PASS' in os.environ:
        password = os.environ['BITWARDEN_PASS']
    else:
        password = getpass.getpass('Master Password: ')
    print('')

    kp = pykeepass.create_database(output, password=password)

    vault = None
    if input_file is not None:
        input_str = ""
        with codecs.open(input_file, 'r', 'utf-8') as f:
            input_str = f.read()

        try:
            vault = json.loads(input_str)
            if vault['encrypted'] is True:
                print("Unsupported: exported json file is encrypted")
                sys.exit(-1)
        except json.decoder.JSONDecodeError:
            sys.exit(-1)

    folders_list = fetch_bitwarden_folders(vault, password)
    groups = create_keepass_groups(kp, folders_list)

    items_list = fetch_bitwarden_items(vault, password)
    print('')

    seen_entries = Counter({})
    for x in items_list:
        group_id = 'root'
        dest_group = kp.root_group
        if x['folderId'] in groups:
            group_id = x['folderId']
            dest_group = groups[group_id]

        url = None
        if 'uris' in x['login'] and len(x['login']['uris']) > 0:
            url = x['login']['uris'][0]['uri']

        username = x['login']['username']
        if username is None:
            username = ''

        password = x['login']['password']
        if password is None:
            password = ''

        title = x['name']

        seen_key = ''.join((group_id, title, username))
        seen_entries[seen_key] += 1

        if seen_entries[seen_key] > 1:
            title = ''.join((title, ' (', str(seen_entries[seen_key] - 1), ')'))

        kp.add_entry(
            dest_group,
            title, username, password,
            url=url, notes=x['notes']
        )

    kp.save()

