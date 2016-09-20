#!/usr/bin/python
"""
Python script to parse converted folder and start adding ID3 tags
"""
from mutagen.easyid3 import EasyID3
from os import walk
import os
from termcolor import colored

class test(object):
  def __init__ (self, string):
    self.string = string
    self.sup = "sup"
    self.dude = 1
    self.no = "no"

  def one(self):
    return self.string, self.sup, self.dude, self.no

if __name__ == "__main__":
  yy = test("Here is a string")
  yy.sup = "Redefined"
  (a, b, c, d) = yy.one()

  print a, b, c, d

