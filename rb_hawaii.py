import gdal, ogr, osr
import numpy as np
import sys, os
import math
import warnings

def rb(inreflfile, chla, depthfile, outfile, logf):

  warnings.filterwarnings("ignore")
  
  constantfile = os.path.dirname(__file__)+os.sep+"constant_values.csv"

  if os.path.isfile(constantfile): 
    try:
      convals = np.genfromtxt(constantfile, delimiter=",", names=True)
    except:
      print(("RB: could not read %s with with numpy.genfromtxt") % ("constant_values.csv"))
      print("Cannot proceed with processing tiles without constant_values.csv")
      if (logf is not None):
        logf.write(("RB: could not read %s with with numpy.genfromtxt\n") % ("constant_values.csv"))
        logf.write("Cannot proceed with processing tiles without constant_values.csv\n")
      return 9
  else:
    print(("File: %s does not exist") % ("constant_values.csv"))
    print("Cannot proceed with processing tiles without constant_values.csv")
    if (logf is not None):
      logf.write("constant_values.csv not found.  Cannot proceed.\n")
    return 9
    
  ## Band center wavelengths
  bandwv = [480, 540, 610]
  
  # if image file does not exist, skip it.
  if (os.path.isfile(inreflfile)):
    try:
      rasterDS = gdal.Open(inreflfile, gdal.GA_ReadOnly)
    except:
      print(("RB: could not open file %s with GDAL API") % (inreflfile))
      if (logf is not None):
        logf.write(("RB: could not open file %s with GDAL API\n") % (inreflfile))
      return 9
  else:
    if (logf is not None):
      logf.write(("File: %s does not exist\n") % (inreflfile))
    return 9

  ## set up values as described by Ji-Wei
  aph440 = 0.06 * math.pow(chla, 0.65)
  acdom440 = 0.5 * aph440
  bbp555 = 0.6 * math.pow(chla, 0.62)
  bbpvec = np.zeros((301,2), dtype=np.float)
  aphvec = np.zeros((301,2), dtype=np.float)
  bbvec = np.zeros((301,2), dtype=np.float)
  atvec = np.zeros((301,2), dtype=np.float)
  rrsdeepvec = np.zeros((301,2), dtype=np.float)
  acdomvec = np.zeros((301,2), dtype=np.float)
  dcvec = np.zeros((301,2), dtype=np.float)

  for d in np.arange(301):
    bbpvec[d,0] = (400 + d)
    bbvec[d,0] = (400 + d)
    atvec[d,0] = (400 + d)
    aphvec[d,0] = (400 + d)
    rrsdeepvec[d,0] = (400 + d)
    acdomvec[d,0] = (400 + d)
    dcvec[d,0] = (400 + d)

    bbpvec[d,1] = (0.002 + 0.02 * (0.5 - 0.25 * math.log10(chla)) * (550./float(400+d))) * bbp555
    bbvec[d,1] = convals[d]['bbw'] + bbpvec[d,1]
    aphvec[d,1] = (convals[d]['a0'] + convals[d]['a1'] * math.log(aph440)) * aph440
    acdomvec[d,1] = acdom440 * np.exp(-0.015 * ((400+d)-440))
    atvec[d,1] = convals[d]['aw'] + aphvec[d,1] + acdomvec[d,1]
    rrsdeepvec[d,1] = (0.089 + 0.125 * (bbvec[d,1]/(atvec[d,1] + bbvec[d,1]))) * (bbvec[d,1]/(atvec[d,1] + bbvec[d,1]))
    dcvec[d,1] = 1.03 * math.pow(1.0 + 2.4 * (bbvec[d,1]/(atvec[d,1]+bbvec[d,1])), 0.5)
  
  ## Read depth data 
  if (os.path.isfile(depthfile)):
    try:
      depDS = gdal.Open(depthfile, gdal.GA_ReadOnly)
      raster_trans = rasterDS.GetGeoTransform()
      depth_trans = depDS.GetGeoTransform()
      x_px_l = int(round((raster_trans[0] - depth_trans[0])/depth_trans[1]))
      y_px_t = int(round((raster_trans[3] - depth_trans[3])/depth_trans[5]))
      depthdata = depDS.GetRasterBand(1).ReadAsArray(x_px_l,y_px_t,rasterDS.RasterXSize,rasterDS.RasterYSize)
    except:
      print(("RB: Could not read depthdata into array from file %s") % (depthfile))
      if (logf is not None):
        logf.write(("RB: Could not read depthdata into array from file %s\n") % (depthfile))
      return 9
  else:
    print(("RB: file %s does not exist") % (depthfile))
    if (logf is not None):
      logf.write(("RB: file %s does not exist\n") % (depthfile))
    return 9
    
  del depDS

  ## make mask of data area
  if (rasterDS.RasterCount > 4):
    try:
      maskdata = rasterDS.GetRasterBand(5).ReadAsArray()
      mask = np.equal(maskdata, 65535)
      maskdata = None
    except:
      print("Exception: problem reading mask band")
      return 9
  else:
    try:
      maskdata = rasterDS.GetRasterBand(1).ReadAsArray()
      mask = np.logical_and(np.not_equal(maskdata, -9999), np.not_equal(maskdata, 0))
      maskdata = None
    except:
      print("Exception: problem reading mask band")
      return 9

  good2 = np.logical_and(mask, np.logical_and(np.less_equal(depthdata, 1500), \
    np.greater(depthdata, -1)))

  maskdata = None

  ## Create output GDAL Data set of Rb result
  drv = gdal.GetDriverByName('GTiff')
  try:
    #outDS = drv.Create(outfile, xsize=good2.shape[1], ysize=good2.shape[0], bands=3, eType=gdal.GDT_Int16)
    outDS = drv.Create(outfile, xsize=good2.shape[1], ysize=good2.shape[0], bands=1, eType=gdal.GDT_Int16)
  except:
    print(("RB: Cannot create output file %s for bottom reflectance") % (outfile))
    if (logf is not None):
      logf.write(("RB: Cannot create output file %s for bottom reflectance\n") % (outfile))
    return 9
    
  try:
    outDS.SetGeoTransform(rasterDS.GetGeoTransform())
    outDS.SetProjection(rasterDS.GetProjection())
    ## outDS.SetMetadataItem('wavelength', "{ 475.0, 540.0, 625.0 }", 'ENVI')
    ## outDS.SetMetadataItem('wavelength units', "nanometers", 'ENVI')
    ## outDS.SetMetadataItem('data ignore value', "-9999.", 'ENVI')
  except:
    print(("RB: Cannot create GeoTransform and/or Projection or MetaData for file %s for bottom reflectance") % (outfile))
    if (logf is not None):
      logf.write(("RB: Cannot create GeoTransform and/or Projection for file %s\n") % (outfile))
    return 9
    
  depthvec = depthdata[good2] / 100.0
  del depthdata

  ## Read NIR band for doing glint correction on the other bands
  try:
    nirdata = rasterDS.GetRasterBand(4).ReadAsArray()
  except:
    print(("RB: Cannot read NIR band from file %s") % (inreflfile))
    if (logf is not None):
      logf.write(("RB: Cannot read NIR band from file %s\n") % (inreflfile))
    return 9

  #for band in np.arange(rasterDS.RasterCount-1).astype(int):
  #for band in range(len(bandwv)):
  for band in [1]:
    try:
      thisdata = rasterDS.GetRasterBand(int(band)+1).ReadAsArray()
    except:
      print(("RB: Cannot read band %d from file %s") % (int(band)+1,inreflfile))
      if (logf is not None):
        logf.write(("RB: Cannot read band %d from file %s\n") % (int(band)+1,inreflfile))
      return 9

    ## Use NIR band for glint removal
    gooddata = thisdata[good2].astype(int) - nirdata[good2].astype(int)
    rrsbig = gooddata/(np.pi * 10000.0)
    rrsvec = rrsbig/(0.52 + 1.7 * rrsbig) 
    rrscvec =  rrsdeepvec[bandwv[band]-400,1] * (1.0 - np.exp(-dcvec[bandwv[band]-400,1] \
      * (atvec[bandwv[band]-400,1] + bbvec[bandwv[band]-400,1]) * depthvec))

    rrsbvec = rrsvec - rrscvec
    dbvec = 1.05 * math.pow(1.0 + 5.5 * (bbvec[bandwv[band]-400,1]/(atvec[bandwv[band]-400,1] + bbvec[bandwv[band]-400,1])), 0.5)
    rbvec = (rrsbvec * np.pi)/(np.exp(-dbvec * (atvec[bandwv[band]-400,1] + bbvec[bandwv[band]-400,1]) * depthvec))
    rbout = np.ones((nirdata.shape[0], nirdata.shape[1]), dtype=np.int16) * -9999.
    rbout[good2] = rbvec * 10000
    #outband = outDS.GetRasterBand(int(band)+1)
    outband = outDS.GetRasterBand(1)
    
    try:
      outband.WriteArray(rbout.astype(np.int16))
    except:
      if (logf is not None):
        logf.write(("RB: Cannot write band %d to file %s\n") % (int(band)+1, outfile))
      return 9

    outband.SetNoDataValue(-9999)
    outband.FlushCache()
  del rasterDS, outDS
  return 0
