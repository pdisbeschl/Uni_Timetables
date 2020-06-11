from algorithms.greedy import Greedy
from algorithms.ilp import ILP
from algorithms.random import Random
from algorithms.weekly import Weekly
from algorithms.tabu import Tabu
from framework.reader import ConstraintParser
import time
import json
import datetime
import pprint
import os 
import re
import copy
from json2html import *
import webbrowser

def myconverter(o):
    if isinstance(o, datetime):
        return o.timestamp()

def see_output(out):
    new_out = {}
    for i in out.keys():
        new_out.setdefault(i.split(' ')[0], {}).setdefault(i.split(' ')[1], out[i])
    #print(new_out)
    with open(os.path.realpath('./InputOutput/out.html'), "w") as f:
        f.write('<link rel="stylesheet" type="text/css" href="style.css">')
        f.write(json2html.convert(json=json.dumps([new_out], indent=4)))
    url = "file://"+os.path.realpath('./InputOutput/out.html')
    webbrowser.open(url,new=2)

def see_output2(out):
    version = '0.1' #FIXME change to add up with new versions
    fixed_out = {}
    for i in out.keys():
        fixed_out.setdefault(i.split(' ')[0], {}).setdefault(i.split(' ')[1], out[i])
    #Read base output table    
    f = open(os.path.realpath('./InputOutput/newOutput.html'), "r")
    html_original = f.read()
    p = re.compile('<div id="0">((.|\n)*)</div><!--0-->')
    div_1 = p.search(html_original).group(0)
    p = re.compile('<div id="1">((.|\n)*)</div><!--1-->')
    div_2 = p.search(html_original).group(0)
    #Insert timetable values
    num_weeks = int(len(fixed_out.keys())/7)
    html_original = html_original.replace('NUMWEEK','0')
    for i in range(1,num_weeks):
        html_original = html_original.replace('<!--0-->','\n'+div_1)
        html_original = html_original.replace('NUMWEEK',str(i))
    out_file =  open(os.path.realpath('./InputOutput/out.html'), "w")
    out_file.write('<link rel="stylesheet" type="text/css" href="style.css">')
    programme = ['BAY1','BAY2','BAY3','MAAIY1','MADSDMY1']
    full_html = ''
    #For each programme add a table
    for prog in programme:
        html = copy.copy(html_original)
        html = html.replace('PROGRAMME',prog)
        #Store result
        full_html += html

    week = 0
    aux = 0
    #Insert values from json
    for day in fixed_out:
        for timeslot in fixed_out[day]:
            for course in fixed_out[day][timeslot]:
                full_html = full_html.replace('_%s_%s_%s_COURSE_%s'%(aux,week,timeslot,course['ProgID']),course['CourseID'])
                full_html = full_html.replace('_%s_%s_%s_ROOM_%s'%(aux,week,timeslot,course['ProgID']),course['RoomID'])
                #print('_%s_%s_COURSE_%s'%(week,timeslot,course['ProgID']))
        #increase day count
        if aux==7:
            week+=1
            aux=0
        else:
            aux+=1
    #specify timetable version
    full_html = full_html.replace('_VERSION',version)
    #Remove empty spaces
    full_html = re.sub('_.*','',full_html)
    #Write result
    out_file.write(full_html)
    out_file.close()
    #Open browser
    url = "file://"+os.path.realpath('./InputOutput/out.html')
    webbrowser.open(url,new=2)


def main():
    print("Calling main")
    logFile = open(os.path.realpath('./Logs/log.txt'), "w")
    logFile.write('Starting scheduling algorithm\n')

    algorithms = [Greedy(), Random(), Weekly(), ILP(), Tabu()]

    selectedAlgorithm = 3

    x = algorithms[selectedAlgorithm]
    x.generate_timetable()
    pp = pprint.PrettyPrinter(depth=6)
    output = open(os.path.realpath('./InputOutput/out.json'), "w")
    #out = pp.pformat(x.get_schedule())
    out = json.dumps(x.get_schedule(), indent=4)
    output.write(out)

    #see_output(x.get_schedule())
    see_output(x.get_schedule())
    #y = ILP()
    
    #constraints = ConstraintParser()
    #print(constraints.get_courses())
    #t = constraints.get_period_info()
    #logFile.write(str(t))
    #logFile.write("\n")
    #x.start_timer()
    #time.sleep(1)
    #x.stop_timer()
    #print(x.get_runtime())

if __name__ == '__main__':
    main()
