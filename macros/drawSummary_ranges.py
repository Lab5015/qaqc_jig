#! /usr/bin/env python3

import os
import shutil
import glob
import math
import array
import sys
import time

import ROOT
import tdrstyle

from collections import OrderedDict

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
MIN_LO_bar = 0.90 * 3150.
MIN_LO_ch = 0.85 * 3150.
MAX_LO_ASYMM_bar = 0.06
MIN_LO_ASYMM_ch = -0.15
MAX_LO_ASYMM_ch = 0.15
MAX_RES_bar = 0.06
NOT_TO_USE_SM = ['32110020000290','32110020000295','32110020000438','32110020000440','32110020000441','32110020000442','32110020000443','32110020000444','32110020000445','32110020000446','32110020000447','32110020000448','32110020000449','32110020000450','32110020000451']

modules_db = getListOfSensorModules.getListOfSensorModules(location=5380,
                                                           size = '1000',
                                                           parent = 'and s.PART_PARENT_ID = 1000',
                                                           minBarcodeFilter = '',
                                                           maxBarcodeFilter = '')

data_path = '/home/cmsdaq/DAQ/qaqc_jig/data/'
selections = []

#runs = ["11-13","30-32","34-34","36-36","38-38","40-40","46-46","49-58","61-63"]
#modules_acc = ["200-224"]
#plotDir = '/data/html/PRODUCTION/sumaryPlots_SMID_201to224/'

#runs = ["106-107"]
#modules_acc = ["225-248"]
#plotDir = '/data/html/PRODUCTION/sumaryPlots_SMID_225to248/'

#runs = ["11-13","30-32","34-34","36-36","38-38","40-40","46-46","49-58","61-63","106-107"]
#modules_acc = ["200-248"]
#plotDir = '/data/html/PRODUCTION_CALIB/sumaryPlots_SMID_201to248/'

runs = ["11-13","30-32","34-34","36-36","38-38","40-40","46-46","49-58","61-63","106-108","110-113", "115-117", "119-119", "127-132", "134-137", "139-141","157-157","159-167"]
modules_acc = ["200-9999"]
plotDir = '/data/html/PRODUCTION/sumaryPlots_SMID_201to9999/'

#runs = ["136-136"]
#modules_acc = ["440-451"]
#plotDir = '/data/html/PRODUCTION/sumaryPlots_SMID_440to451/'




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



nCatA = 0
nCatB = 0
nCatC = 0

params = OrderedDict()


# Create a list of all runs
list_runs = expand_range(runs)
list_modules = expand_range(modules_acc)
# add barcode
prefix = "32110020"
list_modules = ["{}{:06d}".format(prefix, int(mod)) for mod in list_modules]

# retrieving root files 
inputFiles = glob.glob(data_path+'/run*/*_analysis.root')
for inputFile in inputFiles:
    tokens = inputFile.split('/')
    run = ''
    for token in tokens:
        if 'module' in token:
            module = token[7:21] # SM ID
        if 'run' in token:
            run = int(token[3:]) # run number
    # saving in the dict only selected runs and modules
    if int(run) in list_runs and module in list_modules:
        #print("run ", run, "  module ", module)
        params[module] = [inputFile,run,-1.,-1.,-1.,-1.,-1.,'cat. A']

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

h_LO_avg_ch = ROOT.TH1F('h_LO_avg_ch','',100,1200.,5200.)
h_LO_L_ch = ROOT.TH1F('h_LO_L_ch','',100,1200.,5200.)
h_LO_R_ch = ROOT.TH1F('h_LO_R_ch','',100,1200.,5200.)
h_LO_asymm_ch = ROOT.TH1F('h_LO_asymm_ch','',100,-0.3,0.3)

h_LOrms_bar = ROOT.TH1F('h_LOrms_bar','',60,0.,30.)
h_LOrms_ch = ROOT.TH1F('h_LOrms_ch','',60,0.,30.)

h_LOmaxvar_bar = ROOT.TH1F('h_LOmaxvar_bar','',50,0.,100.)
h_LOmaxvar_ch = ROOT.TH1F('h_LOmaxvar_ch','',50,0.,100.)

h_peak_res_L_ch = ROOT.TH1F('h_peak_res_L_ch','',50,0.,25.)
h_peak_res_R_ch = ROOT.TH1F('h_peak_res_R_ch','',50,0.,25.)
h_peak_res_bar = ROOT.TH1F('h_peak_res_bar','',200,0.,20.)
h_peak_res_avg_bar = ROOT.TH1F('h_peak_res_avg_bar','',200,0.,20.)

g_LO_avg_vs_barcode = ROOT.TGraph()
g_LO_L_vs_barcode = ROOT.TGraph()
g_LO_R_vs_barcode = ROOT.TGraph()
g_LOasymm_avg_vs_barcode = ROOT.TGraph()


# selecting the modules to be included in the summary: accept 1 if included, 0 otherwise
sm_lo_dict = {}
modules = params.keys()
for module in sorted(modules):

    param = params[module]
    rootfile = ROOT.TFile(params[module][0],'READ')
    
    # acceptance
    isCatA = True
    isCatB = False
    isCatC = False
    nBadCh = 0
    
    minLO = 999999.
    maxAsymm = -999999.
    maxRes = -999999.
    
    # filling histos
    graph = rootfile.Get('g_spe_L_vs_bar')
    for point in range(graph.GetN()):
        h_spe_L_ch.Fill(graph.GetPointY(point))
        if graph.GetPointY(point) < MIN_SPE_ch or graph.GetPointY(point) > MAX_SPE_ch:
            #print("failing g_spe_L_vs_bar")
            isCatC = True
            isCatA = False
    
    graph = rootfile.Get('g_spe_R_vs_bar')
    for point in range(graph.GetN()):
        h_spe_R_ch.Fill(graph.GetPointY(point))
        if graph.GetPointY(point) < MIN_SPE_ch or graph.GetPointY(point) > MAX_SPE_ch:
            #print("failing g_spe_R_vs_bar")
            isCatC = True
            isCatA = False

    
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
    sm_lo_dict[module] = GetMeanRMS(graph)[0]
    h_LOrms_bar.Fill(GetMeanRMS(graph)[1]/GetMeanRMS(graph)[0]*100.)
    h_LOmaxvar_bar.Fill(GetMaxVar(graph)/GetMeanRMS(graph)[0]*100.)
    h_LO_avg_ch.Fill(graph.GetPointY(point))
    g_LO_avg_vs_barcode.SetPoint(g_LO_avg_vs_barcode.GetN(),int(module)-32110020000000,GetMeanRMS(graph)[0])
    param[2] = GetMeanRMS(graph)[0]
    if GetMeanRMS(graph)[0] < MIN_LO_bar:
        #print("failing g_avg_light_yield_vs_bar")
        isCatC = True
        isCatA = False
    for point in range(graph.GetN()):
        h_LO_avg_ch.Fill(graph.GetPointY(point))
        if graph.GetPointY(point) < MIN_LO_bar:
            #print("failing g_avg_light_yield_vs_ch")
            nBadCh += 1
    
    graph = rootfile.Get('g_light_yield_asymm_vs_bar')
    h_LO_asymm_bar.Fill(GetMeanRMS_abs(graph)[0])
    param[3] = GetMeanRMS_abs(graph)[0]
    g_LOasymm_avg_vs_barcode.SetPoint(g_LOasymm_avg_vs_barcode.GetN(),int(module)-32110020000000,GetMeanRMS_abs(graph)[0])
    #if GetMeanRMS_abs(graph)[0] > MAX_LO_ASYMM_bar:
    #    #print("failing g_light_yield_asymm_vs_bar")
    #    isCatB = True
    #    isCatA = False
    for point in range(graph.GetN()):
        h_LO_asymm_ch.Fill(graph.GetPointY(point))
        if abs(graph.GetPointY(point)) > maxAsymm:
            maxAsymm = abs(graph.GetPointY(point))
        #if graph.GetPointY(point) < MIN_LO_ASYMM_ch or graph.GetPointY(point) > MAX_LO_ASYMM_ch:
        #    #print("failing g_light_yield_asymm_vs_ch")
        #    isCatB = True
        #    isCatA = False
            
    graph = rootfile.Get('g_L_light_yield_vs_bar')
    h_LO_L_bar.Fill(GetMeanRMS(graph)[0])
    if GetMeanRMS(graph)[0] < MIN_LO_ch:
        #print("failing g_L_light_yield_vs_bar")
        isCatC = True
        isCatA = False
    for point in range(graph.GetN()):
        h_LO_L_ch.Fill(graph.GetPointY(point))
        if graph.GetPointY(point) < minLO:
            minLO = graph.GetPointY(point)
        if graph.GetPointY(point) < MIN_LO_ch:
            #print("failing g_L_light_yield_vs_ch")
            nBadCh += 1
    
    graph = rootfile.Get('g_R_light_yield_vs_bar')
    h_LO_R_bar.Fill(GetMeanRMS(graph)[0])
    if GetMeanRMS(graph)[0] < MIN_LO_ch:
        #print("failing g_R_light_yield_vs_bar")
        isCatC = True
        isCatA = False
    for point in range(graph.GetN()):
        h_LO_R_ch.Fill(graph.GetPointY(point))
        if graph.GetPointY(point) < minLO:
            minLO = graph.GetPointY(point)
        if graph.GetPointY(point) < MIN_LO_ch:
            #print("failing g_R_light_yield_vs_ch")
            nBadCh += 1
    
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
            isCatC = True
            isCatA = False
    
    graph = rootfile.Get('g_light_yield_vs_ch')
    h_LOrms_ch.Fill(GetMeanRMS(graph)[1]/GetMeanRMS(graph)[0]*100.)
    h_LOmaxvar_ch.Fill(GetMaxVar(graph)/GetMeanRMS(graph)[0]*100.)

    param[4] = minLO
    param[5] = maxAsymm
    param[6] = maxRes
    
    if isCatC == False:
        if nBadCh == 0:
            isCatA = True
        elif nBadCh < 2:
            isCatB = True
            isCatA = False
        else:
            isCatC = True
            isCatA = False
    
    if isCatA:
        nCatA += 1
    if isCatB:
        nCatB += 1
        param[7] = 'cat. B'
    if isCatC:
        nCatC += 1
        param[7] = 'cat. C'
    
    print("module %s   run %4d   mean LO: %4.0f   mean asymm: %6.3f   min LO: %4.0f   max asymm: %6.3f   peak res: %6.3f   %s"%(module,param[1],round(param[2],0),round(param[3],3),round(param[4],0),round(param[5],3),round(param[6],3),param[7]))

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')
print('--- --- --- --- --- --- --- PRINT SM LIST SORTED BY LO  --- --- --- --- --- ---')
print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')

sorted_lo_dict = sorted(sm_lo_dict.items(), key=lambda x:x[1], reverse=True)
for module in sorted_lo_dict:
    if module[0] in modules_db:
        print("barcode: %s --> LO = %.2f"%(module[0], module[1]))
    
#print(sorted_lo_dict)

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')

print('N cat. A = %4d (%4.1f%%)'%(nCatA,nCatA/(nCatA+nCatB+nCatC)*100.))
print('N cat. B = %4d (%4.1f%%)'%(nCatB,nCatB/(nCatA+nCatB+nCatC)*100.))
print('N cat. C = %4d (%4.1f%%)'%(nCatC,nCatC/(nCatA+nCatB+nCatC)*100.))

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')


print('cat. A modules to be used for DM, sorted by LO:')

modules = params.keys()
for module in sorted_lo_dict:
    if module[0] in modules_db: 
        param = params[module[0]]
        if 'cat. B' not in param and 'cat. C' not in param and module[0] not in NOT_TO_USE_SM:
            print("module %s   run %4d   mean LO: %4.0f   mean asymm: %6.3f   min LO: %4.0f   max asymm: %6.3f   %s"%(module[0],param[1],round(param[2],0),round(param[3],3),round(param[4],0),round(param[5],3),param[6]))

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')

print('cat. B modules:')

modules = params.keys()
for module in sorted(modules):
    param = params[module]
    if 'cat. B' in param:
        print("module %s   run %4d   mean LO: %4.0f   mean asymm: %6.3f   min LO: %4.0f   max asymm: %6.3f   %s"%(module,param[1],round(param[2],0),round(param[3],3),round(param[4],0),round(param[5],3),param[6]))

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')

print('cat. C modules:')

modules = params.keys()
for module in sorted(modules):
    param = params[module]
    if 'cat. C' in param:
        print("module %s   run %4d   mean LO: %4.0f   mean asymm: %6.3f   min LO: %4.0f   max asymm: %6.3f   %s"%(module,param[1],round(param[2],0),round(param[3],3),round(param[4],0),round(param[5],3),param[6]))

print('--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---')


# draw histos
latex_cat = ROOT.TLatex(0.18,0.85,'#splitline{cat. A: %d (%.1f%%)}{#splitline{cat. B: %d (%.1f%%)}{cat. C: %d (%.1f%%)}}'%(nCatA,100.*nCatA/(nCatA+nCatB+nCatC),nCatB,100.*nCatB/(nCatA+nCatB+nCatC),nCatC,100.*nCatC/(nCatA+nCatB+nCatC)))
latex_cat.SetNDC()
latex_cat.SetTextSize(0.05)



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
c.Print('%s/h_LO_avg_bar.png'%plotDir)

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
#line_high.Draw('same')
latex_cat.Draw('same')
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
#line_low.Draw('same')
line_high = ROOT.TLine(MAX_LO_ASYMM_ch,0.,MAX_LO_ASYMM_ch,1.05*h_LO_asymm_ch.GetMaximum())
line_high.SetLineColor(ROOT.kGreen+1)
line_high.SetLineWidth(4)
line_high.SetLineStyle(2)
#line_high.Draw('same')
latex_cat.Draw('same')
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
line.Draw('same')
latex_cat.Draw('same')
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
line.Draw('same')
latex_cat.Draw('same')
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
line.Draw('same')
latex_cat.Draw('same')
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
line.Draw('same')
latex_cat.Draw('same')
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
line_low = ROOT.TLine(MIN_SPE_ch,0.,MIN_SPE_ch,1.05*h_peak_res_L_ch.GetMaximum())
line_low.SetLineColor(ROOT.kGreen+1)
line_low.SetLineWidth(4)
line_low.SetLineStyle(2)
line_low.Draw('same')
line_high = ROOT.TLine(MAX_SPE_ch,0.,MAX_SPE_ch,1.05*h_peak_res_L_ch.GetMaximum())
line_high.SetLineColor(ROOT.kGreen+1)
line_high.SetLineWidth(4)
line_high.SetLineStyle(2)
line_high.Draw('same')
c.Print('%s/h_peakRes_LR_ch.png'%plotDir)

c = ROOT.TCanvas('c_peakRes_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_peak_res_bar.SetTitle(';peak resolution[%];entries')
h_peak_res_bar.SetFillStyle(3001)
h_peak_res_bar.SetFillColor(ROOT.kBlack)
h_peak_res_bar.Draw()
line = ROOT.TLine(MAX_RES_bar,0.,MAX_RES_bar,1.05*h_peak_res_bar.GetMaximum())
line.SetLineColor(ROOT.kGreen+1)
line.SetLineWidth(4)
line.SetLineStyle(2)
line.Draw('same')
latex = ROOT.TLatex(0.64,0.60,'#splitline{mean: %.2e}{RMS: %.1f %%}'%(h_peak_res_bar.GetMean(),h_peak_res_bar.GetRMS()/h_peak_res_bar.GetMean()*100.))
latex.SetNDC()
latex.SetTextSize(0.05)
latex.Draw('same')
latex_cat.Draw('same')
c.Print('%s/h_peak_res_bar.png'%plotDir)

c = ROOT.TCanvas('c_peakRes_avg_bar','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
ROOT.gPad.SetLogy()
h_peak_res_avg_bar.SetTitle(';avg. peak resolution[%];entries')
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
c.Print('%s/h_peak_res_avg_bar.png'%plotDir)



c = ROOT.TCanvas('c_LO_vs_barcode','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
g_LO_avg_vs_barcode.SetTitle(';barcode;avg. light output [p.e./MeV]')
g_LO_avg_vs_barcode.SetLineWidth(2)
g_LO_avg_vs_barcode.GetYaxis().SetRangeUser(3150*0.75,3150*1.15)
g_LO_avg_vs_barcode.Draw('AL')
fitFunc = ROOT.TF1('fitFunc','pol1',200.,9999.)
fitFunc.SetNpx(10000)
g_LO_avg_vs_barcode.Fit(fitFunc,'QNRS+')
fitFunc.SetLineColor(ROOT.kRed)
fitFunc.Draw('same')
c.Print('%s/g_LO_vs_barcode.png'%plotDir)

c = ROOT.TCanvas('c_LOasymm_vs_barcode','',800,700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
g_LOasymm_avg_vs_barcode.SetTitle(';barcode;avg. L.O. asymm.')
g_LOasymm_avg_vs_barcode.SetLineWidth(2)
g_LOasymm_avg_vs_barcode.GetYaxis().SetRangeUser(0.,0.2)
g_LOasymm_avg_vs_barcode.Draw('AL')
c.Print('%s/g_LOasymm_vs_barcode.png'%plotDir)
