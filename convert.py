#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# Imports
##

# import pdb

import argparse
import getpass
import subprocess
import sys

import json
import pykeepass

##
# Functions
##


def fetch_bitwarden_folders(password):
    print("Fetching folders...")

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


def fetch_bitwarden_items(password):
    print("Fetching items...")

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


def convert(output):
    password = getpass.getpass('Master Password: ')
    print('')

    kp = pykeepass.create_database(output, password=password)

    folders_list = fetch_bitwarden_folders(password)
    groups = create_keepass_groups(kp, folders_list)

    items_list = fetch_bitwarden_items(password)
    print('')

    for x in items_list:
        dest_group = kp.root_group
        if x['folderId'] in groups:
            dest_group = groups[x['folderId']]

        url = None
        if 'uris' in x['login'] and len(x['login']['uris']) > 0:
            url = x['login']['uris'][0]['uri']

        username = x['login']['username']
        if username is None:
            username = ''

        password = x['login']['password']
        if password is None:
            password = ''

        kp.add_entry(
            dest_group,
            x['name'], username, password,
            url=url, notes=x['notes']
        )

    kp.save()

##
# Main
##


parser = argparse.ArgumentParser()

parser.add_argument("-o", "--Output", required=True,
                    help="Output kdbx file path")

args = parser.parse_args()
convert(args.Output)
