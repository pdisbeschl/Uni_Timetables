"""
Genetic Timetable scheduler
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
import numpy as np
import random
import math


class Genetic(Scheduler):
    def __init__(self):
        super().__init__()
        self.population = []
        self.population_size = 250
        self.individual_size = 20 * 8
        self.generations = 50
        self.crossover_probability = 0.8
        self.mutation_probability = 0.2

    def generate_timetable(self):

        courses = self.hard_constraints.get_courses()
        rooms = self.hard_constraints.get_rooms()
        free_timeslots = self.hard_constraints.get_free_timeslots()
        self.create_population()
        list_fitness_pop = []
        for i in self.population:
            score = self.fitness(i, courses, rooms)
            list_fitness_pop.append(i, score)
        print('111111')

    def crossover(self, individual1, individual2):
        individual1_new = individual1.copy()
        individual2_new = individual2.copy()

        for i in range(self.individual_size):
            if random.random() < self.crossover_probability:
                individual1_new[i] = individual2[i]
                individual2_new[i] = individual1[i]

        return individual1_new, individual2_new

    def mutate(self, individual):
        individual_m = individual.copy()

        for i in range(self.individual_size):
            if random.random() < self.mutation_probability:
                individual_m[i] = 222

        return individual_m

    def selection(self, population):
        index1 = random.randint(0, self.population_size - 1)
        while True:
            index2 = random.randint(0, self.population_size - 1)
            if index2 != index1:
                break
        individual_s = population[index1]
        if index2 > index1:
            individual_s = population[index2]

        return individual_s

    def fitness(self, individual, courses, rooms):
        list_courses = list(courses)
        lis_rooms = list(rooms)
        count = 0
        score = 0
        for g in individual:
            if g != 0:
                c = courses[list_courses[int(g) - 1]]
                r = rooms[lis_rooms[count % 8]]
                s = math.floor(count / 8)
                if c["Number of students"] >= r["Capacity"]:
                    score += 1
                if not has_lecturer_conflict(g, count, individual, courses):
                    score += 1
                if s == 2:
                    score += 1

            count += 1
        return score

    # individual is list of classes (course with timeslot and room)
    def create_population(self):
        courses = list(range(1, 22))
        for p in range(self.population_size):
            # 20 slots, 8 rooms per week
            individual = np.zeros(20 * 8)
            c = 0
            while c < len(courses):
                pos = random.randint(0, 20 * 8 - 1)
                if individual[pos] == 0:
                    individual[pos] = courses[c]
                    c += 1
            self.population.append(individual)

    def get_schedule(self):
        return self.schedule


# check lecture conflict in slot time of day
# gen = class
def has_lecturer_conflict(gen, pos, individual, courses):
    list_courses = list(courses)
    low_slot = pos - (pos % 8)
    high_slot = pos - (pos % 8) + 8

    gen_course = courses[list_courses[int(gen) - 1]]
    lecturers = gen_course["Lecturers"].split(';')

    for g in individual[low_slot:high_slot]:
        if g != 0 and g != gen:
            c = courses[list_courses[int(g) - 1]]
            list_lecturers = c["Lecturers"].split(';')
            for l in list_lecturers:
                if l in lecturers:
                    return True
    return False
