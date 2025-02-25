#! /usr/bin/python3

import os
import argparse
import json


def get_list(input_list):
    vals = []
    comma_list = input_list.split(',')
    for item in comma_list:
        hyphen_list = item.split('-')
        if len(hyphen_list) > 1:
            for i in range(int(hyphen_list[0]), int(hyphen_list[1])+1):
                vals.append(i)
        else:
            vals.append(int(hyphen_list[0]))
    return vals


parser = argparse.ArgumentParser(description='Launch reco')
parser.add_argument("-r", "--runs",   help="runs to reprocess", type=str, dest="runs", required=True)
parser.add_argument("-s", "--slot",   help="slots to reprocess", type=str, dest="slots", required=False)
parser.add_argument("-i", "--integration", help="integration task", action='store_true')
parser.add_argument("-a", "--analysis", help="analysis task", action='store_true')
parser.add_argument("--submit", help="submit jobs", action='store_true')
args = parser.parse_args()

runs_list = get_list(args.runs)
print('Runs to process', runs_list)

slots_list = [it for it in range(12)]
if args.slots:
    slots_list = get_list(args.slots)
print('Slots to process', slots_list)


path = '/home/cmsdaq/DAQ/qaqc_jig/data/'
sourceType = 'sodium'


for run in runs_list:
    jsonFileName = path+'run%04d/qaqc_gui.settings'%run
    config = json.load(open(jsonFileName))
    slot = 0
    for barcode in config['barcodes']:
        if config['module_available'][slot] == 1 and slot in slots_list:
            print('\n',barcode,slot)
            command = ''
            if args.integration:
                command = './python/integrate-waveforms -o %s/run%04d/module_%s_integrals.root %s/run%04d/module_%s.hdf5' % (path,run,barcode,path,run,barcode)
            if args.analysis:
                command = './python/analyze-waveforms --barcode '+str(barcode)+' --slot '+str(slot)+' --sourceType %s --print-pdfs \"/data/html/PRODUCTION_CALIB/\" -o %s/run%04d/module_%s_analysis_calib.root %s/run%04d/module_%s_integrals.hdf5' % (sourceType,path,run,barcode,path,run,barcode)
            print(command)
            if args.submit: os.system(command)

            slot += 1
        else:
            slot += 1
