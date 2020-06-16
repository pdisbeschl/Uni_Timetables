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
    GUI()

    #####Run without GUI
    # ILP = 0 
    # Greedy = 1
    # Tabu = 2
    # Random = 3
    #  Weekly = 4
    #GUI(alg=0)

    #### Load a timetable and get the score (from the json output)
    '''
    schedule = json.load(open('./examples/MA_AI-DSDM_Y1_p5.json','r'))
    #schedule = json.load(open('./InputOutput/out.json','r'))
    schedule = {str(k): v for k, v in schedule.items()}
    print(schedule)
    Evaluate(schedule, False)
    '''