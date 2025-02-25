#! /usr/bin/env python3
 
import os
import shutil
import glob
import math
import array
import sys
import time
import subprocess
import json

import ROOT
import tdrstyle

from collections import OrderedDict
from typing import NamedTuple

from btl_scripts import getListOfSensorModules

#set the tdr style
tdrstyle.setTDRStyle()
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFit(0)
ROOT.gStyle.SetTitleOffset(1.25,'Y')
ROOT.gErrorIgnoreLevel = ROOT.kWarning;
ROOT.gROOT.SetBatch(True)
#ROOT.gROOT.SetBatch(False)

MIN_SPE_ch = 3.4
MAX_SPE_ch = 4.4
MIN_LO_bar = 0.85 * 3150.
MIN_LO_ch = 0.80 * 3150.
MAX_LO_ASYMM_bar = 0.08
MIN_LO_ASYMM_ch = -0.2
MAX_LO_ASYMM_ch = 0.2
MAX_RES_bar = 0.06
NOT_TO_USE_SM = ['32110020000290','32110020000295','32110020000438','32110020000440','32110020000441','32110020000442','32110020000443','32110020000444','32110020000445','32110020000446','32110020000447','32110020000448','32110020000449','32110020000450','32110020000451']

modules_db = getListOfSensorModules.getListOfSensorModules(location=5380,
                                                           size = '1000',
                                                           parent = 'and s.PART_PARENT_ID = 1000',
                                                           minBarcodeFilter = '',
                                                           maxBarcodeFilter = '')

with open('/home/cmsdaq/Programs/mtddb/btl_scripts/SMdata.json', 'r') as infile:
    SMdata = json.load(infile)
with open('/home/cmsdaq/Programs/mtddb/btl_scripts/LYSOdata.json', 'r') as infile:
    LYSOdata = json.load(infile)
    
data_path = '/home/cmsdaq/DAQ/qaqc_jig/data/'
selections = []

#runs = ["11-13","30-32","34-34","36-36","38-38","40-40","46-46","49-58","61-63"]
#modules_acc = ["200-224"]
#plotDir = '/data/html/PRODUCTION/summaryPlots_SMID_201to224/'

#runs = ["106-107"]
#modules_acc = ["225-248"]
#plotDir = '/data/html/PRODUCTION/summaryPlots_SMID_225to248/'

#runs = ["11-13","30-32","34-34","36-36","38-38","40-40","46-46","49-58","61-63","106-107"]
#modules_acc = ["200-248"]
#plotDir = '/data/html/PRODUCTION_CALIB/summaryPlots_SMID_201to248/'

runs = ["11-13","30-32","34-34","36-36","38-38","40-40","46-46","49-58","61-63","106-108","110-113", "115-117", "119-119", "127-132", "134-137", "139-141","157-157","159-167","170-171","175-176","179-182","240-243","248-248","250-250","252-259","261-262","265-265","269-269","271-288","290-290","292-292"]
modules_acc = ["200-9999"]
plotDir = '/data/html/PRODUCTION_CALIB/summaryPlots_SMID_201to9999/'

### reference runs
#runs = ["136-136","186-186","289-289"]
#modules_acc = ["440-451"]
#plotDir = '/data/html/PRODUCTION/summaryPlots_SMID_440to451/'


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



nTot = 0
nCatA = 0
nCatB = 0
nCatC = 0
nCatD = 0
nCatLO1 = 0
nCatLO2 = 0
nCatLO3 = 0
nCatR1 = 0
nCatR2 = 0
nCatR3 = 0
nCatAS1 = 0
nCatAS2 = 0
nCatAS3 = 0


class ParamStruct(NamedTuple):                                                                                                                                                                                                                                                                                                                                             
    inputFileName: str
    run: int
    meanLO: float
    meanAsymm: float
    minLO: float
    maxAsymm: float
    maxRes: float
    cat: str

params = OrderedDict()

# Create a list of all runs
list_runs = expand_range(runs)
list_modules = expand_range(modules_acc)
# add barcode
prefix = "32110020"
list_modules = ["{}{:06d}".format(prefix, int(mod)) for mod in list_modules]

# retrieving root files 
modules = []
inputFiles = glob.glob(data_path+'/run*/*_analysis_calib.root')
for inputFile in inputFiles:
    tokens = inputFile.split('/')
    run = ''
    for token in tokens:
        if 'module' in token:
            module = token[7:21] # SM ID
        if 'run' in token:
            run = int(token[3:]) # run number
    if int(run) in list_runs and module in list_modules:
        modules.append((module,inputFile,int(run)))

if not os.path.isdir(plotDir):
    os.mkdir(plotDir)


# creating histos
h_spe_L_ch = ROOT.TH1F('h_spe_L_ch','',100,3.,5.)
h_spe_R_ch = ROOT.TH1F('h_spe_R_ch','',100,3.,5.)

h_charge_raw_L_ch = ROOT.TH1F('h_charge_raw_L_ch','',100,0.,5.)
h_charge_raw_R_ch = ROOT.TH1F('h_charge_raw_R_ch','',100,0.,5.)
h_charge_L_ch = ROOT.TH1F('h_charge_L_ch','',100,0.,5.)
h_charge_R_ch = ROOT.TH1F('h_charge_R_ch','',100,0.,5.)

h_LO_avg_bar = ROOT.TH1F('h_LO_avg_bar','',100,1200.,5200.)
h_LO_L_bar = ROOT.TH1F('h_LO_L_bar','',100,1200.,5200.)
h_LO_R_bar = ROOT.TH1F('h_LO_R_bar','',100,1200.,5200.)
h_LO_asymm_bar = ROOT.TH1F('h_LO_asymm_bar','',100,0,0.2)

h_FOM_bar = ROOT.TH1F('h_FOM_bar','',100,0.2,0.8)
h_LO_avg_ch = ROOT.TH1F('h_LO_avg_ch','',100,1200.,5200.)
h_LO_L_ch = ROOT.TH1F('h_LO_L_ch','',100,1200.,5200.)
h_LO_R_ch = ROOT.TH1F('h_LO_R_ch','',100,1200.,5200.)
h_LO_asymm_ch = ROOT.TH1F('h_LO_asymm_ch','',100,-0.4,0.4)

h_LOrms_bar = ROOT.TH1F('h_LOrms_bar','',50,0.,10.)
h_LOrms_ch = ROOT.TH1F('h_LOrms_ch','',80,0.,20.)

h_LOmaxvar_bar = ROOT.TH1F('h_LOmaxvar_bar','',60,0.,30.)
h_LOmaxvar_ch = ROOT.TH1F('h_LOmaxvar_ch','',50,0.,100.)

h_peak_res_L_ch = ROOT.TH1F('h_peak_res_L_ch','',50,0.,25.)
h_peak_res_R_ch = ROOT.TH1F('h_peak_res_R_ch','',50,0.,25.)
h_peak_res_bar = ROOT.TH1F('h_peak_res_bar','',100,2.,12.)
h_peak_res_avg_bar = ROOT.TH1F('h_peak_res_avg_bar','',120,2.,8.)

g_LO_avg_vs_barcode_all = ROOT.TGraph()
g_LO_avg_vs_barcode = {}
g_LOasymm_avg_vs_barcode = {}
g_peak_res_max_vs_barcode = {}
g_lyso_vs_barcode = {}
g_LO_avg_vs_lyso = {}
g_LOasymm_avg_vs_lyso = {}
g_peak_res_max_vs_lyso = {}
for batch in range(9):
    g_LO_avg_vs_barcode[batch] = ROOT.TGraph()
    g_LOasymm_avg_vs_barcode[batch] = ROOT.TGraph()
    g_peak_res_max_vs_barcode[batch] = ROOT.TGraph()
    g_lyso_vs_barcode[batch] = ROOT.TGraph()
    g_LO_avg_vs_lyso[batch] = ROOT.TGraph()
    g_LOasymm_avg_vs_lyso[batch] = ROOT.TGraph()
    g_peak_res_max_vs_lyso[batch] = ROOT.TGraph()




# selecting the modules to be included in the summary: accept 1 if included, 0 otherwise
sm_lo_dict = {}
barcodeMin = 9999
barcodeMax = -9999
for module in sorted(modules):

    if (int(module[0])-32110020000000) > barcodeMax:
        barcodeMax = int(module[0])-32110020000000
    if (int(module[0])-32110020000000) < barcodeMin:
        barcodeMin = int(module[0])-32110020000000
    
    rootfile = ROOT.TFile(module[1],'READ')
    LYSObarcode = 32110000000000
    batchStr = ''
    batch = -1
    ingot = ''
    if module[0] in SMdata.keys():
        LYSObarcode = int(SMdata[module[0]]['LYSO']) 
        batchStr = LYSOdata[str(LYSObarcode)]['batch']
        batch = int(batchStr[5:6])-1
        ingot = LYSOdata[str(LYSObarcode)]['ingot']
    
    # acceptance
    isCatA = True
    isCatB = False
    isCatC = False
    isCatD = False
    isCatLO1 = False
    isCatLO2 = False
    isCatLO3 = False    
    isCatR1 = False
    isCatR2 = False
    isCatR3 = False    
    isCatAS1 = False
    isCatAS2 = False
    isCatAS3 = False    
    nBadSpe = {}
    nBadLO = {}
    nBadRes = {}
    nBadAsymm = {}
    
    for ch in range(16):
        nBadSpe[ch]=0
        nBadLO[ch]=0
        nBadRes[ch]=0
        nBadAsymm[ch]=0
    
    
    minLO = 999999.
    maxAsymm = -999999.
    maxRes = -999999.
    
    # filling histos
    graph = rootfile.Get('g_spe_L_vs_bar')
    for point in range(graph.GetN()):
        h_spe_L_ch.Fill(graph.GetPointY(point))
        if graph.GetPointY(point) < MIN_SPE_ch or graph.GetPointY(point) > MAX_SPE_ch:
            nBadSpe[point] += 1
    
    graph = rootfile.Get('g_spe_R_vs_bar')
    for point in range(graph.GetN()):
        h_spe_R_ch.Fill(graph.GetPointY(point))
        if graph.GetPointY(point) < MIN_SPE_ch or graph.GetPointY(point) > MAX_SPE_ch:
            nBadSpe[point] += 1
    
    graph = rootfile.Get('g_lyso_L_pc_per_kev_raw_vs_bar')
    for point in range(graph.GetN()):
        h_charge_raw_L_ch.Fill(graph.GetPointY(point))
    graph = rootfile.Get('g_lyso_R_pc_per_kev_raw_vs_bar')
    for point in range(graph.GetN()):
        h_charge_raw_R_ch.Fill(graph.GetPointY(point))

    graph = rootfile.Get('g_lyso_L_pc_per_kev_vs_bar')
    for point in range(graph.GetN()):
        h_charge_L_ch.Fill(graph.GetPointY(point))
        
    graph = rootfile.Get('g_lyso_R_pc_per_kev_vs_bar')
    for point in range(graph.GetN()):
        h_charge_R_ch.Fill(graph.GetPointY(point))
    
    graph = rootfile.Get('g_avg_light_yield_vs_bar')
    h_LO_avg_bar.Fill(GetMeanRMS(graph)[0])
    h_LOrms_bar.Fill(GetMeanRMS(graph)[1]/GetMeanRMS(graph)[0]*100.)
    h_LOmaxvar_bar.Fill(GetMaxVar(graph)/GetMeanRMS(graph)[0]*100.)
    h_LO_avg_ch.Fill(graph.GetPointY(point))
    g_LO_avg_vs_barcode_all.SetPoint(g_LO_avg_vs_barcode_all.GetN(),int(module[0])-32110020000000,GetMeanRMS(graph)[0])
    if batch != -1:
        g_LO_avg_vs_barcode[batch].SetPoint(g_LO_avg_vs_barcode[batch].GetN(),int(module[0])-32110020000000,GetMeanRMS(graph)[0])
        g_LO_avg_vs_lyso[batch].SetPoint(g_LO_avg_vs_lyso[batch].GetN(),LYSObarcode-32110000000000,GetMeanRMS(graph)[0])    
    meanLO = GetMeanRMS(graph)[0]
    if GetMeanRMS(graph)[0] < MIN_LO_bar:
        isCatD = True
        isCatA = False
    for point in range(graph.GetN()):
        h_LO_avg_ch.Fill(graph.GetPointY(point))
    
    graph = rootfile.Get('g_light_yield_asymm_vs_bar')
    h_LO_asymm_bar.Fill(GetMeanRMS_abs(graph)[0])
    meanAsymm = GetMeanRMS_abs(graph)[0]
    if batch != -1:
        g_LOasymm_avg_vs_barcode[batch].SetPoint(g_LOasymm_avg_vs_barcode[batch].GetN(),int(module[0])-32110020000000,GetMeanRMS_abs(graph)[0])
    if GetMeanRMS_abs(graph)[0] > MAX_LO_ASYMM_bar:
        isCatD=True
        isCatA=False
    for point in range(graph.GetN()):
        h_LO_asymm_ch.Fill(graph.GetPointY(point))
        if abs(graph.GetPointY(point)) > maxAsymm:
            maxAsymm = abs(graph.GetPointY(point))
        if graph.GetPointY(point) < MIN_LO_ASYMM_ch or graph.GetPointY(point) > MAX_LO_ASYMM_ch:
            nBadAsymm[point]+=1
            
    graph = rootfile.Get('g_L_light_yield_vs_bar')
    h_LO_L_bar.Fill(GetMeanRMS(graph)[0])
    for point in range(graph.GetN()):
        h_LO_L_ch.Fill(graph.GetPointY(point))
        if graph.GetPointY(point) < minLO:
            minLO = graph.GetPointY(point)
        if graph.GetPointY(point) < MIN_LO_ch:
            nBadLO[point] += 1
    
    graph = rootfile.Get('g_R_light_yield_vs_bar')
    h_LO_R_bar.Fill(GetMeanRMS(graph)[0])
    for point in range(graph.GetN()):
        h_LO_R_ch.Fill(graph.GetPointY(point))
        if graph.GetPointY(point) < minLO:
            minLO = graph.GetPointY(point)
        if graph.GetPointY(point) < MIN_LO_ch:
            nBadLO[point] += 1
    
    graphL = rootfile.Get('g_L_light_yield_vs_bar')
    graphR = rootfile.Get('g_R_light_yield_vs_bar')                
    for point in range(graphL.GetN()):
        LO_L = graphL.GetPointY(point)
        LO_R = graphR.GetPointY(point)        
        alpha = -0.7
        FOM = 100*math.sqrt(pow(abs(LO_L), 2*alpha) + pow(abs(LO_R), 2*alpha))
        h_FOM_bar.Fill(FOM)
    
    graph = rootfile.Get('g_lyso_L_peak_res_vs_bar')
    for point in range(graph.GetN()):
        h_peak_res_L_ch.Fill(100.*graph.GetPointY(point))
    graph = rootfile.Get('g_lyso_R_peak_res_vs_bar')
    for point in range(graph.GetN()):
        h_peak_res_R_ch.Fill(100.*graph.GetPointY(point))
    graph = rootfile.Get('g_avg_lyso_res_vs_bar')
    h_peak_res_avg_bar.Fill(100.*GetMeanRMS(graph)[0])
    for point in range(graph.GetN()):
        if graph.GetPointY(point) > maxRes:
            maxRes = graph.GetPointY(point)
        h_peak_res_bar.Fill(100.*graph.GetPointY(point))
        if graph.GetPointY(point) > MAX_RES_bar:
            nBadRes[point] += 1
    
    if batch != -1:
        g_peak_res_max_vs_barcode[batch].SetPoint(g_peak_res_max_vs_barcode[batch].GetN(),int(module[0])-32110020000000,maxRes)
        
    graph = rootfile.Get('g_light_yield_vs_ch')
    h_LOrms_ch.Fill(GetMeanRMS(graph)[1]/GetMeanRMS(graph)[0]*100.)
    h_LOmaxvar_ch.Fill(GetMaxVar(graph)/GetMeanRMS(graph)[0]*100.)

    if batch != -1:
        g_peak_res_max_vs_lyso[batch].SetPoint(g_peak_res_max_vs_lyso[batch].GetN(),LYSObarcode-32110000000000,maxRes)
        g_lyso_vs_barcode[batch].SetPoint(g_lyso_vs_barcode[batch].GetN(),int(module[0])-32110020000000,LYSObarcode-32110000000000)
     
    if isCatD == False:
        if (countBad(nBadSpe,nBadLO,nBadRes,nBadAsymm)) == 0:
            isCatA = True
        elif (countBad(nBadSpe,nBadLO,nBadRes,nBadAsymm)) == 1:
            isCatB = True
            isCatA = False
        elif (countBad(nBadSpe,nBadLO,nBadRes,nBadAsymm)) == 2:
            isCatC = True
            isCatA = False
        else:
            isCatD = True
            isCatA = False
    
    if sum(nBadLO.values()) == 1:
        isCatLO1 = True
    elif sum(nBadLO.values()) == 2: 
        isCatLO2 = True
    elif sum(nBadLO.values()) > 2: 
        isCatLO3 = True

    if sum(nBadRes.values()) == 1:
        isCatR1 = True
    elif sum(nBadRes.values()) == 2: 
        isCatR2 = True
    elif sum(nBadRes.values()) > 2: 
        isCatR3 = True

    if sum(nBadAsymm.values()) == 1:
        isCatAS1 = True
    elif sum(nBadAsymm.values()) == 2: 
        isCatAS2 = True
    elif sum(nBadAsymm.values()) > 2: 
        isCatAS3 = True

    nTot += 1
    cat = 'n.a.'  
    if isCatA:
        nCatA += 1
        cat = 'A'
    if isCatB:
        nCatB += 1
        cat = 'B'
    if isCatC:
        nCatC += 1
        cat = 'C'
    if isCatD:
        nCatD += 1
        cat = 'D'

    if isCatLO1:
        nCatLO1 += 1
    if isCatLO2:
        nCatLO2 += 1
    if isCatLO3:
        nCatLO3 += 1        
    
    if isCatR1:
        nCatR1 += 1
    if isCatR2:
        nCatR2 += 1
    if isCatR3:
        nCatR3 += 1
    
    if isCatAS1:
        nCatAS1 += 1
    if isCatAS2:
        nCatAS2 += 1
    if isCatAS3:
        nCatAS3 += 1

    if module[0] in params.keys():
        print('!!!!!!!!!!!!',params[module[0]])
    
    params[module[0]] = ParamStruct(
            inputFileName = module[1],
            run = module[2],
            meanLO = meanLO,
            meanAsymm = meanAsymm,
            minLO = minLO,
            maxAsymm = maxAsymm,
            maxRes = maxRes,
            cat = cat
        )
    param = params[module[0]]  
    print('module %s   run: %04d   mean LO: %4.0f   mean asymm: %6.3f   min LO: %4.0f   max asymm: %6.3f   peak res: %6.3f   cat: %s'%(module[0],param.run,round(param.meanLO,0),round(param.meanAsymm,3),round(param.minLO,0),round(param.maxAsymm,3),round(param.maxRes,3),param.cat))

nCatTot = nCatA + nCatB + nCatC + nCatD
print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')
print('N tot    = %4d'%(nTot))
print('N cat. A = %4d (%4.1f%%)'%(nCatA,nCatA/nCatTot*100.))
print('N cat. B = %4d (%4.1f%%)'%(nCatB,nCatB/nCatTot*100.))
print('N cat. C = %4d (%4.1f%%)'%(nCatC,nCatC/nCatTot*100.))
print('N cat. D = %4d (%4.1f%%)'%(nCatD,nCatD/nCatTot*100.))

summary_dict = {
    key: dict(zip(value._fields, value)) 
    for key, value in params.items()
}
with open('./SM_summary_dict.json', "w") as file:
    json.dump(summary_dict, file, indent=4)

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')

print('cat. A modules to be used for DM, sorted by LO:')
params = dict(sorted(params.items(), key=lambda x: x[1].meanLO, reverse=True))
for module in params.keys():
    if module in modules_db: 
        param = params[module]
        if param.cat == 'A' and module not in NOT_TO_USE_SM:
            print('module %s   mean LO: %4.0f   cat: %s'%(module,round(param.meanLO,0),param.cat))

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')

print('cat. B modules to be used for DM, sorted by LO:')
params = dict(sorted(params.items(), key=lambda x: x[1].meanLO, reverse=True))
for module in params.keys():
    if module in modules_db: 
        param = params[module]
        if param.cat == 'B' and module not in NOT_TO_USE_SM:
            print('module %s   mean LO: %4.0f   cat: %s'%(module,round(param.meanLO,0),param.cat))

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')

print('cat. C modules to be used for DM, sorted by LO:')
params = dict(sorted(params.items(), key=lambda x: x[1].meanLO, reverse=True))
for module in params.keys():
    if module in modules_db: 
        param = params[module]
        if param.cat == 'C' and module not in NOT_TO_USE_SM:
            print('module %s   mean LO: %4.0f   cat: %s'%(module,round(param.meanLO,0),param.cat))

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')

print('cat. D modules:')

params = dict(sorted(params.items()))
for module in params.keys():
    if module in modules_db: 
        param = params[module]
        if param.cat == 'D' and module not in NOT_TO_USE_SM:
            LYSObarcode = 32110000000000
            batchStr = ''
            batch = -1
            ingot = ''
            if module in SMdata.keys():
                LYSObarcode = int(SMdata[module]['LYSO']) 
                batchStr = LYSOdata[str(LYSObarcode)]['batch']
                batch = int(batchStr[5:6])-1
                ingot = LYSOdata[str(LYSObarcode)]['ingot']
            print('module %s   run: %04d   mean LO: %4.0f   mean asymm: %6.3f   min LO: %4.0f   max asymm: %6.3f   peak res: %6.3f   cat: %s   batch: %d   ingot: %s'%(module,param.run,round(param.meanLO,0),round(param.meanAsymm,3),round(param.minLO,0),round(param.maxAsymm,3),round(param.maxRes,3),param.cat,batch,ingot))

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')




# draw histos
latex_cat = ROOT.TLatex(0.18,0.85,'#splitline{cat. A: %d (%.1f%%)}{#splitline{cat. B: %d (%.1f%%)}{#splitline{cat. C: %d (%.1f%%)}{cat. D: %d (%.1f%%)}}}'%(nCatA,100.*nCatA/nCatTot,nCatB,100.*nCatB/nCatTot,nCatC,100.*nCatC/nCatTot, nCatD, 100.*nCatD/nCatTot))
latex_cat.SetNDC()
latex_cat.SetTextSize(0.05)

latex_catLO = ROOT.TLatex(0.18,0.60,'#splitline{cat. LO1: %d (%.1f%%)}{#splitline{cat. LO2: %d (%.1f%%)}{cat. LO3: %d (%.1f%%)}}'%(nCatLO1,100.*nCatLO1/nCatTot,nCatLO2,100.*nCatLO2/nCatTot,nCatLO3,100.*nCatLO3/nCatTot))
latex_catLO.SetNDC()
latex_catLO.SetTextSize(0.04)

latex_catRes = ROOT.TLatex(0.18,0.45,'#splitline{cat. R1: %d (%.1f%%)}{#splitline{cat. R2: %d (%.1f%%)}{cat. R3: %d (%.1f%%)}}'%(nCatR1,100.*nCatR1/nCatTot,nCatR2,100.*nCatR2/nCatTot,nCatR3,100.*nCatR3/nCatTot))
latex_catRes.SetNDC()
latex_catRes.SetTextSize(0.04)

latex_catAs = ROOT.TLatex(0.18,0.30,'#splitline{cat. AS1: %d (%.1f%%)}{#splitline{cat. AS2: %d (%.1f%%)}{cat. AS3: %d (%.1f%%)}}'%(nCatAS1,100.*nCatAS1/nCatTot,nCatAS2,100.*nCatAS2/nCatTot,nCatAS3,100.*nCatAS3/nCatTot))
latex_catAs.SetNDC()
latex_catAs.SetTextSize(0.04)


c = ROOT.TCanvas('c_spe_LR_ch','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_spe_L_ch.SetTitle(';single p.e. charge [pC];entries')
h_spe_L_ch.SetFillStyle(3001)
h_spe_L_ch.SetFillColor(ROOT.kRed)
h_spe_L_ch.SetLineColor(ROOT.kRed)
h_spe_L_ch.GetYaxis().SetRangeUser(0.5,1.1*max(h_spe_L_ch.GetMaximum(),h_spe_R_ch.GetMaximum()))
h_spe_L_ch.Draw()
latex_L = ROOT.TLatex(0.64,0.70,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_spe_L_ch.GetMean(),h_spe_L_ch.GetRMS()/h_spe_L_ch.GetMean()*100.))
latex_L.SetNDC()
latex_L.SetTextSize(0.05)
latex_L.SetTextColor(ROOT.kRed)
latex_L.Draw('same')
h_spe_R_ch.SetFillStyle(3001)
h_spe_R_ch.SetFillColor(ROOT.kBlue)
h_spe_R_ch.SetLineColor(ROOT.kBlue)
h_spe_R_ch.Draw('same')
latex_R = ROOT.TLatex(0.64,0.40,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_spe_R_ch.GetMean(),h_spe_R_ch.GetRMS()/h_spe_R_ch.GetMean()*100.))
latex_R.SetNDC()
latex_R.SetTextSize(0.05)
latex_R.SetTextColor(ROOT.kBlue)
latex_R.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
line_low = ROOT.TLine(MIN_SPE_ch,0.,MIN_SPE_ch,1.05*h_spe_L_ch.GetMaximum())
line_low.SetLineColor(ROOT.kGreen+1)
line_low.SetLineWidth(4)
line_low.SetLineStyle(2)
line_low.Draw('same')
line_high = ROOT.TLine(MAX_SPE_ch,0.,MAX_SPE_ch,1.05*h_spe_L_ch.GetMaximum())
line_high.SetLineColor(ROOT.kGreen+1)
line_high.SetLineWidth(4)
line_high.SetLineStyle(2)
line_high.Draw('same')
c.Print('%s/h_spe_LR_ch.png'%plotDir)




c = ROOT.TCanvas('c_charge_raw_LR_ch','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_charge_raw_L_ch.SetTitle(';raw integrated charge [pC/keV];entries')
h_charge_raw_L_ch.SetFillStyle(3001)
h_charge_raw_L_ch.SetFillColor(ROOT.kRed)
h_charge_raw_L_ch.SetLineColor(ROOT.kRed)
h_charge_raw_L_ch.GetYaxis().SetRangeUser(0.5,1.1*max(h_charge_raw_L_ch.GetMaximum(),h_charge_raw_R_ch.GetMaximum()))
h_charge_raw_L_ch.Draw()
latex_L = ROOT.TLatex(0.64,0.70,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_charge_raw_L_ch.GetMean(),h_charge_raw_L_ch.GetRMS()/h_charge_raw_L_ch.GetMean()*100.))
latex_L.SetNDC()
latex_L.SetTextSize(0.05)
latex_L.SetTextColor(ROOT.kRed)
latex_L.Draw('same')
h_charge_raw_R_ch.SetFillStyle(3001)
h_charge_raw_R_ch.SetFillColor(ROOT.kBlue)
h_charge_raw_R_ch.SetLineColor(ROOT.kBlue)
h_charge_raw_R_ch.Draw('same')
latex_R = ROOT.TLatex(0.64,0.40,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_charge_raw_R_ch.GetMean(),h_charge_raw_R_ch.GetRMS()/h_charge_raw_R_ch.GetMean()*100.))
latex_R.SetNDC()
latex_R.SetTextSize(0.05)
latex_R.SetTextColor(ROOT.kBlue)
latex_R.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_charge_raw_LR_ch.png'%plotDir)




c = ROOT.TCanvas('c_charge_LR_ch','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_charge_L_ch.SetTitle(';integrated charge [pC/keV];entries')
h_charge_L_ch.SetFillStyle(3001)
h_charge_L_ch.SetFillColor(ROOT.kRed)
h_charge_L_ch.SetLineColor(ROOT.kRed)
h_charge_L_ch.GetYaxis().SetRangeUser(0.5,1.1*max(h_charge_L_ch.GetMaximum(),h_charge_R_ch.GetMaximum()))
h_charge_L_ch.Draw()
latex_L = ROOT.TLatex(0.64,0.70,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_charge_L_ch.GetMean(),h_charge_L_ch.GetRMS()/h_charge_L_ch.GetMean()*100.))
latex_L.SetNDC()
latex_L.SetTextSize(0.05)
latex_L.SetTextColor(ROOT.kRed)
latex_L.Draw('same')
h_charge_R_ch.SetFillStyle(3001)
h_charge_R_ch.SetFillColor(ROOT.kBlue)
h_charge_R_ch.SetLineColor(ROOT.kBlue)
h_charge_R_ch.Draw('same')
latex_R = ROOT.TLatex(0.64,0.40,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_charge_R_ch.GetMean(),h_charge_R_ch.GetRMS()/h_charge_R_ch.GetMean()*100.))
latex_R.SetNDC()
latex_R.SetTextSize(0.05)
latex_R.SetTextColor(ROOT.kBlue)
latex_R.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_charge_LR_ch.png'%plotDir)




c = ROOT.TCanvas('c_LO_avg_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LO_avg_bar.SetTitle(';avg. bar light output [pe/MeV];entries')
h_LO_avg_bar.SetFillStyle(3001)
h_LO_avg_bar.SetFillColor(ROOT.kBlack)
h_LO_avg_bar.Draw()
latex = ROOT.TLatex(0.64,0.60,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_LO_avg_bar.GetMean(),h_LO_avg_bar.GetRMS()/h_LO_avg_bar.GetMean()*100.))
latex.SetNDC()
latex.SetTextSize(0.05)
latex.Draw('same') 
line_low = ROOT.TLine(MIN_LO_bar,0.,MIN_LO_bar,1.05*h_LO_avg_bar.GetMaximum())
line_low.SetLineColor(ROOT.kGreen+1)
line_low.SetLineWidth(4)
line_low.SetLineStyle(2)
line_low.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LO_avg_bar.png'%plotDir)

c = ROOT.TCanvas('c_FOM_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_FOM_bar.SetTitle(';bar LO FOM;entries')
h_FOM_bar.SetFillStyle(3001)
h_FOM_bar.SetFillColor(ROOT.kBlack)
h_FOM_bar.Draw()
latex = ROOT.TLatex(0.64,0.60,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_FOM_bar.GetMean(),h_FOM_bar.GetRMS()/h_FOM_bar.GetMean()*100.))
latex.SetNDC()
latex.SetTextSize(0.05)
latex.Draw('same') 
line_low = ROOT.TLine(0.58,0.,0.58,1.05*h_FOM_bar.GetMaximum())
line_low.SetLineColor(ROOT.kGreen+1)
line_low.SetLineWidth(4)
line_low.SetLineStyle(2)
line_low.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
latex_catAs.Draw('same')
c.Print('%s/h_FOM_bar.png'%plotDir)


c = ROOT.TCanvas('c_LO_avg_ch','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LO_avg_ch.SetTitle(';bar light output [pe/MeV];entries')
h_LO_avg_ch.SetFillStyle(3001)
h_LO_avg_ch.SetFillColor(ROOT.kBlack)
h_LO_avg_ch.Draw()
latex = ROOT.TLatex(0.64,0.60,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_LO_avg_ch.GetMean(),h_LO_avg_ch.GetRMS()/h_LO_avg_ch.GetMean()*100.))
latex.SetNDC()
latex.SetTextSize(0.05)
latex.Draw('same')
line_low = ROOT.TLine(MIN_LO_bar,0.,MIN_LO_bar,1.05*h_LO_avg_ch.GetMaximum())
line_low.SetLineColor(ROOT.kGreen+1)
line_low.SetLineWidth(4)
line_low.SetLineStyle(2)
line_low.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LO_avg_ch.png'%plotDir)




c = ROOT.TCanvas('c_LO_LR_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LO_L_bar.SetTitle(';avg. channel light output [pe/MeV];entries')
h_LO_L_bar.SetFillStyle(3001)
h_LO_L_bar.SetFillColor(ROOT.kRed)
h_LO_L_bar.SetLineColor(ROOT.kRed)
h_LO_L_bar.GetYaxis().SetRangeUser(0.5,1.1*max(h_LO_L_bar.GetMaximum(),h_LO_R_bar.GetMaximum()))
h_LO_L_bar.Draw()
latex_L = ROOT.TLatex(0.64,0.70,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_LO_L_bar.GetMean(),h_LO_L_bar.GetRMS()/h_LO_L_bar.GetMean()*100.))
latex_L.SetNDC()
latex_L.SetTextSize(0.05)
latex_L.SetTextColor(ROOT.kRed)
latex_L.Draw('same')
h_LO_R_bar.SetFillStyle(3001)
h_LO_R_bar.SetFillColor(ROOT.kBlue)
h_LO_R_bar.SetLineColor(ROOT.kBlue)
h_LO_R_bar.Draw('same')
latex_R = ROOT.TLatex(0.64,0.40,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_LO_R_bar.GetMean(),h_LO_R_bar.GetRMS()/h_LO_R_bar.GetMean()*100.))
latex_R.SetNDC()
latex_R.SetTextSize(0.05)
latex_R.SetTextColor(ROOT.kBlue)
latex_R.Draw('same')
line_low = ROOT.TLine(MIN_LO_ch,0.,MIN_LO_ch,1.*max(h_LO_L_bar.GetMaximum(),h_LO_R_bar.GetMaximum()))
line_low.SetLineColor(ROOT.kGreen+1)
line_low.SetLineWidth(4)
line_low.SetLineStyle(2)
line_low.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LO_LR_bar.png'%plotDir)

c = ROOT.TCanvas('c_LO_LR_ch','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LO_L_ch.SetTitle(';channel light output [pe/MeV];entries')
h_LO_L_ch.SetFillStyle(3001)
h_LO_L_ch.SetFillColor(ROOT.kRed)
h_LO_L_ch.SetLineColor(ROOT.kRed)
h_LO_L_ch.GetYaxis().SetRangeUser(0.5,1.1*max(h_LO_L_ch.GetMaximum(),h_LO_R_ch.GetMaximum()))
h_LO_L_ch.Draw()
latex_L = ROOT.TLatex(0.64,0.70,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_LO_L_ch.GetMean(),h_LO_L_ch.GetRMS()/h_LO_L_ch.GetMean()*100.))
latex_L.SetNDC()
latex_L.SetTextSize(0.05)
latex_L.SetTextColor(ROOT.kRed)
latex_L.Draw('same')
h_LO_R_ch.SetFillStyle(3001)
h_LO_R_ch.SetFillColor(ROOT.kBlue)
h_LO_R_ch.SetLineColor(ROOT.kBlue)
h_LO_R_ch.Draw('same')
latex_R = ROOT.TLatex(0.64,0.40,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_LO_R_ch.GetMean(),h_LO_R_ch.GetRMS()/h_LO_R_ch.GetMean()*100.))
latex_R.SetNDC()
latex_R.SetTextSize(0.05)
latex_R.SetTextColor(ROOT.kBlue)
latex_R.Draw('same')
line_low = ROOT.TLine(MIN_LO_ch,0.,MIN_LO_ch,1.*max(h_LO_L_ch.GetMaximum(),h_LO_R_ch.GetMaximum()))
line_low.SetLineColor(ROOT.kGreen+1)
line_low.SetLineWidth(4)
line_low.SetLineStyle(2)
line_low.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LO_LR_ch.png'%plotDir)




c = ROOT.TCanvas('c_LO_asymm_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LO_asymm_bar.SetTitle(';avg. L.O. asymmetry [ 2*(L-R)/(L+R) ];entries')
h_LO_asymm_bar.SetFillStyle(3001)
h_LO_asymm_bar.SetFillColor(ROOT.kBlack)
h_LO_asymm_bar.Draw()
latex = ROOT.TLatex(0.64,0.60,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_LO_asymm_bar.GetMean(),h_LO_asymm_bar.GetRMS()*100.))
latex.SetNDC()
latex.SetTextSize(0.05)
latex.Draw('same') 
line_high = ROOT.TLine(MAX_LO_ASYMM_bar,0.,MAX_LO_ASYMM_bar,1.05*h_LO_asymm_bar.GetMaximum())
line_high.SetLineColor(ROOT.kGreen+1)
line_high.SetLineWidth(4)
line_high.SetLineStyle(2)
line_high.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LO_asymm_bar.png'%plotDir)

c = ROOT.TCanvas('c_LO_asymm_ch','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LO_asymm_ch.SetTitle(';L.O. asymmetry [ 2*(L-R)/(L+R) ];entries')
h_LO_asymm_ch.SetFillStyle(3001)
h_LO_asymm_ch.SetFillColor(ROOT.kBlack)
h_LO_asymm_ch.Draw()
latex = ROOT.TLatex(0.64,0.60,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_LO_asymm_ch.GetMean(),h_LO_asymm_ch.GetRMS()*100.))
latex.SetNDC()
latex.SetTextSize(0.05)
latex.Draw('same') 
line_low = ROOT.TLine(MIN_LO_ASYMM_ch,0.,MIN_LO_ASYMM_ch,1.05*h_LO_asymm_ch.GetMaximum())
line_low.SetLineColor(ROOT.kGreen+1)
line_low.SetLineWidth(4)
line_low.SetLineStyle(2)
line_low.Draw('same')
line_high = ROOT.TLine(MAX_LO_ASYMM_ch,0.,MAX_LO_ASYMM_ch,1.05*h_LO_asymm_ch.GetMaximum())
line_high.SetLineColor(ROOT.kGreen+1)
line_high.SetLineWidth(4)
line_high.SetLineStyle(2)
line_high.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LO_asymm_ch.png'%plotDir)




c = ROOT.TCanvas('c_LOrms_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LOrms_bar.SetTitle(';bar RMS [%];entries')
h_LOrms_bar.SetFillStyle(3001)
h_LOrms_bar.SetFillColor(ROOT.kBlack)
h_LOrms_bar.Draw()
line = ROOT.TLine(5.,0.,5.,1.05*h_LOrms_bar.GetMaximum())
line.SetLineColor(ROOT.kGreen+1)
line.SetLineWidth(4)
line.SetLineStyle(2)
#line.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LOrms_bar.png'%plotDir)

c = ROOT.TCanvas('c_LOrms_ch','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LOrms_ch.SetTitle(';channel RMS [%];entries')
h_LOrms_ch.SetFillStyle(3001)
h_LOrms_ch.SetFillColor(ROOT.kBlack)
h_LOrms_ch.Draw()
line = ROOT.TLine(7.,0.,7.,1.05*h_LOrms_ch.GetMaximum())
line.SetLineColor(ROOT.kGreen+1)
line.SetLineWidth(4)
line.SetLineStyle(2)
#line.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LOrms_ch.png'%plotDir)



c = ROOT.TCanvas('c_LOmaxvar_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LOmaxvar_bar.SetTitle(';bar max. var. [%];entries')
h_LOmaxvar_bar.SetFillStyle(3001)
h_LOmaxvar_bar.SetFillColor(ROOT.kBlack)
h_LOmaxvar_bar.Draw()
line = ROOT.TLine(30.,0.,30.,1.05*h_LOmaxvar_bar.GetMaximum())
line.SetLineColor(ROOT.kGreen+1)
line.SetLineWidth(4)
line.SetLineStyle(2)
#line.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LOmaxvar_bar.png'%plotDir)

c = ROOT.TCanvas('c_LOmaxvar_ch','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_LOmaxvar_ch.SetTitle(';channel max. var. [%];entries')
h_LOmaxvar_ch.SetFillStyle(3001)
h_LOmaxvar_ch.SetFillColor(ROOT.kBlack)
h_LOmaxvar_ch.Draw()
line = ROOT.TLine(40.,0.,40.,1.05*h_LOmaxvar_ch.GetMaximum())
line.SetLineColor(ROOT.kGreen+1)
line.SetLineWidth(4)
line.SetLineStyle(2)
#line.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_LOmaxvar_ch.png'%plotDir)



c = ROOT.TCanvas('c_peakRes_LR_ch','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_peak_res_L_ch.SetTitle(';peak resolution;entries')
h_peak_res_L_ch.SetFillStyle(3001)
h_peak_res_L_ch.SetFillColor(ROOT.kRed)
h_peak_res_L_ch.SetLineColor(ROOT.kRed)
h_peak_res_L_ch.GetYaxis().SetRangeUser(0.5,1.1*max(h_peak_res_L_ch.GetMaximum(),h_peak_res_R_ch.GetMaximum()))
h_peak_res_L_ch.Draw()
latex_L = ROOT.TLatex(0.64,0.70,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_peak_res_L_ch.GetMean(),h_peak_res_L_ch.GetRMS()/h_peak_res_L_ch.GetMean()*100.))
latex_L.SetNDC()
latex_L.SetTextSize(0.05)
latex_L.SetTextColor(ROOT.kRed)
latex_L.Draw('same')
h_peak_res_R_ch.SetFillStyle(3001)
h_peak_res_R_ch.SetFillColor(ROOT.kBlue)
h_peak_res_R_ch.SetLineColor(ROOT.kBlue)
h_peak_res_R_ch.Draw('same')
latex_R = ROOT.TLatex(0.64,0.40,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_peak_res_R_ch.GetMean(),h_peak_res_R_ch.GetRMS()/h_peak_res_R_ch.GetMean()*100.))
latex_R.SetNDC()
latex_R.SetTextSize(0.05)
latex_R.SetTextColor(ROOT.kBlue)
latex_R.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_peakRes_LR_ch.png'%plotDir)

c = ROOT.TCanvas('c_peakRes_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_peak_res_bar.SetTitle(';peak resolution [%];entries')
h_peak_res_bar.SetFillStyle(3001)
h_peak_res_bar.SetFillColor(ROOT.kBlack)
h_peak_res_bar.Draw()
latex = ROOT.TLatex(0.64,0.60,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_peak_res_bar.GetMean(),h_peak_res_bar.GetRMS()/h_peak_res_bar.GetMean()*100.))
latex.SetNDC()
latex.SetTextSize(0.05)
latex.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
line_high = ROOT.TLine(MAX_RES_bar*100.,0.,MAX_RES_bar*100.,1.05*h_peak_res_bar.GetMaximum())
line_high.SetLineColor(ROOT.kGreen+1)
line_high.SetLineWidth(4)
line_high.SetLineStyle(2)
line_high.Draw('same')
c.Print('%s/h_peak_res_bar.png'%plotDir)

c = ROOT.TCanvas('c_peakRes_avg_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_peak_res_avg_bar.SetTitle(';avg. peak resolution [%];entries')
h_peak_res_avg_bar.SetFillStyle(3001)
h_peak_res_avg_bar.SetFillColor(ROOT.kBlack)
h_peak_res_avg_bar.Draw()
line = ROOT.TLine(MAX_RES_bar,0.,MAX_RES_bar,1.05*h_peak_res_avg_bar.GetMaximum())
line.SetLineColor(ROOT.kGreen+1)
line.SetLineWidth(4)
line.SetLineStyle(2)
line.Draw('same')
latex = ROOT.TLatex(0.64,0.60,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_peak_res_avg_bar.GetMean(),h_peak_res_avg_bar.GetRMS()/h_peak_res_avg_bar.GetMean()*100.))
latex.SetNDC()
latex.SetTextSize(0.05)
latex.Draw('same')
latex_cat.Draw('same')
latex_catLO.Draw('same')
latex_catRes.Draw('same')
c.Print('%s/h_peak_res_avg_bar.png'%plotDir)



c = ROOT.TCanvas('c_LO_vs_barcode','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hpad = ROOT.gPad.DrawFrame(barcodeMin-10,3150*0.75,barcodeMax+10,3150*1.15)
hpad.SetTitle(';SM barcode;avg. light output [p.e./MeV]')
hpad.Draw()
for batch in range(9):
    if g_LO_avg_vs_barcode[batch].GetN() == 0: continue
    g_LO_avg_vs_barcode[batch].SetLineColor(50+9*batch)
    g_LO_avg_vs_barcode[batch].SetMarkerColor(50+9*batch)
    g_LO_avg_vs_barcode[batch].SetMarkerStyle(20)
    g_LO_avg_vs_barcode[batch].SetMarkerSize(1.)
    g_LO_avg_vs_barcode[batch].Draw('P,same')
fitFunc = ROOT.TF1('fitFunc','pol1',0.,3000.)
fitFunc.SetNpx(10000)
g_LO_avg_vs_barcode_all.Fit(fitFunc,'QNRS+')
fitFunc.SetLineColor(ROOT.kBlack)
fitFunc.Draw('same')
c.Print('%s/g_LO_vs_barcode.png'%plotDir)


c = ROOT.TCanvas('c_LOasymm_vs_barcode','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hpad = ROOT.gPad.DrawFrame(barcodeMin-10,0.,barcodeMax+10,0.2)
hpad.SetTitle(';SM barcode;avg. L.O. asymm.')
hpad.Draw()
for batch in range(9):
    if g_LOasymm_avg_vs_barcode[batch].GetN() == 0: continue
    g_LOasymm_avg_vs_barcode[batch].SetLineColor(50+9*batch)
    g_LOasymm_avg_vs_barcode[batch].SetMarkerColor(50+9*batch)
    g_LOasymm_avg_vs_barcode[batch].SetMarkerStyle(20)
    g_LOasymm_avg_vs_barcode[batch].SetMarkerSize(1.)
    g_LOasymm_avg_vs_barcode[batch].Draw('P,same')
c.Print('%s/g_LOasymm_vs_barcode.png'%plotDir)

c = ROOT.TCanvas('c_peak_res_max_vs_barcode','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hpad = ROOT.gPad.DrawFrame(barcodeMin-10,0.03,barcodeMax+10,0.1)
hpad.SetTitle(';SM barcode;max. peak resolution')
hpad.Draw()
for batch in range(9):
    if g_peak_res_max_vs_barcode[batch].GetN() == 0: continue
    g_peak_res_max_vs_barcode[batch].SetLineColor(50+9*batch)
    g_peak_res_max_vs_barcode[batch].SetMarkerColor(50+9*batch)
    g_peak_res_max_vs_barcode[batch].SetMarkerStyle(20)
    g_peak_res_max_vs_barcode[batch].SetMarkerSize(1.)
    g_peak_res_max_vs_barcode[batch].Draw('P,same')
c.Print('%s/g_peak_res_max_vs_barcode.png'%plotDir)

c = ROOT.TCanvas('c_lyso_vs_barcode','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hpad = ROOT.gPad.DrawFrame(barcodeMin-10,100000.,barcodeMax+10,106000.)
hpad.SetTitle(';SM barcode;LYSO barcode')
hpad.Draw()
for batch in range(9):
    if g_lyso_vs_barcode[batch].GetN() == 0: continue
    g_lyso_vs_barcode[batch].SetLineColor(50+9*batch)
    g_lyso_vs_barcode[batch].SetMarkerColor(50+9*batch)
    g_lyso_vs_barcode[batch].SetMarkerStyle(20)
    g_lyso_vs_barcode[batch].SetMarkerSize(1.)
    g_lyso_vs_barcode[batch].Draw('P,same')
c.Print('%s/g_lyso_vs_barcode.png'%plotDir)



c = ROOT.TCanvas('c_LO_vs_lyso','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hpad = ROOT.gPad.DrawFrame(100000.,3150*0.75,106000.,3150*1.15)
hpad.SetTitle(';LYSO barcode;avg. light output [p.e./MeV]')
hpad.Draw()
for batch in range(9):
    g_LO_avg_vs_lyso[batch].SetLineColor(50+9*batch)
    g_LO_avg_vs_lyso[batch].SetMarkerColor(50+9*batch)
    g_LO_avg_vs_lyso[batch].SetMarkerStyle(20)
    g_LO_avg_vs_lyso[batch].SetMarkerSize(1.)
    g_LO_avg_vs_lyso[batch].Draw('P,same')
c.Print('%s/g_LO_vs_lyso.png'%plotDir)

c = ROOT.TCanvas('c_maxRes_vs_lyso','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hpad = ROOT.gPad.DrawFrame(100000.,0.03,106000.,0.1)
hpad.SetTitle(';LYSO barcode;max. peak resolution')
hpad.Draw()
for batch in range(9):
    g_peak_res_max_vs_lyso[batch].SetLineColor(50+9*batch)
    g_peak_res_max_vs_lyso[batch].SetMarkerColor(50+9*batch)
    g_peak_res_max_vs_lyso[batch].SetLineWidth(2)
    g_peak_res_max_vs_lyso[batch].Draw('P,same')
c.Print('%s/g_peak_res_max_vs_lyso.png'%plotDir)
