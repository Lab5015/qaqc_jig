#! /usr/bin/env python3
 
from typing import NamedTuple

import ROOT




def countBad(nBadSpe, nBadLO, nBadRes, nBadAsymm):
    nBadCount=0    
    for ch in range(16):
        if(nBadRes[ch] == 1 or nBadAsymm[ch]==1 or nBadLO[ch]>0 or nBadSpe[ch]>0):
            nBadCount+=1
    return nBadCount


def expand_range(rng):
    numbers = []
    for item in rng:
        if '-' in item:
            start, end = map(int, item.split('-'))   
            numbers.extend(range(start, end + 1))
        else:
            numbers.append(int(item))
    return sorted(numbers)


def GetMaxVar(graph):
    minVal = 999999.
    maxVal = -999999.
    for point in range(graph.GetN()):
        if graph.GetPointY(point) < minVal:
            minVal = graph.GetPointY(point)
        if graph.GetPointY(point) > maxVal:
            maxVal = graph.GetPointY(point)            
    return maxVal-minVal


def GetMeanRMS(graph):
    htemp = ROOT.TH1F('htemp','',100,-100.,10000)
    for point in range(graph.GetN()):
        #if graph.GetPointY(point) > 1000. and  graph.GetPointY(point) < 5000.:
        htemp.Fill(graph.GetPointY(point))
    return (htemp.GetMean(),htemp.GetRMS())


def GetMeanRMS_abs(graph):
    htemp = ROOT.TH1F('htemp','',100,-100.,10000)
    for point in range(graph.GetN()):
        #if graph.GetPointY(point) > 1000. and  graph.GetPointY(point) < 5000.:
        htemp.Fill(abs(graph.GetPointY(point)))
    return (htemp.GetMean(),htemp.GetRMS())


class ParamStruct(NamedTuple):
    inputFileName: str
    run: int
    meanLO: float
    meanAsymm: float
    minLO: float
    maxAsymm: float
    maxRes: float
    cat: str
