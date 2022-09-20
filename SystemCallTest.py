# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 14:00:34 2022

@author: Manuel Rufin
"""

import os
import subprocess
import shlex

FUllCommand = """python BowstringWidget.py 1e-6 1.4e-6 "BSFibril-14.tif"
"""

SplitCommand = shlex.split(FUllCommand)

#p = subprocess.Popen(FUllCommand, shell=True, stdout = subprocess.PIPE, encoding='UTF-8')
#p = subprocess.Popen(SplitCommand, shell=False,bufsize=0, stdout  subprocess.PIPE, encoding='UTF-8')

cmd = SplitCommand

with subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1,universal_newlines=True) as p:
    for line in p.stdout:
        print(line, end='')

