#!/bin/env python3
import gdal
import numpy as np
import os
import sys
import yaml
import glob
import subprocess
import datetime
import scipy.stats as st

tileid = sys.argv[1]
ascdesc = sys.argv[2]
stopat = sys.argv[3]

thedirs = glob.glob(ascdesc + '_20[0-9][0-9][0-1][0-9][0-3][0-9]_to_20[0-9][0-9][0-1][0-9][0-3][0-9]')
basefile = 'BaseFiles/'+ascdesc+'_'+tileid+'_base.tif'

stopdate = datetime.datetime(int(stopat[-8:-4]), int(stopat[-4:-2]), int(stopat[-2:])) + datetime.timedelta(days=1)
starttime = stopdate - datetime.timedelta(days=8)
stoptime = stopdate - datetime.timedelta(days=1)

bleachfile = ascdesc + '_' + starttime.strftime('%Y%m%d') + '_to_' + stoptime.strftime('%Y%m%d') + os.path.sep + tileid + '_br_comp.tif'
if not (os.path.exists(basefile) and os.path.exists(bleachfile)):
  print('Base or Bleach file does not exist..exitting: %s' % (bleachfile))

bDS = gdal.Open(basefile, gdal.GA_ReadOnly)
xsize = bDS.RasterXSize
ysize = bDS.RasterYSize
gt = bDS.GetGeoTransform()
proj = bDS.GetProjection()
meanBaseData = bDS.GetRasterBand(1).ReadAsArray()
sdBaseData = bDS.GetRasterBand(2).ReadAsArray()

blDS = gdal.Open(bleachfile, gdal.GA_ReadOnly)
pseudomeanBleachData = blDS.GetRasterBand(1).ReadAsArray()
good = np.logical_and(np.not_equal(pseudomeanBleachData, -9999), np.not_equal(meanBaseData, -9999))
pseudosdev = 400
zcrit = (pseudomeanBleachData - meanBaseData)/np.sqrt(np.power(sdBaseData,2) + pseudosdev**2)
prob = st.norm.cdf(zcrit)
outData = np.zeros((ysize, xsize), np.float32) - 9999.
outData[good] = prob[good]

## maskfile = 'CoralNew2/' + tileid + '_coral.tif'
## maskfile = 'CoralTiles10m/' + tileid + '_coral.tif'
## print('Maskfile %s' % (maskfile))
## maskset = gdal.Open(maskfile, gdal.GA_ReadOnly)

driver = gdal.GetDriverByName('GTiff')
driver.Register()

## outname = 'persistant_deviation_{}_{}_{:0>2d}.tif'.format(ascdesc, tileid, stopat)
outdir = '/scratch/dknapp4/Hawaii_Weekly/AscendingDescending/Bayesian/'+stopdate.strftime('%Y%m%d')+'/'
outname = 'bayes_deviation_{}_{}_{}.tif'.format(ascdesc, tileid, stopdate.strftime('%Y%m%d'))
outDS = driver.Create(outdir+outname, xsize, ysize, 1, gdal.GDT_Float32,options=['COMPRESS=LZW','TILED=YES'])
outDS.GetRasterBand(1).WriteArray(outData.astype(np.float32))
outDS.SetProjection(proj)
outDS.SetGeoTransform(gt)
outDS.GetRasterBand(1).SetNoDataValue(-9999.)
bDS, blDS, outDS = None, None, None

subprocess.call('gdaladdo {} 2 4 8 16 32 64 128'.format(outdir+outname),shell=True)

