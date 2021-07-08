#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
## Imports
##

#import pdb

import argparse
import getpass
import subprocess
import sys

import json
import pykeepass

##
## Functions
##

def fetchBWFolders(passw):
    print("Fetching folders...")

    r = subprocess.run(
        ["bw", "list", "folders"],
        input=passw.encode('utf-8'),
        stderr=sys.stderr,
        stdout=subprocess.PIPE
    )

    try:
        folders = json.loads(r.stdout)
        return folders
    except json.decoder.JSONDecodeError:
        sys.exit(-1)

def fetchBWItems(passw):
    print("Fetching items...")

    r = subprocess.run(
        ["bw", "list", "items"],
        input=passw.encode('utf-8'),
        stderr=sys.stderr,
        stdout=subprocess.PIPE
    )

    try:
        items = json.loads(r.stdout)
        return items
    except json.decoder.JSONDecodeError:
        sys.exit(-1)

def createKPGroups(kp, foldersList):
    d = {}
    
    for x in foldersList:
        name = x['name'].split('/')

        g = None
        parent = kp.root_group
        for n in name:
            if n == 'No Folder':
                g = kp.root_group
                break

            if n not in d:
                g = kp.add_group(parent, n)
                d[n] = g
            
            parent = d[n]
        
        d[x['id']] = g

    return d

def convert(output):
    passw = getpass.getpass('Master Password: ')
    print('')

    kp = pykeepass.create_database(output, password=passw)

    foldersList = fetchBWFolders(passw)
    groups = createKPGroups(kp, foldersList)
    
    itemsList = fetchBWItems(passw)
    print('')

    for x in itemsList:
        destGroup = kp.root_group
        if x['folderId'] in groups:
            destGroup = groups[x['folderId']]

        url = None
        if 'uris' in x['login'] and len(x['login']['uris']) > 0:
            url = x['login']['uris'][0]['uri']

        username = x['login']['username']
        if username is None:
            username = ''

        password = x['login']['password']
        if password is None:
            password = ''

        entry = kp.add_entry(
            destGroup,
            x['name'], username, password,
            url=url, notes=x['notes']
        )

    kp.save()

##
## Main
##

parser = argparse.ArgumentParser()

parser.add_argument("-o", "--Output", required = True, help = "Output kdbx file path")

args = parser.parse_args()
convert(args.Output)