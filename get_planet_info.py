#!/bin/env python3
from planet import api
import planet
import numpy as np
import json
import subprocess
import requests
import os, sys
import math
import pyproj
import datetime
import dateutil.parser
import dateutil
import pvlib

"""The purpose of this code is to compare the input scenes for the quads of 
     a pair of Planet mosaics (made separately from Ascending and Descending scenes).
     The code connects to Planet to get the metadata for the mosaics, associated
     quads, and individual scenes.  
     The code determines the solar and view geometry of the scenes and compiles a
     a count of good and bad oriented scenes for Ascending and Descending data.
     It also compares the amount of coverage  of each quad for the 2 different
     orbits.  Finally, it determines which orbit (Ascending or Descending) to 
     select for each quad.

     The following example shows how to run the code for the comparison of
     the Ascending and Descending orbits for the mosaics of Hawaii for the 
     week 20200427 to 20200504.  
     NOTE: The Ascending mosaic must be followed by the Descending mosaic.

     get_planet_info.py hawaii_reef_20200427_to_20200504_normalized_sr_shift_dark_ascending_mosaic hawaii_reef_20200427_to_20200504_normalized_sr_shift_dark_descending_mosaic

"""           

def get_ids(items):
  ## return a list of the quad ids from a given mosaic
  ids = []
  for item in items:
    thelink = item['link']
    theid = os.path.basename(thelink)
    pos = theid.find('#')
    ids.append(theid[0:pos])
  return ids
    
def get_crosstrack_direction(meta):
  ## read the geometry coordinates of the area of an image and determine
  ## its  orientation by searching for the longest segment.  This should
  ## be the across-track direction.
  ##

  ## get EPSG code of projection 
  epsg = str(meta['properties']['epsg_code'])
  utmproj = pyproj.Proj(init='EPSG:'+epsg)

  ## get coordinates.
  coords = meta['geometry']['coordinates'][0]

  ## check to make sure that I have gone deep enough.  This is to avoid 
  ## problems with multi-polygons
  if (len(coords[0]) != 2):
    coords = coords[0]
  segdir = []
  seglen = []
  utmcoords = []
  totx = 0.; toty= 0.;

  ## run through the coordinates and get an average of the coords
  ## to represent the center of the image for solar position
  ## calcula.tions
  for j in coords:
    utmx, utmy = utmproj(j[0], j[1])
    utmcoords.append([utmx, utmy])
    totx += j[0]
    toty += j[1]
  centx = totx/len(coords)
  centy = toty/len(coords)

  ## for each segment of the geometry, calculate its length and direction
  for k in range(len(utmcoords)-1):
    distx1 = utmcoords[k+1][0] - utmcoords[k][0]
    disty1 = utmcoords[k+1][1] - utmcoords[k][1]
    distx = pow(utmcoords[k+1][0] - utmcoords[k][0], 2)
    disty = pow(utmcoords[k+1][1] - utmcoords[k][1], 2)
    seglen.append(math.sqrt(distx+disty))
    segdir.append(math.degrees(math.atan2(distx1, disty1)))
    ## find longest segment and return its azimuth
    index = sorted(range(len(seglen)), key=lambda k: seglen[k])
    azim = segdir[index[-1]]
  return centx, centy, azim
    
def main(ascendingname, descendingname):
  ## This is the main program that accepts Ascending and Descending mosaic
  ## names
  ## connect to Planet database and download mosaics information
  today = datetime.datetime.now().isoformat()[0:19]
  fmosaicsname = 'mosaic_data_'+today+'_map.json'
  fmosaics = open(fmosaicsname, 'w+')
  subprocess.call(['planet', 'mosaics', 'list'], stdout=fmosaics)
  fmosaics.seek(0)
  mosdata = json.load(fmosaics)
  fmosaics.close()
  
  iddata = []
  numimgs = []
  client = api.ClientV1()
  
  ## see if the mosaics that user provided are in the data from Planet
  allmosaicnames = [ rec['name'] for rec in mosdata['mosaics'] ]
  if (ascendingname not in allmosaicnames) or (descendingname not in allmosaicnames) :
    print('Mosaic %s not found in currently available mosaics' % (ascendingname))
    print('OR')
    print('Mosaic %s not found in currently available mosaics' % (descendingname))
    return

  ## get data for the Ascending and Descending mosaics.
  fmap1 = open(ascendingname+'_map.txt', 'w+')
  subprocess.call(['planet', 'mosaics', 'search', ascendingname], stdout=fmap1)
  fmap1.seek(0)
  mapdata1 = json.load(fmap1)
  fmap1.close()
  fmap2 = open(descendingname+'_map.txt', 'w+')
  subprocess.call(['planet', 'mosaics', 'search', descendingname], stdout=fmap2)
  fmap2.seek(0)
  mapdata2 = json.load(fmap2)
  fmap2.close()

  ## Get the quad information for each of the 2 mosaics.
  ## join them together to make a list of  quads that appear in either or
  ## both mosaics
  numquads1 = len(mapdata1['items'])
  quadids1 = [ quad['id'] for quad in mapdata1['items'] ]
  numquads2 = len(mapdata2['items'])
  quadids2 = [ quad['id'] for quad in mapdata2['items'] ]
  allquads = np.unique(np.concatenate((quadids1, quadids2)))
  ## make array to hold output data.
  allquadcount = np.zeros((allquads.shape[0], 6))

  ## for the Ascending (map1) and the Descending (map2) data,
  ## get data on the individual scenes in each quad
  for k,mapstuff in enumerate([mapdata1['items'], mapdata2['items']]):
    for quadrec in mapstuff:
      thisquadname = 'L15-%04dE-%04dN' % (int(quadrec['id'].split('-')[0]),int(quadrec['id'].split('-')[1]))
      ## find the index of the quad for the row where data should be written.
      index = np.nonzero(np.char.equal(allquads, quadrec['id']))[0][0]
      quadlink = quadrec['_links']['_self']
      r = requests.get(quadlink)
      indivdata = r.json()
      iddata.append(quadrec['id'])
      numimgs.append(len(indivdata))
      g = requests.get(indivdata['_links']['items'])
      indiv = g.json()
      itemids = get_ids(indiv['items'])
      if (k == 0):
        allquadcount[index,0] = quadrec['percent_covered'] 
      else:
        allquadcount[index,1] = quadrec['percent_covered'] 

      ## print('%d, %s, %6.2f' % (k, thisquadname, quadrec['percent_covered']))
      ## print('===========================================')

      ## for each item (scene), get its solar information sand orientation.
      for item_id in itemids:
        try:
          temp = client.get_item("PSScene4Band", item_id).get()
        except planet.api.exceptions.MissingResource:
          print('Resource not found...skipping.')
          continue
        metadata = json.loads(json.dumps(temp))

        ## calculate orientation of image
        centerx, centery, cross = get_crosstrack_direction(metadata)

        ## get acquisition date
        acqdate = dateutil.parser.parse(metadata['properties']['acquired'])

        ## calculate solar position for center of  image at acquisition date
        sunpos = pvlib.solarposition.get_solarposition(acqdate, centery, centerx)
        if (cross < 0.0):
          cross += 180.0
        if (sunpos.azimuth[0] < 0.0):
          sunaz = 180. + sunpos.azimuth[0]
        else:
          sunaz = sunpos.azimuth[0]
        sunzen = sunpos.zenith[0]
        ## add scene to counts for Ascending or Descending scenes
        ## and good (> 3 degress difference) or bad (within 3deg of difference) 
        ## orientation
        try:
          if (k == 0):
            ## Ascending
            if (abs(sunaz-cross) < 3.0):
              allquadcount[index, 2] += 1
            elif (abs(sunaz-cross) >= 3.0):
              allquadcount[index, 3] += 1
          if (k == 1):
            ## Descending
            if (abs(sunaz-cross) < 3.0):
              allquadcount[index, 4] += 1
            elif (abs(sunaz-cross) >= 3.0):
              allquadcount[index, 5] += 1
        except:
          continue
        ## print('%s, %8.1f, %8.1f, %8.1f' % (acqdate.strftime('%Y%m%d'), cross, sunaz, sunzen))


  ## Now that all of the info has been gathered, examine it for each quad and determine
  ## whether to use Ascending or Descending and write out the data to a csv.
  ##
  tempparts = descendingname.split('_')
  pos = tempparts.index('descending')
  outname = '_'.join(tempparts[0:pos]) + '_compare_' + '_'.join(tempparts[pos+1:]) + '.csv'
  fout = open(outname, 'w')
  fout.write('QUADNAME, ORBIT, ASC_PERCOV, DESC_PERCOV, ASC_BAD, ASC_GOOD, DESC_BAD, DESC_GOOD\n')
  for j in range(len(allquads)):
    quadname = 'L15-%04dE-%04dN' % (int(allquads[j].split('-')[0]), int(allquads[j].split('-')[1]))
    orbit = 'Descending'    # default
    if (allquadcount[j,1] > 0):
      if ((allquadcount[j,0]/allquadcount[j,1]) > 0.5) and (allquadcount[j,3] > allquadcount[j,5]): 
        orbit = 'Ascending'
    elif (allquadcount[j,1] == 0) and (allquadcount[j,0] > 0) \
       and (allquadcount[j,3] > allquadcount[j,5]):
      orbit = 'Ascending'
    fout.write('%s, %s, %6.2f, %6.2f, %d, %d, %d, %d\n' \
      % (quadname, orbit, allquadcount[j,0], allquadcount[j,1], allquadcount[j,2], allquadcount[j,3], \
      allquadcount[j,4], allquadcount[j,5]))

  ## close output file.  ALL DONE!
  fout.close()
  
  
if __name__ == "__main__":

  main(sys.argv[1], sys.argv[2])

