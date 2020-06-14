"""
GUI
===================
author: Daniel Kaestner
author: Paul Disbeschl 
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim
author: Huy Ngo
author: Yu Fee Chan

Documented following PEP 257.
"""
from PyQt5 import uic
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from algorithms.greedy import Greedy
from algorithms.ilp import ILP
from algorithms.random import Random
from algorithms.weekly import Weekly
from algorithms.tabu import Tabu
from framework.reader import ConstraintParser
from framework.evaluate import Evaluate
import time
import json
import datetime
import pprint
import os 
import re
import copy
from json2html import *
import webbrowser

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

def see_output2(out, period_info):
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
    num_weeks = 8
    # First week num
    html_original = html_original.replace('NUMWEEK','0')
    # From second week onwards
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
    day = period_info['StartDate']
    aux = 0
    #Insert values from json
    while day < period_info['EndDate']:
    #for day in fixed_out:
        if str(day.date()) in fixed_out:
            for timeslot in fixed_out[str(day.date())]:
                for course in fixed_out[str(day.date())][timeslot]:
                    full_html = full_html.replace('_%s_%s_%s_COURSE_%s'%(aux,week,timeslot,course['ProgID']),course['CourseID'])
                    t = [int(i) for i in timeslot.split(':')]
                    lecture_time = day + datetime.timedelta(hours=t[0], minutes=t[1])
                    full_html = full_html.replace('_%s_%s_%s_ROOM_%s'%(aux,week,timeslot,course['ProgID']),course['RoomID'])#str(lecture_time))
                    #print('_%s_%s_COURSE_%s'%(week,timeslot,course['ProgID']))
        #increase day count
        if aux==7:
            week+=1
            aux=0
        else:
            aux+=1
            day = day + datetime.timedelta(days=1)
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

class GUI:
    inputFile = ''
    outputDir = ''

    def __init__(self, alg=None):
        if alg!=None:
            print('asdasdasd')
            self.generate(alg)
            return
        Form, Window = uic.loadUiType('./gui/quokkas.ui')

        app = QApplication([])
        window = Window()
        self.form = Form()
        self.form.setupUi(window)
        window.show()
        self.setup_buttons()
        app.exec_()

    def setup_buttons(self):
        self.form.pushButton.clicked.connect(self.generate)
        self.form.browseButtonInput.clicked.connect(self.browseFile)

    def generate(self, alg=None):
        #alg = str(self.form.algComboBox.currentText())
        if alg==None:
            selectedAlgorithm = self.form.algComboBox.currentIndex()
        else:
            selectedAlgorithm = alg
        print("Calling main")
        logFile = open(os.path.realpath('./Logs/log.txt'), "w")
        logFile.write('Starting scheduling algorithm\n')

        algorithms = [ILP(), Greedy(), Tabu(), Random(), Weekly()]
        x = algorithms[selectedAlgorithm]
        
        x.generate_timetable()
        eval = Evaluate(x.get_schedule())
        print(eval.get_score())
        pp = pprint.PrettyPrinter(depth=6)
        output = open(os.path.realpath('./InputOutput/out.json'), "w")
        #out = pp.pformat(x.get_schedule())
        out = json.dumps(x.get_schedule(), indent=4)
        output.write(out)
        out = x.get_schedule()

        #see_output(x.get_schedule())
        output.write(json.dumps(out, indent=4))
        see_output2(out, x.get_period_info())

    def refreshAll( self ):
        '''
        Updates the GUI
        '''
        self.form.inputLineEdit.setText(self.inputFile)
        self.form.outputLineEdit.setText(self.outputDir)

    def browseFile(self):
            ''' 
            Called when the user presses the Browse button for the input
            '''
            #print( "Browse button pressed" )
            
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            fileName, _ = QtWidgets.QFileDialog.getOpenFileName(
                            None,
                            "QFileDialog.getOpenFileName()",
                            "",
                            "Excel files (*.xlsx);;All Files (*)",
                            options=options)
            if fileName:
                print( "setting file name: " + fileName )
                self.inputFile = fileName
                self.refreshAll()