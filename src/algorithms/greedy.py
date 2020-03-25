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
    def __init__(self):
        super().__init__()

    def generate_timetable(self, input_dir, algorithm):
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
