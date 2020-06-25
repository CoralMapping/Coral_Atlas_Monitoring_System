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

def get_ids(items):
  ## indiv['items'][0]['link']
  ## 'https://api.planet.com/data/v1/item-types/PSScene4Band/items/20200429_071805_1008#analytic_sr'
  ids = []
  for item in items:
    thelink = item['link']
    theid = os.path.basename(thelink)
    pos = theid.find('#')
    ids.append(theid[0:pos])
  return ids
    
def find_date(mname):
  baseit = os.path.basename(mname)
  parts = baseit.split('_')
  try:
    datestr = parts[parts.index('to')-1]
  except ValueError:
    datestr = '00000000'
  if (len(datestr) > 8):
    tempstr = datestr.split('-')
    datestr = tempstr.join()
  return datestr 
    
def get_crosstrack_direction(meta):
  epsg = str(meta['properties']['epsg_code'])
  utmproj = pyproj.Proj(init='EPSG:'+epsg)
  coords = meta['geometry']['coordinates'][0]
  if (len(coords[0]) != 2):
    coords = coords[0]
  segdir = []
  seglen = []
  utmcoords = []
  totx = 0.; toty= 0.;
  for j in coords:
    utmx, utmy = utmproj(j[0], j[1])
    utmcoords.append([utmx, utmy])
    totx += j[0]
    toty += j[1]
  centx = totx/len(coords)
  centy = toty/len(coords)
  for k in range(len(utmcoords)-1):
    distx1 = utmcoords[k+1][0] - utmcoords[k][0]
    disty1 = utmcoords[k+1][1] - utmcoords[k][1]
    distx = pow(utmcoords[k+1][0] - utmcoords[k][0], 2)
    disty = pow(utmcoords[k+1][1] - utmcoords[k][1], 2)
    seglen.append(math.sqrt(distx+disty))
    segdir.append(math.degrees(math.atan2(distx1, disty1)))
    index = sorted(range(len(seglen)), key=lambda k: seglen[k])
    azim = segdir[index[-1]]
  return centx, centy, azim
    
def main(ascendingname, descendingname):
  today = datetime.datetime.now().isoformat()[0:19]
  fmosaicsname = 'mosaic_data_'+today+'_map.json'
  fmosaics = open(fmosaicsname, 'w+')
  subprocess.call(['planet', 'mosaics', 'list'], stdout=fmosaics)
  fmosaics.seek(0)
  mosdata = json.load(fmosaics)
  fmosaics.close()
  ## fmosaicsname = "mosaic_data_2020-06-23T11:20:09_map.json"
  ## fmosaics = open(fmosaicsname, 'r')
  ## fmosaics.seek(0)
  ## mosdata = json.load(fmosaics)
  ## fmosaics.close()

  ## mosdata['mosaics']
  
  iddata = []
  numimgs = []
  client = api.ClientV1()
  
  allmosaicnames = [ rec['name'] for rec in mosdata['mosaics'] ]
  if (ascendingname not in allmosaicnames) or (descendingname not in allmosaicnames) :
    print('Mosaic %s not found in currently available mosaics' % (ascendingname))
    print('OR')
    print('Mosaic %s not found in currently available mosaics' % (descendingname))
    return
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
  numquads1 = len(mapdata2['items'])
  quadids1 = [ quad['id'] for quad in mapdata1['items'] ]
  numquads2 = len(mapdata2['items'])
  quadids2 = [ quad['id'] for quad in mapdata2['items'] ]
  allquads = np.unique(np.concatenate((quadids1, quadids2)))
  allquadcount = np.zeros((allquads.shape[0], 6))

  for k,mapstuff in enumerate([mapdata1['items'], mapdata2['items']]):
    for quadrec in mapstuff:
      thisquadname = 'L15-%04dE-%04dN' % (int(quadrec['id'].split('-')[0]),int(quadrec['id'].split('-')[1]))
      index = np.nonzero(np.char.equal(allquads,quadrec['id']))[0][0]
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
      for item_id in itemids:
        try:
          temp = client.get_item("PSScene4Band", item_id).get()
        except planet.api.exceptions.MissingResource:
          print('Resource not found...skipping.')
          continue
        metadata = json.loads(json.dumps(temp))
        centerx, centery, cross = get_crosstrack_direction(metadata)
        acqdate = dateutil.parser.parse(metadata['properties']['acquired'])
        ## cloudcov = metadata['properties']['cloud_cover']
        sunpos = pvlib.solarposition.get_solarposition(acqdate, centery, centerx)
        if (cross < 0.0):
          cross += 180.0
        if (sunpos.azimuth[0] < 0.0):
          sunaz = 180. + sunpos.azimuth[0]
        else:
          sunaz = sunpos.azimuth[0]
        sunzen = sunpos.zenith[0]
        try:
          if (('ascending' in mosaicname) and (abs(sunaz-cross) < 3.0)):
            ## Ascending
            allquadcount[index, 2] += 1
          if (('ascending' in mosaicname) and (abs(sunaz-cross) >= 3.0)):
            ## Ascending
            allquadcount[index, 3] += 1
          if (('descending' in mosaicname) and (abs(sunaz-cross) < 3.0)):
            ## Descending
            allquadcount[index, 4] += 1
          if (('descending' in mosaicname) and (abs(sunaz-cross) >= 3.0)):
            ## Descending
            allquadcount[index, 5] += 1
        except:
          continue
      ## print('   %s, %s, %4d, %12.8f, %12.8f, %6.1f, %6.1f, %6.1f' % (quadrec['id'], item_id, cloudcov, centerx, centery, cross, sunzen, sunaz))

  print('QUADNAME, ASCEEND_PERCOV, DESC_PERCOV, ASC_BAD, ASC_GOOD, DESC_BAD, DESC_GOOD')
  for j in range(len(allquads)):
    quadname = 'L15-%04dE-%04dN' % (int(allquads[j].split('-')[0]), int(allquads[j].split('-')[1]))
    print('%s, %6.2f, %6.2f, %d, %d, %d, %d' % (quadname, allquadcount[j,0], allquadcount[j,1], allquadcount[j,2], allquadcount[j,3], allquadcount[j,4], allquadcount[j,5]))

  
if __name__ == "__main__":

  main(sys.argv[1], sys.argv[2])

