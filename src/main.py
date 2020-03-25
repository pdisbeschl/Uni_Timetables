from algorithms.greedy import Greedy
from algorithms.ilp import ILP
from framework.reader import ConstraintParser
import time
import json

def main():
    print("Calling main")
    logFile = open(__file__ + "\..\Logs\log.txt", "a")
    #logFile.write('Logging something useful')
    x = Greedy()
    y = ILP()

    constraints = ConstraintParser()
    print(constraints.get_courses())
    t = constraints.get_period_info()
    logFile.write(str(t))
    logFile.write("\n")
    x.start_timer()
    time.sleep(1)
    x.stop_timer()
    print(x.get_runtime())


if __name__ == '__main__':
    main()
