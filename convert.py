#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# Imports
##

# import pdb

import argparse

import lib

##
# Main
##

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--Input", required=False,
                    help="BitWarden unencrypted JSON file")

parser.add_argument("-o", "--Output", required=True,
                    help="Output kdbx file path")

args = parser.parse_args()

lib.convert(args.Input, args.Output)
