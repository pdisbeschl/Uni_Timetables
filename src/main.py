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

def myconverter(o):
    if isinstance(o, datetime):
        return o.timestamp()


def main(alg=None):
    print("Calling main")
    logFile = open(os.path.realpath('./Logs/log.txt'), "w")
    logFile.write('Starting scheduling algorithm\n')

    algorithms = [Greedy(), Random(), Weekly(), ILP(), Tabu()]
    selectedAlgorithm = 3
    x = algorithms[selectedAlgorithm]
    
    x.generate_timetable()
    eval = Evaluate(x.get_schedule())
    print(eval.get_score())
    pp = pprint.PrettyPrinter(depth=6)
    output = open(os.path.realpath('./InputOutput/out.json'), "w")
    #out = pp.pformat(x.get_schedule())
    out = json.dumps(x.get_schedule(), indent=4)
    output.write(out)
    out = x.get_schedule()

    #see_output(x.get_schedule())
    output.write(json.dumps(out, indent=4))
    see_output2(out, x.get_period_info())
    #y = ILP()

    #constraints = ConstraintParser()
    #print(constraints.get_courses())
    #t = constraints.get_period_info()
    #logFile.write(str(t))
    #logFile.write("\n")
    #x.start_timer()
    #time.sleep(1)
    #x.stop_timer()
    #print(x.get_runtime())

if __name__ == '__main__':
    GUI()
