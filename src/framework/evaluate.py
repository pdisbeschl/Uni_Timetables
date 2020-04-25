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

class Evaluate:
    
    metrics_file_path = "./evaluation_metrics.json"

    def __init__(self):
        self.read_metrics()

    def read_metrics(self):
        with open(self.metrics_file_path,"r") as f:
            self.metrics = json.load(f)
        
        self.preferences = self.metrics["preferences"]
        print(self.preferences)



if __name__ == "__main__":
    Evaluate()