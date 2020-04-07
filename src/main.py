from algorithms.greedy import Greedy
from algorithms.ilp import ILP
from framework.reader import ConstraintParser
import time
import json
import datetime
import pprint
import os 

def myconverter(o):
    if isinstance(o, datetime):
        return o.timestamp()


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
