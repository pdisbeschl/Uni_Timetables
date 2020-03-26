"""
Greedy Timetable scheduler
===================

author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner
author: Paul Disbeschl
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

Documented following PEP 257.
"""

from framework.scheduler import Scheduler

class Greedy(Scheduler):
    logFile = open(__file__ + "\..\..\Logs\log.txt", "a")

    def __init__(self):
        self.logFile.write('Initialising Greedy algorithm\n')
        super().__init__()


    def generate_timetable(self):
        print(self.constraints.get_courses())
        """
        Generates a timetable.

        Input
        -----
        input_dir: string
            path where input files are located.
        algorithm: type
            algorithm to use to generate the timetable.
        """
        pass
