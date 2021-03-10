# -*- coding: utf-8 -*-
"""
Created on Wed Mar 10 21:16:18 2021

@author: ASUS
"""

import argparse

def process_cl_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--currpos', action='store')
    parser.add_argument('--fullfile', action='store')

    parsed_args, unparsed_args = parser.parse_known_args()
    return parsed_args, unparsed_args


if __name__ == '__main__':
    import sys
    parsed_args, unparsed_args = process_cl_args()
    qt_args = sys.argv[:1] + unparsed_args
    app = QApplication(qt_args)
    ex = MainWindow()
    sys.exit(app.exec_())