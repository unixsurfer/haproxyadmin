#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# File name: a.py
#
# Creation date: 09-04-2015
#
# Created by: Pavlos Parissis <pavlos.parissis@booking.com>
#
import re


def main():
    # [[:digit:]]{1,}\. [0-9A-Za-z_]{1,} \[.*B.*\]:'
    frontend = []
    backend = []
    server = []
    with open('/home/pparissis/configuration.txt') as file:
        for line in file:
            line = line.strip()
            match = re.search(r'\d+\. (\w+) (\[.*\]:) .*', line)
            if match:
                if 'F' in match.group(2):
                    frontend.append(match.group(1))
                if 'B' in match.group(2):
                    backend.append(match.group(1))
                if 'S' in match.group(2):
                    server.append(match.group(1))
    print("FRONTEND_METRICS = [")
    for m in frontend:
        print("{:<4}'{}',".format('', m))
    print("]")
    print("POOL_METRICS = [")
    for m in backend:
        print("{:<4}'{}',".format('', m))
    print("]")
    print("SERVER_METRICS = [")
    for m in server:
        print("{:<4}'{}',".format('', m))
    print("]")


# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
