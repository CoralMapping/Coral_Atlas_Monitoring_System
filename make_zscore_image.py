#!/bin/env python3
import gdal
import os, sys
import numpy as np
import glob
import warnings

def main(tile, ascdesc, theweek, basebleach):
  
  drv = gdal.GetDriverByName('GTiff')
  
  infile = ascdesc + '_' + theweek + '/' + tile + '_br_comp.tif'
  outfile = ascdesc + '_' + theweek + '/' + tile + '_zscore_base.tif'

  if (basebleach == 'base'):
    statfile = 'BaseFiles/' + ascdesc + '_' + tile + '_base.tif'
  else:
    statfile = 'BleachFiles/' + ascdesc + '_' + tile + '_bleach.tif'

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

  gt = inDS.GetGeoTransform()
  proj = inDS.GetProjection()
  
  outDS = drv.Create(outfile, inDS.RasterXSize, inDS.RasterYSize, 1, gdal.GDT_Float32, options=['COMPRESS=LZW', 'TILED=YES'])
  outDS.SetGeoTransform(gt)
  outDS.SetProjection(proj)
  Band1 = outDS.GetRasterBand(1)

  rb = inDS.GetRasterBand(1).ReadAsArray()
  statmean = stDS.GetRasterBand(1).ReadAsArray() 
  statsdev = stDS.GetRasterBand(2).ReadAsArray() 

  good = np.logical_and(np.greater(rb, -9999), np.greater(statmean, -9999))
  zscore = np.zeros((inDS.RasterYSize, inDS.RasterXSize), dtype=np.float32) - 9999
  zval = (rb[good] - statmean[good])/statsdev[good]
  zscore[good] = zval
  Band1.WriteArray(zscore)
  Band1.FlushCache()
  Band1.SetNoDataValue(-9999.)
  inDS, stDS, outDS = None, None, None

if __name__ == "__main__":

  if len( sys.argv ) != 5:
    print("[ ERROR ] you must supply 4 arguments: make_zscore_image.py tile ascdesc theweek basebleach")
    print("where:")
    print("    tile = the tile id, e.g. L15-0113E-1152N")
    print("    ascdesc = to indicate whether image is ascending or descending.")
    print("    theweek = the week indicator, e.g. 20191223_to_20191230")
    print("    basebleach = either base or bleach to indicate to which distribution the zscore should be relative")
    print("")

    sys.exit( 0 )

  main( sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] )
