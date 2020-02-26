#!/bin/env python3
import argparse
import gdal
import numpy as np
import os
import sys
import yaml
import glob
import subprocess
import datetime

## This code takes the following arguements
## tileid = the tile ID (e.g., L15-0115E-1153N)
## ascdesc = the indicator of whether the image is an ascending or descending imagetile ID (e.g., L15-0115E-1153N)
## This can be made automatically determined based on the quality of a given image. For Hawaii, certain tile IDs have been selected 
## to be either ascending or descending
## stopat = this is for processing up to a certain week, given from Monday to Monday (e.g., 20200113_to_20200120)

tileid = sys.argv[1]
ascdesc = sys.argv[2]
stopat = sys.argv[3]

## Look through the directories with the bottom reflectance tiles
thedirs = glob.glob(ascdesc + '_20[0-9][0-9][0-1][0-9][0-3][0-9]_to_20[0-9][0-9][0-1][0-9][0-3][0-9]')
files = []

## go through those files and get the bottom reflectance (br) files.
for thedir in thedirs:
  tilepath = thedir + os.path.sep + tileid + '_rb.tif'
  if os.path.exists(tilepath):
    files.append(tilepath)

## sort the files and report
files.sort()
print("Got %d files for tile %s" % (len(files), tileid))
print("First file: %s" % (files[0]))
print("Last file: %s" % (files[-1]))

## separate baseline from Bleaching files
## for Hawaii, the baseline period was April through August 2019
## I know that this logic is silly and should use the datetime package to work this out.  We just kept caring this logic forward, but we need something more elegant.
baseline_files = [x for x in files if '201908' not in x and '201909' not in x and '201910' not in x and '201911' not in x and '201912' not in x and '202001' not in x and '202002' not in x]
temp_bleaching_files = [x for x in files if '201908' in x or '201909' in x or '201910' in x or '201911' in x or '201912' in x or '202001' in x or '202002' in x]
bleaching_files = []

## create a date object of the week to stop
stopdate = datetime.datetime(int(stopat[-8:-4]), int(stopat[-4:-2]), int(stopat[-2:])) + datetime.timedelta(days=1)

## go through the files to only get the bleaching files up to the "stopping week"
for j,name in enumerate(temp_bleaching_files):
  imgdatestr = name.split('_')[3][0:8]
  imgdate = datetime.datetime(int(imgdatestr[0:4]), int(imgdatestr[4:6]), int(imgdatestr[6:]))
  if (imgdate < stopdate):
    bleaching_files.append(name) 

if (len(bleaching_files) < 2):
  print('Not enough times series tiles to do differencing.  Exiting.')
  sys.exit(0)

## go through each image and open it as a GDAL dataset
baseline_datasets = []
for _f in range(len(baseline_files)):
    baseline_datasets.append(gdal.Open(baseline_files[_f],gdal.GA_ReadOnly))
    print((baseline_files[_f],baseline_datasets[-1].RasterXSize,baseline_datasets[-1].RasterYSize))

bleaching_datasets = []
for _f in range(len(bleaching_files)):
    bleaching_datasets.append(gdal.Open(bleaching_files[_f],gdal.GA_ReadOnly))
    print((bleaching_files[_f],bleaching_datasets[-1].RasterXSize,bleaching_datasets[-1].RasterYSize))

## Open coral mask
## this is for the coral mask files divided up into the same tile scheme as the other data.
## a value of 1 indicates it is coral and 0 is not.
maskfile = 'CoralNew/' + tileid + '_coral2.tif'
print('Maskfile %s' % (maskfile))
maskset = gdal.Open(maskfile, gdal.GA_ReadOnly)

## Get parameters for output file
driver = gdal.GetDriverByName('GTiff')
driver.Register()

x_off = 0
y_off = 0
x_size = baseline_datasets[0].RasterXSize
y_size = baseline_datasets[0].RasterYSize

trans = baseline_datasets[0].GetGeoTransform()
out_trans = list(trans)
out_trans[0] += x_off*trans[1]
out_trans[3] += y_off*trans[5]

n_output_bands = 2
## outname = 'persistant_deviation_{}_{}_{:0>2d}.tif'.format(ascdesc, tileid, stopat)
outdir = '/scratch/dknapp4/Hawaii_Weekly/AscendingDescending/Persistent_Deviation/'+stopdate.strftime('%Y%m%d')+'/'
outname = 'persistant_deviation_{}_{}_{}.tif'.format(ascdesc, tileid, stopdate.strftime('%Y%m%d'))
outDataset = driver.Create(outdir+outname,x_size,y_size,n_output_bands,gdal.GDT_Float32,options=['COMPRESS=LZW','TILED=YES'])
outDataset.SetProjection(baseline_datasets[0].GetProjection())
outDataset.SetGeoTransform(out_trans)

## create array to hold results
change_dat = np.zeros((y_size,x_size,n_output_bands),dtype=np.float32) -9999

## Go through images line by line to determine baseline and count pixels above maximum from baseline
## Apply mask to each line
for _line in range(y_off, y_off+y_size):

    # get the baseline values
    line_dat = np.zeros((x_size,len(baseline_datasets)))
    for _f in range(len(baseline_files)):
        line_dat[:,_f] = np.squeeze(baseline_datasets[_f].ReadAsArray(x_off,_line,x_size,1))

    # merge those values together to determine baseline
    line_dat[line_dat == -9999] = np.nan
    baseline = np.nanmax(line_dat,axis=1)

    # step through bleaching datasets
    n_dev = np.zeros(x_size)
    max_dev = np.zeros(x_size) - 9999
    
    ## go through each bleaching week and count number of times above baseline max
    for _f in range(len(bleaching_datasets)):
        ldat = np.squeeze(bleaching_datasets[_f].ReadAsArray(x_off,_line,x_size,1))

        # add one for each deviation above baseline
        n_dev[ldat > baseline] += 1

        # save the maximum deviation
        max_dev[ldat > baseline] = np.maximum(ldat - baseline, max_dev)[ldat > baseline]
        
    mask = np.squeeze(maskset.ReadAsArray(x_off,_line,x_size,1))

    n_dev[mask == 0] = -9999
    max_dev[mask == 0] = -9999

    change_dat[_line-y_off,:,0] = n_dev
    change_dat[_line-y_off,:,1] = max_dev

## write out each band (n_dev and max_dev) and  close output file
for n in range(change_dat.shape[-1]):
    outDataset.GetRasterBand(n+1).WriteArray(np.squeeze(change_dat[...,n]),0,0)
    outDataset.GetRasterBand(n+1).SetNoDataValue(-9999)
del outDataset

## close Bleaching and baseline data sets
for thisDS in bleaching_datasets:
  thisDS = None

for thisDS in baseline_datasets:
  thisDS = None
## print rough histogram data for reality check
print(np.histogram(change_dat[change_dat != -9999]))

## produce overlays for output tif file
subprocess.call('gdaladdo {} 2 4 8 16 32 64 128'.format(outdir+outname),shell=True)

