# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 13:10:55 2020

@author: beck
"""
from geotag import match
from tkinter.filedialog import askdirectory
from tkinter import *

def init(dir1, dir2):
    match(inputPath=dir1,projectPath=dir2)

root = Tk()
print('Input Path: ', end = ' ')
root.update()
dir1 = askdirectory()
print(dir1)    
print('Output Path: ', end = ' ')
root.update()
dir2 = askdirectory()
print(dir2)
root.destroy()

init(dir1, dir2)