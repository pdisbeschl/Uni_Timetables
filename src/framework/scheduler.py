"""
Timetable scheduler
===================

author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner
author: Paul Disbeschl
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

Documented following PEP 257.
"""

from abc import ABCMeta, abstractmethod
import time

"""
Main scheduler class
Generates a timetable according to the specified input data and selected
algorithm.
"""
class Scheduler(metaclass=ABCMeta):

    """ Any initialisation steps that all algorithms need """
    #I am thinking of reading a schedule, starting a timer to measure runtime etc.
    def __init__(self):
        pass

    """ Evaluates a timetable """
    def __evaluate(self):
        pass

    """ Starts a timer to measure the runtime of an algorithms """
    def start_timer(self):
        self.start_time = time.time()
        print(self.start_time)

    """ Once the algorithm has terminated, stop the timer """
    def stop_timer(self):
        self.stop_time = time.time()
        print(self.stop_time)

    """
    Tries to compute the runtime based on the start_time and stop_time.
    If either time is not defined, return -1
    """
    def get_runtime(self):
        try:
            self.runtime = self.stop_time - self.start_time
            return self.runtime
        except:
            return -1