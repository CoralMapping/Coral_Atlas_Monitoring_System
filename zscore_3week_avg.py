#!/bin/env python3
import gdal
import numpy as np
import os, sys
import warnings

def main(img1, img2, img3):

  np.seterr(all='ignore')

  outfile = 'Zscore_3week_Avg/' + os.path.splitext(os.path.basename(img2))[0] + '_3weekavg.tif' 

  inDS1 = gdal.Open(img1, gdal.GA_ReadOnly)
  inDS2 = gdal.Open(img2, gdal.GA_ReadOnly)
  inDS3 = gdal.Open(img3, gdal.GA_ReadOnly)

  proj = inDS1.GetProjection()
  gt1 = inDS1.GetGeoTransform()
  gt2 = inDS2.GetGeoTransform()
  gt3 = inDS3.GetGeoTransform()

  drv = gdal.GetDriverByName('GTiff')
  outDS = drv.Create(outfile, inDS2.RasterXSize, inDS2.RasterYSize, 1, \
    eType=gdal.GDT_Float32, options=['COMPRESS=LZW','TILED=YES'])
  outDS.SetGeoTransform(gt2)
  outDS.SetProjection(proj)

  test1 = np.isclose(gt1, gt2, atol=0.01)
  test2 = np.isclose(gt2, gt3)
  allclose = np.logical_and(test1, test2)
  if (np.sum(allclose) != 6):
    print('GeoTransforms of the 3 images are not the same.')
    inDS1, inDS2, inDS3 = None, None, None
    return 0

  data1 = inDS1.GetRasterBand(1).ReadAsArray()
  data2 = inDS2.GetRasterBand(1).ReadAsArray()
  data3 = inDS3.GetRasterBand(1).ReadAsArray()

  bad1 = np.equal(data1, -9999)
  data1[bad1] = np.nan
  bad2 = np.equal(data2, -9999)
  data2[bad2] = np.nan
  bad3 = np.equal(data3, -9999)
  data3[bad3] = np.nan

  badstack = np.stack((bad1, bad2, bad3)).astype(np.uint8)
  goodsum = 3 - np.sum(badstack, axis=0)
  setmiss = np.less(goodsum, 2)

  datastack = np.stack((data1, data2, data3))
  with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    meandata = np.nanmean(datastack, axis=0)
  meandata[setmiss] = -9999.
  thenans = np.isnan(meandata)
  meandata[thenans] = -9999.
  outBand = outDS.GetRasterBand(1)
  outBand.WriteArray(meandata)
  outBand.SetNoDataValue(-9999.)

  outBand = None
  outDS, inDS1, inDS2, inDS3 = None, None, None, None

if __name__ == "__main__":                                                      
                                                                                
  if len( sys.argv ) != 4:                                                      
    print("[ ERROR ] you must supply 3 arguments: zscore_3week_avg.py imgfile1, imgile2, ingfile3")
    print("where:")
    print("    imgfile1 = the 1st week input image for making the 3-week average")
    print("    imgfile2 = the 2nd week input image for making the 3-week average")
    print("    imgfile3 = the 3rd week input image for making the 3-week average")
    print("")
    sys.exit( 0 )                                                               
                                                                                
  main(sys.argv[1], sys.argv[2], sys.argv[3])

