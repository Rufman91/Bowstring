# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 14:00:34 2022

@author: Manuel Rufin
"""

import os
import time
import subprocess
import shlex
import psutil

def parse_and_execute_instructions(InList):
    for S in InList:
        print(S)
    time.sleep(5)
    return

FullCommand = """python BowstringWidget.py 1e-6 1.4e-6 "BSFibril-14.tif"
"""

SplitCommand = shlex.split(FullCommand)

#p = subprocess.Popen(FullCommand, shell=True, stdout = subprocess.PIPE, encoding='UTF-8')
#p = subprocess.Popen(SplitCommand, shell=False,bufsize=0, stdout  subprocess.PIPE, encoding='UTF-8')

cmd = SplitCommand


with subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1,universal_newlines=True) as p:
    Instructions=['Waiting']
    psProcess = psutil.Process(pid=p.pid)
    for line in p.stdout:
        if line=='InstructionStart\n':
            Instructions = ['InstructionStart']
        elif line=='InstructionEnd\n' and Instructions[0]=='InstructionStart':
            Instructions.append(line[0:-1])
            # psProcess.suspend()
            BlockNewInstructions = True
            parse_and_execute_instructions(Instructions)
            # psProcess.resume()
            Instructions = ['Waiting']
        elif Instructions[0]=='Waiting':
            print('Waiting...')
            continue
        else:
            Instructions.append(line[0:-1])
        # print(Instructions)
        # print(line)
