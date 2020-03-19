#!/bin/env python3
import gdal
import os, sys
import numpy as np
import glob
import warnings

def main(tile, ascdesc, stopat):
  
  drv = gdal.GetDriverByName('GTiff')
  
  ## infile = ascdesc + '_' + theweek + '/' + tile + '_br_comp.tif'
  ## e.g. descending_L15-0143E-1137N_bleach_20191125.tif

  infile = 'BleachFiles/' + ascdesc + '_' + tile + '_bleach_' + stopat + '.tif'
  outfile = 'BleachFiles/' + ascdesc + '_' + tile + '_bleach_' + stopat + '_zscore_base.tif'
  statfile = 'BaseFiles/' + ascdesc + '_' + tile + '_base.tif'

  coralfile = 'CoralNew/' + tile + '_coral3.tif'

  if os.path.exists(infile):
    inDS = gdal.Open(infile, gdal.GA_ReadOnly)
  else:
    print('File %s does not exist' % (infile))
    sys.exit(0)

  if os.path.exists(statfile):
    stDS = gdal.Open(statfile, gdal.GA_ReadOnly)
  else:
    inDS = None
    print('File %s does not exist' % (statfile))
    sys.exit(0)

  if os.path.exists(coralfile):
    coDS = gdal.Open(coralfile, gdal.GA_ReadOnly)
  else:
    inDS = None
    stDS = None
    print('File %s does not exist' % (coralfile))
    sys.exit(0)

  cmask = coDS.GetRasterBand(1).ReadAsArray()
  mask = np.equal(cmask, 1)
  coDS = None

  gt = inDS.GetGeoTransform()
  proj = inDS.GetProjection()
  
  outDS = drv.Create(outfile, inDS.RasterXSize, inDS.RasterYSize, 1, gdal.GDT_Float32, options=['COMPRESS=LZW', 'TILED=YES'])
  outDS.SetGeoTransform(gt)
  outDS.SetProjection(proj)
  Band1 = outDS.GetRasterBand(1)

  rb = inDS.GetRasterBand(1).ReadAsArray()
  statmean = stDS.GetRasterBand(1).ReadAsArray() 
  statsdev = stDS.GetRasterBand(2).ReadAsArray() 

  pregood = np.logical_and(np.greater(rb, -9999), np.greater(statmean, -9999))
  good = np.logical_and(pregood, mask)

  zscore = np.zeros((inDS.RasterYSize, inDS.RasterXSize), dtype=np.float32) - 9999
  zval = (rb[good] - statmean[good])/statsdev[good]
  zscore[good] = zval
  ## find Nans and Inf and replace with -9999.
  bad = np.logical_not(np.isfinite(zscore))
  zscore[bad] = -9999
  Band1.WriteArray(zscore)
  Band1.FlushCache()
  Band1.SetNoDataValue(-9999.)
  inDS, stDS, outDS = None, None, None

if __name__ == "__main__":

  if len( sys.argv ) != 4:
    print("[ ERROR ] you must supply 4 arguments: make_zscore_image.py tile ascdesc stopat")
    print("where:")
    print("    tile = the tile id, e.g. L15-0113E-1152N")
    print("    ascdesc = to indicate whether image is ascending or descending.")
    print("    stopat = the Monday on which to stop, e.g. 20191125")
    print("")

    sys.exit( 0 )

  main( sys.argv[1], sys.argv[2], sys.argv[3] )
