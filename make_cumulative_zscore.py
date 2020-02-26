#!/bin/env python3
import gdal
import os, sys
import numpy as np
import glob

## ./Bayesian/20191119/bayes_deviation_ascending_L15-0136E-1139N_20191119.tif
## L15-0125E-1148N_20191007_to_20191014_zscore_base.tif

def accumulate(tileid, stopat):

  coralfile = 'CoralNew/' + tileid + '_coral2.tif'                                
  if os.path.exists(coralfile):                                                 
    coDS = gdal.Open(coralfile, gdal.GA_ReadOnly)                               
  else:                                                                         
    print('File %s does not exist' % (coralfile))                               
    sys.exit(0)                                                                 
                                                                                
  cmask = coDS.GetRasterBand(1).ReadAsArray()                                   
  notcoral = np.equal(cmask, 0)                                                     
  coDS = None                                            

  matchit = glob.glob('Zscorefiles/descending_' + tileid + '*_zscore_base.tif')
  matchit_sorted = sorted(matchit)
  
  for f,img in enumerate(matchit_sorted):
    if stopat+'_zscore_base.tif' in img:
      endit = f
      break

  if (endit is not None):
    matchit_sorted = matchit_sorted[0:(endit+1)]

  ## pvmaskfile = glob.glob('Persistent_Deviation/20200121/persistant_deviation_*scending_'+tileid+'_20200121_cleaned.tif')

  ## if (len(pvmaskfile) > 0):
  ##   pvDS = gdal.Open(pvmaskfile[0], gdal.GA_ReadOnly)
  ##   gt = pvDS.GetGeoTransform()
  ##   proj = pvDS.GetProjection()
  ##   pvarr = pvDS.GetRasterBand(1).ReadAsArray() 
  ##   pvmask = np.less(pvarr, 2)
  ##   pvDS = None
  ## else:
  ##   print('PV image %s not found' % (pvmaskfile[0]))
  ##   sys.exit(0)

  tmpDS = gdal.Open(matchit_sorted[0], gdal.GA_ReadOnly)
  xsize = tmpDS.RasterXSize
  ysize = tmpDS.RasterYSize
  gt = tmpDS.GetGeoTransform()
  proj = tmpDS.GetProjection()
  tmpDS = None
  
  drv = gdal.GetDriverByName('GTiff')
  
  outDS = drv.Create('zscore_cumul_'+tileid+'_'+stopat+'.tif', xsize, ysize, 
    1, gdal.GDT_Float32, options=['COMPRESS=LZW', 'TILED=YES'])
  outDS.SetGeoTransform(gt)
  outDS.SetProjection(proj)
  outDS.GetRasterBand(1).SetNoDataValue(-9999)
  
  DS = []
  
  for infile in matchit_sorted:
    DS.append(gdal.Open(infile, gdal.GA_ReadOnly))
  
  for _line in range(ysize):
    cumul = np.zeros((1,xsize))
    for inDS in DS:
      theline = inDS.GetRasterBand(1).ReadAsArray(0, _line, xsize, 1)
      good = np.not_equal(theline, -9999)
      cumul[good] += theline[good]
    bad = np.equal(cumul, 0)
    cumul[bad] = -9999
    cumul[notcoral[_line,:].reshape(1,xsize)] = -9999
    ## pvmaskline = pvmask[_line,:].reshape((1,xsize))
    ## cumul[pvmaskline] = -9999
    outDS.GetRasterBand(1).WriteArray(cumul, 0, _line)
  
  ## close output image
  outDS.FlushCache()
  outDS = None
  
  ## close input datasets
  for k in DS:
    k = None
  
tileids = ['L15-0171E-0922N', 'L15-0171E-0923N', 'L15-0172E-0922N']

## tileids = ['L15-0112E-1150N', 'L15-0112E-1151N', 'L15-0112E-1152N',
## 'L15-0113E-1151N', 'L15-0113E-1152N', 'L15-0114E-1152N',
## 'L15-0115E-1151N', 'L15-0115E-1152N', 'L15-0115E-1153N',
## 'L15-0116E-1151N', 'L15-0116E-1153N', 'L15-0117E-1151N',
## 'L15-0117E-1152N', 'L15-0117E-1153N', 'L15-0123E-1148N',
## 'L15-0123E-1149N', 'L15-0124E-1147N', 'L15-0124E-1148N',
## 'L15-0124E-1149N', 'L15-0124E-1150N', 'L15-0125E-1147N',
## 'L15-0125E-1148N', 'L15-0125E-1149N', 'L15-0125E-1150N',
## 'L15-0126E-1147N', 'L15-0126E-1148N', 'L15-0126E-1149N',
## 'L15-0127E-1147N', 'L15-0127E-1148N', 'L15-0128E-1146N',
## 'L15-0129E-1146N', 'L15-0129E-1147N', 'L15-0130E-1144N',
## 'L15-0130E-1145N', 'L15-0130E-1146N', 'L15-0130E-1147N',
## 'L15-0131E-1144N', 'L15-0131E-1145N', 'L15-0131E-1146N',
## 'L15-0131E-1147N', 'L15-0132E-1143N', 'L15-0132E-1144N',
## 'L15-0132E-1145N', 'L15-0132E-1146N', 'L15-0132E-1147N',
## 'L15-0133E-1143N', 'L15-0133E-1144N', 'L15-0133E-1145N',
## 'L15-0133E-1146N', 'L15-0134E-1143N', 'L15-0134E-1144N',
## 'L15-0134E-1145N', 'L15-0135E-1143N', 'L15-0135E-1144N',
## 'L15-0135E-1145N', 'L15-0136E-1134N', 'L15-0136E-1135N',
## 'L15-0136E-1136N', 'L15-0136E-1137N', 'L15-0136E-1138N',
## 'L15-0136E-1139N', 'L15-0136E-1144N', 'L15-0136E-1145N',
## 'L15-0137E-1133N', 'L15-0137E-1134N', 'L15-0137E-1135N',
## 'L15-0137E-1136N', 'L15-0137E-1139N', 'L15-0137E-1140N',
## 'L15-0137E-1141N', 'L15-0138E-1133N', 'L15-0138E-1134N',
## 'L15-0138E-1140N', 'L15-0138E-1141N', 'L15-0139E-1134N',
## 'L15-0139E-1135N', 'L15-0139E-1140N', 'L15-0140E-1135N',
## 'L15-0140E-1140N', 'L15-0141E-1135N', 'L15-0141E-1136N',
## 'L15-0141E-1138N', 'L15-0141E-1139N', 'L15-0141E-1140N',
## 'L15-0142E-1136N', 'L15-0142E-1137N', 'L15-0142E-1138N',
## 'L15-0143E-1136N', 'L15-0143E-1137N']
## tileids = tileids[-38:]
## tileids = tileids[0:52]

theweeks = ['20190408', '20190415', '20190422', 
'20190429', '20190506', '20190513', 
'20190520', '20190527', '20190603', 
'20190610', '20190617', '20190624', 
'20190701', '20190708', '20190715', 
'20190722', '20190729', '20190805', 
'20190812', '20190819', '20190826', 
'20190902', '20190909', '20190916', 
'20190923', '20190930', '20191007'] 

for week in theweeks:
  for tileid in tileids:
    accumulate(tileid, week)
    print('Finished %s %s' % (tileid, week))
