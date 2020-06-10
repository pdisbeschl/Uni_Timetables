"""
ILP Timetable scheduler
===================

author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner
author: Paul Disbeschl
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

Documented following PEP 257.
"""
from mip import *
from framework.scheduler import Scheduler

class ILP(Scheduler):
    def __init__(self):
        super().__init__()
        self.model = Model()
        self.model.verbose = 0

    def generate_timetable(self):
        self.generate_ILP_hard_constraints()
        self.tranform_to_schedule()
        return

    def generate_ILP_hard_constraints(self):
        free_timeslots = self.hard_constraints.get_free_timeslots()
        courses = self.hard_constraints.get_courses()

        #Define binarz decision variables for every course and timeslot. If the variable is 1 it means that the course
        # is scheduled at the timeslot
        x = [self.model.add_var(var_type=BINARY, name=str(tid)+";"+cid)for cid in courses.keys() for tid in free_timeslots]

        #Temporary objective function. It pretty much does nothing useful at the moment. Just adds all courses and timeslots
        #together
        self.model.objective = maximize(xsum(1 * self.model.var_by_name(str(tid)+";"+cid) for cid in courses.keys() for tid in free_timeslots))

        #Every course must have exactly #'contact hours' scheduled in the schedule
        for cid,course in courses.items():
            self.model.add_constr(xsum(self.model.var_by_name(str(tid)+";"+cid) for tid in free_timeslots) == course['Contact hours']/2)

        print("Testb")
        self.model.optimize(max_seconds=300)

        print("Test")
        self.selected = [x[i].name for i in range(len(x)) if x[i].x >= 0.9]
        self.selected.sort()

    def tranform_to_schedule(self):
        courses = self.hard_constraints.get_courses()
        for c in self.selected:
            tid,cid = c.split(";")
            prog_id = courses[cid]['Programme']
            self.schedule.setdefault(tid, []).append({"CourseID": cid, "ProgID": prog_id, "RoomID": "-1"})
        #Sort the schedule based on timeslots (hotfix)
        return
