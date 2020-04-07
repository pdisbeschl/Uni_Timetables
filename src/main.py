from algorithms.greedy import Greedy
from algorithms.ilp import ILP
from algorithms.random import Random
from framework.reader import ConstraintParser
import time
import json
import datetime
import pprint
import os 
from json2html import *
import webbrowser

def myconverter(o):
    if isinstance(o, datetime):
        return o.timestamp()

def see_output(out):
    new_out = {}
    for i in out.keys():
        new_out.setdefault(i.split(' ')[0], {}).setdefault(i.split(' ')[1], out[i])
    #print(new_out)
    with open(os.path.realpath('./InputOutput/out.html'), "w") as f:
        f.write('<link rel="stylesheet" type="text/css" href="style.css">')
        f.write(json2html.convert(json=json.dumps([new_out], indent=4)))
    url = "file://"+os.path.realpath('./InputOutput/out.html')
    webbrowser.open(url,new=2)

def main():
    print("Calling main")
    logFile = open(os.path.realpath('./Logs/log.txt'), "w")
    logFile.write('Starting scheduling algorithm\n')
    x = Greedy()
    x.generate_timetable()
    pp = pprint.PrettyPrinter(depth=6)
    output = open(os.path.realpath('./InputOutput/out.json'), "w")
    #out = pp.pformat(x.get_schedule())
    out = json.dumps(x.get_schedule(), indent=4)
    output.write(out)

    see_output(x.get_schedule())
    
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
    main()
