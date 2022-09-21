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
    
    SplitList = []
    for S in InList:
        SplitList.append(S.split(';'))
    
    print(InList)
    print(SplitList)
    
    StartStringCounter = 0
    EndStringCounter = 0
    for S in SplitList:
        if S[0]=='InstructionStart':
            StartStringCounter += 1
        elif S[0]=='InstructionEnd':
            EndStringCounter +=1
    if not (StartStringCounter==1 and EndStringCounter==1):
            print('Error: Instructions are faulty!')
            return
    SplitList.pop(0)
    SplitList.pop(-1)
    ModeSettings = SplitList.pop(0)
    print(ModeSettings)
    Mode = ModeSettings[0]
    if ModeSettings[1]=='True':
        RecordRealTimeScan = True
    elif ModeSettings[1]=='False':
        RecordRealTimeScan = False
    else:
        print('Error: Instructions are faulty!')
        return
    if ModeSettings[2]=='True':
        RecordVideo = True
    elif ModeSettings[2]=='False':
        RecordVideo = False
    else:
        print('Error: Instructions are faulty!')
        return
    RecordVideoNthFrame = ModeSettings[3]
    Points = []
    for S in SplitList:
        P = [float(S[0]) , float(S[1]) , float(S[2]) , float(S[3]) , S[4]]
        Points.append(P)
    
    if Mode=='PullAndHold':
        execute_instruction_list(Points,Mode,RecordRealTimeScan,RecordVideo,RecordVideoNthFrame)
    elif Mode=='PullAndHoldPositionCheck':
        execute_instruction_list(Points,Mode,RecordRealTimeScan,RecordVideo,RecordVideoNthFrame)
    else:
        print('%s is not an available Bowstring-mode' % Mode)
    time.sleep(5)
    return

def execute_instruction_list(Points,Mode,RecordRealTimeScan,RecordVideo,RecordVideoNthFrame):
    print('\n\nexecute_instruction_list\n\n')
    print(Mode)
    print(RecordRealTimeScan)
    print(RecordVideo)
    print(RecordVideoNthFrame)
    print(Points)

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
