# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 14:00:34 2022

@author: Manuel Rufin
"""

import subprocess
import time

FUllCommand = """python BowstringWidget.py 1e-6 1.4e-6 "BSFibril-14.tif"
"""

MyProcess = subprocess.Popen(FUllCommand, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding='UTF-8')

ReturnCode = None

while ReturnCode==None:
    print('...')
    time.sleep(1)
    ReturnCode = MyProcess.poll()
    
print(ReturnCode)
print('STDOUT:')
print(MyProcess.stdout.read())
print('STDERR:')
print(MyProcess.communicate()[1])
