import os
import sys
from subprocess import Popen, PIPE

BAC = "Milano"

if BAC == "CERN":
    print()
    
if BAC == "Milano":
    sys.path.append('/home/cmsdaq/Programs/Lab5015Utils')
    #from Lab5015_utils import LAUDAChiller
    from Lab5015_utils import SMChiller


class Chiller:
    def __init__(self):
        if BAC == "Milano":
            #self.chiller = LAUDAChiller(portname='tcp://pc-mtd-mib01:5050')
            self.chiller = SMChiller(portname='tcp://pc-mtd-mib01:5050')
        if BAC == "CERN":
            print()
            
    def getState(self):
        if BAC == "Milano":
            state = self.chiller.check_state()
            return state
        if BAC == "CERN":
            print()
    
    def setState(self,state):
        if BAC == "Milano":
            self.chiller.set_state(state)
        if BAC == "CERN":
            print()

    def getWaterTemp(self):
        if BAC == "Milano":
            temp = self.chiller.read_meas_temp()
            return temp
        if BAC == "CERN":
            print()

    def setTemp(self,temp):
        if BAC == "Milano":
            self.chiller.write_set_temp(temp)
        if BAC == "CERN":
            print()
    
    def startPIDProcess(self, temp):
        if BAC == "Milano":
            proc = Popen(['nohup','python3','/home/cmsdaq/DAQ/qaqc_jig/python/utilities/setBoxTemp_PID.py','--target','%f'%temp,'&'])
            return proc
        if BAC == "CERN":
            print()

    def stopPIDProcess(self,pid):
        if BAC == "Milano":
            os.system('kill -9 %d'%pid)
            self.chiller.set_state('0')
        if BAC == "CERN":
            print()
            
