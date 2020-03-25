from algorithms.greedy import Greedy
from algorithms.ilp import ILP
import time

def main():
    print("Calling main")
    logFile = open(__file__ + "\..\Logs\log.txt", "a")
    logFile.write('Logging something useful')
    x = Greedy()
    y = ILP()
    x.start_timer()
    time.sleep(5)
    x.stop_timer()
    print(x.get_runtime())

if __name__ == '__main__':
    main()
