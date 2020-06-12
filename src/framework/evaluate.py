"""
Evaluate the generated timetables according to the given metrics
===================

author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner
author: Paul Disbeschl
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

Documented following PEP 257.
"""
import sys
import json
import os
import datetime


class Evaluate:
    """This class evaluates a generated timetable.

    The evaluation is performed using some specified metrics.

    The quality indicators "practicals on the same day as lectures" and "stay in the same room vs. change rooms"
    are not taken into account.

    It is assumed that all hard constraints are satisfied.
    """

    metrics_file_path = "framework/evaluation_metrics.json"
    score = 0

    def __init__(self, timetable):
        self.read_metrics()
        self.timetable = timetable
        # self.check_conflicts() #FIXME not necessary now, also it doesnt check the 'elective' boolean
        self.evaluation()
        print('\n[FINAL RESULT] Schedule score: %0.2f' % (self.score))

    def read_metrics(self):
        print('[INFO] Reading metrics file...')
        with open(os.path.realpath(self.metrics_file_path), "r") as f:
            self.metrics = json.load(f)

        self.preferences = self.metrics['preferences']
        self.weights = self.metrics['weights']

    def check_conflicts(self):
        print('[INFO] Checking conflicts...')
        for day in self.timetable:
            for timeslot in self.timetable[day]:
                prog = []
                room = []
                for c in self.timetable[day][timeslot]:
                    # Programme conclicts (same programme twice in a timeslot)
                    if c['ProgID'] not in prog:
                        prog.append(c['ProgID'])
                    else:
                        raise Exception('Conflict in programme %s on %s at %s' % (c['ProgID'], day, timeslot))
                    # Room conflicts
                    if c['RoomID'] not in room:
                        room.append(c['RoomID'])
                    else:
                        raise Exception('Conflict in room %s on %s at %s' % (c['RoomID'], day, timeslot))
                    # Lecturer conflicts
                    # TODO

        print('[Success] No conflicts.')

    def init_counters(self, cases):
        """
        Helper function that initializes maps with counters how often different cases fail / succeed.
        """
        return {"fails": [0 for _ in cases],
                "succeeds": [0 for _ in cases]}

    def add_to_score(self, results, name, text):
        """
        Helper function that prints info and adds to score.
        """
        for i, pref in enumerate(self.preferences[name]):
            print(text % (
                    results["succeeds"][i], results["succeeds"][i] + results["fails"][i], self.preferences[name][pref], pref))
            print('[RESULT] This adds %.2f to the score.' % (results["succeeds"][i] * self.preferences[name][pref]))
            self.score += (results["succeeds"][i] * self.preferences[name][pref]) * self.weights[name]

    def evaluation(self):
        """
        Evaluate the schedule and calculate the score.
        """
        # initialize variables to evaluate max hours per day
        max_hours = [int(i) for i in self.preferences['max_hours_per_day']]
        max_hours_results = self.init_counters(max_hours)

        # initialize variables to evaluate starting times
        starting_times = [i for i in self.preferences['starting_time']]
        starting_times_results = self.init_counters(starting_times)

        # initialize variables to evaluate days off
        # note: days were there are no lectures at all do not count
        days_off = [i for i in self.preferences['day_off']]
        days_off_results = self.init_counters(days_off)
        # as this is about programmes that do not have lectures on a day, we need to know all programmes in the schedule
        all_progs = set([c["ProgID"] for timeslot in self.timetable for c in self.timetable[timeslot]])

        # initialize variables to evaluate break length
        break_length = [int(i) for i in self.preferences['break_length']]
        break_length_results = self.init_counters(break_length)

        # loop over timetable timeslot by timeslot
        date = ""
        for timeslot in self.timetable:
            # if a new day starts ...
            if timeslot.split()[0] != date:
                # ... first evaluate previous day ...
                if date != "":
                    # check how often max hours constraints succeeded / failed
                    for prog in hours_per_prog:
                        for i, max in enumerate(max_hours):
                            if hours_per_prog[prog] > max:
                                max_hours_results["fails"][i] += 1
                            else:
                                max_hours_results["succeeds"][i] += 1
                    # check how often starting time constraints succeeded / failed
                    for prog in starting_time_per_prog:
                        for i, time in enumerate(starting_times):
                            if starting_time_per_prog[prog] != time:
                                starting_times_results["fails"][i] += 1
                            else:
                                starting_times_results["succeeds"][i] += 1
                    # check how often day off constraints succeeded / failed
                    for prog in all_progs:
                        if prog in starting_time_per_prog.keys():
                            days_off_results["fails"][day_index] += 1
                        else:
                            days_off_results["succeeds"][day_index] += 1
                    # check how often break length constraints succeeded / failed
                    for prog in break_length_per_prog:
                        for i, l in enumerate(break_length):
                            if break_length_per_prog[prog] != l:
                                break_length_results["fails"][i] += 1
                            else:
                                break_length_results["succeeds"][i] += 1
                # ... then reset variables
                hours_per_prog = {}
                starting_time_per_prog = {}
                break_length_per_prog = {}
                date = timeslot.split()[0]
                # day index for weekday that is off
                day_index = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()

            # process lectures of that timeslot

            # increment break length if there was already a lecture for the programme but there is none in this timeslot
            for prog in break_length_per_prog:
                if prog not in [c['ProgID'] for c in self.timetable[timeslot]]:
                    break_length_per_prog[prog] += 1

            # add lectures to hours per day
            # (use the set because multiple electives for the same programme are in the same timeslot)
            for prog in set([c['ProgID'] for c in self.timetable[timeslot]]):
                if prog not in hours_per_prog:
                    hours_per_prog.setdefault(prog, 2)
                else:
                    hours_per_prog[prog] += 2  # FIXME I'm assuming every timeslot is 2h long

            # add it as starting time if there was no lecture in that course before
                if prog not in starting_time_per_prog:
                    starting_time_per_prog.setdefault(prog, timeslot.split()[1])
                if prog not in break_length_per_prog:
                    break_length_per_prog.setdefault(prog, 0)

        # add results to final score
        self.add_to_score(max_hours_results, 'max_hours_per_day',
                          '[RESULT] %i days (separately for each programme) out of %i satisfy the %.2f%% of people who want at most %s hours/day.')
        self.add_to_score(starting_times_results, 'starting_time',
                          '[RESULT] %i days (separately for each programme) out of %i satisfy the %.2f%% of people who want to start at %s.')
        self.add_to_score(days_off_results, 'day_off',
                          '[RESULT] %i days (separately for each programme) out of %i satisfy the %.2f%% of people who want a day off on %s.')
        self.add_to_score(break_length_results, 'break_length',
                          '[RESULT] %i days (separately for each programme) out of %i satisfy the %.2f%% of people who want a break of %s timeslots.')



