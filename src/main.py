from algorithms.greedy import Greedy
from algorithms.ilp import ILP
from algorithms.random import Random
from algorithms.weekly import Weekly
from algorithms.tabu import Tabu
from framework.reader import ConstraintParser
from framework.evaluate import Evaluate
import time
import json
import datetime
import pprint
import os 
import re
import copy
from json2html import *
import webbrowser
from gui.gui import GUI

if __name__ == '__main__':
    #####Run with GUI
    #GUI()

    #####Run without GUI
    # ILP = 0 
    # Greedy = 1
    # Tabu = 2
    # Random = 3
    #  Weekly = 4
    GUI(alg=0)
