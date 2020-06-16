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
import json
import os
import datetime
import numpy as np
from framework.reader import ConstraintParser


class Evaluate:
    """This class evaluates a generated timetable.

    The evaluation is performed using some specified metrics.

    The quality indicators "practicals on the same day as lectures" and "stay in the same room vs. change rooms"
    are not taken into account.

    It is assumed that all hard constraints are satisfied.
    """

    metrics_file_path = "framework/evaluation_metrics.json"
    score = 0

    def __init__(self, timetable, check_hard_constraints=True, silent=False, excel_file_path='./InputOutput/Sample.xlsx'):
        self.silent = silent
        self.read_metrics()
        self.timetable = timetable

        self.is_valid = True

        if check_hard_constraints:
            self.check_hard_constraints(excel_file_path)
        self.evaluation()

        if not self.silent:
            print('\n[FINAL RESULT] Schedule score: %0.2f' % (self.score))

    def read_metrics(self):
        if not self.silent:
            print('[INFO] Reading metrics file...')
        with open(os.path.realpath(self.metrics_file_path), "r") as f:
            self.metrics = json.load(f)

        self.preferences = self.metrics['preferences']
        self.weights = self.metrics['weights']

    def conflict(self, c, message):
        if not self.silent:
            print(message)
        c["Conflict"] = True
        self.is_valid = False

    def check_hard_constraints(self, excel_file_path):
        self.constraints = ConstraintParser(excel_file_path)
        if not self.silent:
            print('[INFO] Checking hard constraints ...')
        courses = {}
        for timeslot in self.timetable:
            date = timeslot.split()[0]
            dt = datetime.datetime.strptime(date, '%Y-%m-%d')
            prog = []
            room = []
            electives = {}
            lecturers = []
            for c in self.timetable[timeslot]:
                c["Conflict"] = False
                course_data = self.constraints.get_courses()[c['CourseID']]
                # Programme conflicts (same programme twice in a timeslot)
                if c['ProgID'] not in prog:
                    prog.append(c['ProgID'])
                elif not course_data['Elective']:
                    self.conflict(c, '[CONFLICT] Conflict in programme %s on %s' % (c['ProgID'], timeslot))
                if course_data['Elective']:
                    if c['ProgID'] not in electives.keys():
                        electives.setdefault(c['ProgID'], [])
                    if c['CourseID'] not in electives[c['ProgID']]:
                        electives[c['ProgID']].append(c['CourseID'])
                    else:
                        self.conflict(c, '[CONFLICT] Conflict in programme %s on %s' % (c['ProgID'], timeslot))
                # Room conflicts
                if c['RoomID'] not in room or c['RoomID'] == '-1':
                    room.append(c['RoomID'])
                else:
                    self.conflict(c, '[CONFLICT] Conflict in room %s on %s' % (c['RoomID'], timeslot))
                # Lecturer conflicts
                for lecturer in course_data['Lecturers'].split(';'):
                    if lecturer not in lecturers:
                        lecturers.append(lecturer)
                    else:
                        self.conflict(c, '[CONFLICT] Conflict with lecturer %s on %s' % (lecturer, timeslot))
                    if lecturer in self.constraints.get_lecturers():
                        if dt in self.constraints.get_lecturers()[lecturer]:
                            self.conflict(c, '[CONFLICT] Conflict with lecturer %s on %s' % (lecturer, timeslot))
                # Room size
                if c['RoomID'] != '-1' and course_data['Number of students'] > self.constraints.get_rooms()[c['RoomID']]['Capacity']:
                    self.conflict(c, '[CONFLICT] Conflict with capacity in room %s on %s' % (c['RoomID'], timeslot))
                # Count to check contact hours
                if c['CourseID'] not in courses.keys():
                    courses.setdefault(c['CourseID'], 2)
                else:
                    courses[c['CourseID']] += 2
                # check holidays
                if self.constraints.get_holidays()[dt] == 1:
                    self.conflict(c, '[CONFLICT] Conflict with holiday on %s' % timeslot)
                # check period
                if dt < self.constraints.get_period_info()["StartDate"] or dt > self.constraints.get_period_info()["EndDate"]:
                    self.conflict(c, '[CONFLICT] Conflict with period date on %s' % timeslot)
        # check contact hours
        if not len(courses) == len(self.constraints.get_courses()):
            self.conflict({}, "[CONFLICT] Conflict in number of courses.")
        for course in courses:
            if course not in self.constraints.get_courses():
                self.conflict({}, "[CONFLICT] Unknown course %s" % course)
            if courses[course] != self.constraints.get_courses()[course]['Contact hours']:
                self.conflict({}, "[CONFLICT] Conflict in contact hours of course %s" % course)
        if not self.silent:
            print('[INFO] Finished checking hard constraints.\n')

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
            total = results["succeeds"][i] + results["fails"][i]
            if not self.silent:
                print(text % (
                    results["succeeds"][i], total, self.preferences[name][pref] * 100, pref))
            if total == 0:
                if not self.silent:
                    print('[INFO] Skipping this preference.')
            else:
                add = ((results["succeeds"][i] / total) * self.preferences[name][pref]) * self.weights[name]
                if not self.silent:
                    print('[RESULT] This adds %.5f to the score.' % add)
                self.score += add

    def evaluation(self):
        """
        Evaluate the schedule and calculate the score.
        """
        if not self.silent:
            print("[INFO] Evaluating schedule...")

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
        # boolean to indicate if "none" day off applies

        # initialize variables to evaluate break length
        break_length = [int(i) for i in self.preferences['break_length']]
        break_length_results = self.init_counters(break_length)

        # initialize variables to evaluate if schedule is the same every week
        weeks_per_course = {}
        week_counter = 0

        # loop over timetable timeslot by timeslot
        date = ""
        week_index = 0
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
                            # cannot have "none" day off in that week
                            if prog not in has_day_off_per_prog:
                                has_day_off_per_prog.append(prog)
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
                dt = datetime.datetime.strptime(date, '%Y-%m-%d')
                # day index for days off constraints
                day_index = dt.weekday()
                if day_index > 4:
                    raise Exception("Courses on the weekend in %s" % timeslot)
                # if a new week starts ...
                if not dt.isocalendar()[1] == week_index:
                    if week_index > 0:
                        # ... first evaluate previous week ...
                        # check how often "none" day off succeeded / failed
                        for prog in all_progs:
                            if prog in has_day_off_per_prog:
                                days_off_results["fails"][5] += 1
                            else:
                                days_off_results["succeeds"][5] += 1

                    # ... then reset variables
                    has_day_off_per_prog = []  # for "none" day_off
                    week_index = dt.isocalendar()[1]
                    week_counter += 1

            # process lectures of that timeslot

            # increment break length if there was already a lecture for the programme but there is none in this timeslot
            for prog in break_length_per_prog:
                if prog not in [c['ProgID'] for c in self.timetable[timeslot]]:
                    break_length_per_prog[prog] += 1

            # add lectures to hours per day
            # (use the set because multiple electives for the same programme can be in a timeslot)
            for prog in set([c['ProgID'] for c in self.timetable[timeslot]]):
                if prog not in hours_per_prog:
                    hours_per_prog.setdefault(prog, 2)
                else:
                    hours_per_prog[prog] += 2  # FIXME I'm assuming every timeslot is 2h long

                # add it as starting time if there was no lecture in that course before
                if prog not in starting_time_per_prog:
                    starting_time_per_prog.setdefault(prog, timeslot.split()[1])

                # set break length to 0
                if prog not in break_length_per_prog:
                    break_length_per_prog.setdefault(prog, 0)

            # add lectures to regularity matrix
            # TODO timeslots are hardcoded here
            for course in self.timetable[timeslot]:
                if course['CourseID'] not in weeks_per_course:
                    weeks_per_course.setdefault(course['CourseID'], np.zeros((5, 4)))
                if timeslot.split()[1] == "08:30:00":
                    i = 0
                elif timeslot.split()[1] == "11:00:00":
                    i = 1
                elif timeslot.split()[1] == "13:30:00":
                    i = 2
                else:
                    i = 3
                weeks_per_course[course["CourseID"]][day_index][i] += 1

        # add results to final score
        self.evaluate_regularity(weeks_per_course, week_counter)
        self.add_to_score(max_hours_results, 'max_hours_per_day',
                          '[RESULT] %i days (separately for each programme) out of %i satisfy the %.3f%% of people who want at most %s hours/day.')
        self.add_to_score(starting_times_results, 'starting_time',
                          '[RESULT] %i days (separately for each programme) out of %i satisfy the %.3f%% of people who want to start at %s.')
        self.add_to_score(days_off_results, 'day_off',
                          '[RESULT] %i days (separately for each programme) out of %i satisfy the %.3f%% of people who want a day off on %s.')
        self.add_to_score(break_length_results, 'break_length',
                          '[RESULT] %i days (separately for each programme) out of %i satisfy the %.3f%% of people who want a break of %s timeslots.')
        if not self.silent:
            print("[INFO] Finished evaluating.")

    def evaluate_regularity(self, weeks_per_course, weeks):
        """
        Evaluates how regular a schedule is.
        """
        all_lectures = 0  # sum of all lectures
        regular_lectures = 0  # sum of lectures that are regular
        # look at the distribution of lectures for each course
        for course in weeks_per_course:
            matrix = weeks_per_course[course]
            # add total number of lectures
            sum = matrix.sum()
            all_lectures += sum
            val = 0
            # in an optimal regular schedule, (sum/weeks) timeslots are needed. Therefore, the (sum/weeks) most frequent
            # timeslots are added to regular_lectures
            while val < sum:
                val += weeks
                # find max and add it to regular_lectures
                max = np.amax(matrix)
                regular_lectures += max
                # set to 0 so that it cannot be used in the next iteration
                where = np.where(matrix == max)
                matrix[where[0][0]][where[1][0]] = 0

        # add result to score
        add = (regular_lectures / all_lectures) * self.preferences['same_schedule_every_week']['true'] * self.weights[
            'same_schedule_every_week']
        if not self.silent:
            print('[RESULT] %i lectures out of %i satisfy the %.3f%% of people who want the same schedule every week.' % (
                regular_lectures, all_lectures, self.preferences['same_schedule_every_week']['true']))
            print('[RESULT] This adds %.5f to the score.' % add)
        self.score += add

    def get_score(self):
        return self.score

    def is_valid(self):
        return self.is_valid