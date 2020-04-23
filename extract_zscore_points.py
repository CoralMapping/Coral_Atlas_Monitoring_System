#!/bin/env python3
import gdal
import ogr
import osr
import numpy as np
import os, sys

""" This code is for the Allen Coral Atlas (ACA) Monitoring System version 2, 
developed by Yaping Xu in April 2020.  
This code extracts points from the Zscore images and gives each point an attribute
based on its Z-score value.  Only pixels greater than or equal to 1 are included,
 with values.
"""

def main(inzscoreimg, outshapefile):

  if not os.path.exists(inzscoreimg):
    print("File %s does not exist. Quitting." % (inzscoreimg))
    sys.exit(0)

  inDS = gdal.Open(inzscoreimg, gdal.GA_ReadOnly)
  gt = inDS.GetGeoTransform()
  proj = inDS.GetProjection()
  data = inDS.GetRasterBand(1).ReadAsArray()
  inDS = None

  highvals = np.greater_equal(data, 1.0)
  lin, pix = np.nonzero(highvals)
  ycoords = gt[3] + (lin * gt[5])
  xcoords = gt[0] + (pix * gt[1])

  spatialReference = osr.SpatialReference()
  spatialReference.ImportFromEPSG(3857) 

  drv = ogr.GetDriverByName('ESRI Shapefile')
  shapeData = drv.CreateDataSource(outshapefile)
  layer = shapeData.CreateLayer('zscore', spatialReference, ogr.wkbPoint)
  layer_defn = layer.GetLayerDefn() # gets parameters of the current shapefile
  pointidDefn = ogr.FieldDefn('pointid', ogr.OFTInteger)
  zscoreDefn = ogr.FieldDefn('zscore', ogr.OFTReal)
  zscoreDefn.SetWidth(8)
  zscoreDefn.SetPrecision(2)
  layer.CreateField(pointidDefn)
  layer.CreateField(zscoreDefn)

  featureIndex = 0 #this will be the second polygon in our dataset

  for j in range(ycoords.shape[0]):
    pnt = ogr.Geometry(ogr.wkbPoint)
    pnt.AddPoint(xcoords[j], ycoords[j])
    feature = ogr.Feature(layer_defn)
    feature.SetGeometry(pnt)
    feature.SetFID(featureIndex)
    feature.SetField('pointid', j+1)
    feature.SetField('zscore', float(data[lin[j],pix[j]]))
    layer.CreateFeature(feature)
    featureIndex += 1
    pnt = None
    feature = None

  shapeData.Destroy() #lets close the shapefile


if __name__ == "__main__":
  if (len(sys.argv) != 3):
    print('Usage: extract_zscore_points.py inzscoreimage outpoint_shapefile')
    print('where:')
    print('    inzscoreimage = input Zscore image')
    print('    outpoint_shapefile = output Shapefile with points >= 1')
    sys.exit(0)
  main(sys.argv[1], sys.argv[2])
