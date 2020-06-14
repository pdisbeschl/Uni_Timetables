"""
Weekly Timetable scheduler (based off of the tabu search algorithm)
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
from algorithms.random import Random
import os
import numpy as np
import copy
import sys


class Tabu(Scheduler):
    logFile = open(os.path.realpath('./Logs/log.txt'), "a")
    iteration = 0  # number of current iteration
    # TODO test which values work best
    max_tabu_size = 10  # max size of the tabu list
    total_iterations = 100  # total number of iterations
    placements_to_move = 5  # number of placements to consider in neighborhood

    def __init__(self):
        super().__init__()

    def generate_timetable(self, initial_schedule=None):
        """
        Generates a timetable following a simple tabu search algorithm (see https://en.wikipedia.org/wiki/Tabu_search#Pseudocode).
        The initial timetable can be given but it must satisfy all hard constraints.
        """
        if initial_schedule is None:
            random = Random()
            random.generate_timetable()
            initial_schedule = random.get_schedule()
        # sort initial schedule to make it easier to compare
        for k in initial_schedule.keys():
            initial_schedule[k].sort(key=lambda kv: (kv["CourseID"], kv["CourseID"]))
        # initialize variables
        best_schedule = initial_schedule
        best_schedule_value = self.evaluate(best_schedule)
        tabu_list = [best_schedule]
        best_candidate = best_schedule
        # follow basic tabu search algorithm
        while not self.stopping_condition():
            # get neighbors of current candidate
            neighbors = self.get_neighbors(best_candidate)
            # reset best value
            best_candidate_value = - sys.maxsize
            # find best neighbor that is not in tabu list
            for candidate in neighbors:
                if candidate not in tabu_list:
                    candidate_value = self.evaluate(candidate)
                    if candidate_value > best_candidate_value:
                        best_candidate = candidate
                        best_candidate_value = candidate_value
            # compare it to current best schedule and update if required
            if best_candidate_value > best_schedule_value:
                best_schedule = best_candidate
                best_schedule_value = best_candidate_value
            # add candidate to tabu list
            tabu_list.append(best_candidate)
            # remove first item if tabu list gets too long
            if len(tabu_list) > self.max_tabu_size:
                tabu_list.pop(0)
        # best schedule is found
        self.schedule = best_schedule

    def stopping_condition(self):
        """
        Returns whether searching should stop.
        """
        # stop after fixed number of iterations for now
        # TODO use more refined criterium e.g. only small improvement
        self.iteration += 1
        return self.iteration > self.total_iterations

    def get_neighbors(self, schedule):
        """
        Returns the neighbors to a given schedule.
        Right now, random lectures are chosen and moved to other timeslots without violating the hard constraints.
        """
        neighbors = []
        chosen_indices = []
        for _ in range(0, self.placements_to_move):
            # randomly choose a placement to move
            # first randomly choose a timeslot ...
            timeslot_index = np.random.randint(0, len(schedule))
            current_timeslot_name = list(schedule.keys())[timeslot_index]
            current_timeslot = schedule[current_timeslot_name]
            # only consider timeslots that have at least one lecture scheduled
            if not current_timeslot:
                continue
            # ... then randomly choose a lecture from that timeslot
            index = np.random.randint(0, len(current_timeslot))
            lecture = current_timeslot[index]
            # make sure not to consider the same lecture twice
            if [timeslot_index, index] in chosen_indices:
                continue
            chosen_indices.append([timeslot_index, index])
            # remove lecture from schedule
            schedule[current_timeslot_name].pop(index)
            # go through all timeslots and check if it is possible to put the lecture there instead
            for timeslot_name in schedule.keys():
                # do not put lecture in timeslot it originally was in
                if timeslot_name == current_timeslot_name:
                    continue
                timeslot = schedule[timeslot_name]
                # check if lecture can be put in the timeslot
                if self.is_possible_placement(lecture, timeslot):
                    # put it there
                    schedule[timeslot_name].append(lecture)
                    # sort schedule to make it better comparable
                    schedule[timeslot_name].sort(key=lambda kv: (kv["CourseID"], kv["CourseID"]))
                    # add copy of current schedule to neighbors
                    neighbors.append(copy.deepcopy(schedule))
                    # set it to original value again
                    schedule[timeslot_name] = timeslot
            # put lecture back to original place
            schedule[current_timeslot_name].append(lecture)
        return neighbors

    def is_possible_placement(self, lecture, timeslot):
        """
        Checks if lecture can be placed in the timeslot.
        (Most code copied from Greedy)
        """
        course_data = self.hard_constraints.get_courses()[lecture["CourseID"]]
        for other_lecture in timeslot:
            other_course_data = self.hard_constraints.get_courses()[other_lecture["CourseID"]]
            # Check if programme already has another course in the timeslot
            if lecture["ProgID"] == other_lecture["ProgID"]:
                # exclude electives
                if not course_data["Elective"] or not other_course_data["Elective"]:
                    return False
            # Check if any of the lecturers already has another course in the timeslot
            for lecturer in course_data["Lecturers"].split(";"):
                if lecturer in other_course_data["Lecturers"]:
                    return False
            # TODO check more constraints (e.g. availability of lecturer and room (or find a new room))
        return True

    def evaluate(self, schedule):
        """
        Evaluates a schedule assuming that no hard constraint is violated.
        """
        # This is just a simple dummy to check if the algorithm works.
        # The idea is to favor early timeslots early in the block,
        # simply because it is easy to test if the algorithm improves the schedules.
        # TODO Replace by a real evaluation function
        value = 0
        days = len(self.hard_constraints.get_free_timeslots()) / 4
        date = ""
        for timeslot in schedule.keys():
            if timeslot.split()[0] != date:
                # less value if we move to the next day
                days -= 1
            for courses in schedule[timeslot]:
                # the earlier in the day the better
                time = timeslot.split()[1]
                if time == "08:30:00":
                    value += 3
                elif time == "11:00:00":
                    value += 2
                elif time == "13:30:00":
                    value += 1
                elif time == "16:00:00":
                    value += 0
                # the earlier in the block the better
                value += days
        return value
