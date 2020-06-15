#!/bin/env python3
from planet import api
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
    
def get_crosstrack_direction(meta):
  epsg = str(meta['properties']['epsg_code'])
  utmproj = pyproj.Proj('epsg:'+epsg)
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
    
def main():
  ## f = open('mosaics_list_20200513.json', 'r')
  f = open('mosaics_list_20200513.json', 'r')
  
  mosdata = json.load(f)
  mosdata['mosaics']
  f.close()
  
  scenedata = []
  percov = []
  iddata = []
  numimgs = []
  client = api.ClientV1()
  
  for rec in mosdata['mosaics']:
    mapname = rec['name']
    if ('descending' not in mapname) and ('ascending' not in mapname):
      continue
    print(mapname)  
    fmap = open(rec['name']+'_map.txt', 'w+')
    subprocess.call(['planet', 'mosaics', 'search', rec['name']], stdout=fmap)
    fmap.seek(0)
    mapdata = json.load(fmap)
    fmap.close()
    numquads = len(mapdata['items'])
    print('Mosaic: %s    Numquads: %d' % (rec['name'], numquads))
    for quadrec in mapdata['items']:
      quadlink = quadrec['_links']['_self']
      r = requests.get(quadlink)
      indivdata = r.json()
      iddata.append(quadrec['id'])
      percov.append(quadrec['percent_covered'])
      numimgs.append(len(indivdata))
      g = requests.get(indivdata['_links']['items'])
      indiv = g.json()
      itemids = get_ids(indiv['items'])
      for item_id in itemids:
        temp = client.get_item("PSScene4Band", item_id).get()
        metadata = json.loads(json.dumps(temp))
        centerx, centery, cross = get_crosstrack_direction(metadata)
        acqdate = dateutil.parser.parse(metadata['properties']['acquired'])
        sunpos = pvlib.solarposition.get_solarposition(acqdate, centery, centerx)
        if (cross < 0.0):
          cross += 180.0
        if (sunpos.azimuth[0] < 0.0):
          sunaz = 180. + sunpos.azimuth[0]
        else:
          sunaz = sunpos.azimuth[0]
        sunzen = sunpos.zenith[0]
        print('   %s, %s, %12.8f, %12.8f, %6.1f, %6.1f, %6.1f' % (quadrec['id'], item_id, centerx, centery, cross, sunzen, sunaz))
    print('')

## (Pdb) results.get()['features']
## [{'_links': {'_self': 'https://api.planet.com/data/v1/item-types/PSScene4Band/items/20180310_032901_1044', 'assets': 'https://api.planet.com/data/v1/item-types/PSScene4Band/items/20180310_032901_1044/assets/', 'thumbnail': 'https://tiles.planet.com/data/v1/item-types/PSScene4Band/items/20180310_032901_1044/thumb'}, '_permissions': ['assets.udm:download', 'assets.analytic:download', 'assets.analytic_xml:download', 'assets.analytic_dn:download', 'assets.analytic_dn_xml:download', 'assets.basic_analytic:download', 'assets.basic_analytic_rpc:download', 'assets.basic_analytic_dn:download', 'assets.basic_analytic_dn_rpc:download', 'assets.basic_analytic_xml:download', 'assets.basic_analytic_dn_xml:download', 'assets.basic_analytic_dn_nitf:download', 'assets.basic_analytic_dn_rpc_nitf:download', 'assets.basic_analytic_dn_xml_nitf:download', 'assets.basic_analytic_nitf:download', 'assets.basic_analytic_rpc_nitf:download', 'assets.basic_analytic_xml_nitf:download', 'assets.basic_udm:download', 'assets.analytic_sr:download'], 'geometry': {'coordinates': [[[96.86043748460656, 17.652781277238184], [97.10047823213063, 17.606845574841426], [97.0852763452143, 17.532745766188874], [96.84476781850219, 17.578682818276306], [96.85735846586421, 17.640410116365047], [96.85789012995211, 17.64030855712588], [96.86043748460656, 17.652781277238184]]], 'type': 'Polygon'}, 'id': '20180310_032901_1044', 'properties': {'acquired': '2018-03-10T03:29:01.038046Z', 'anomalous_pixels': 0, 'cloud_cover': 0, 'columns': 9061, 'epsg_code': 32647, 'ground_control': True, 'gsd': 3.9, 'instrument': 'PS2', 'item_type': 'PSScene4Band', 'origin_x': 271260, 'origin_y': 1953057, 'pixel_resolution': 3, 'provider': 'planetscope', 'published': '2018-03-11T03:01:02.000Z', 'quality_category': 'standard', 'rows': 4515, 'satellite_id': '1044', 'strip_id': '1254035', 'sun_azimuth': 120.4, 'sun_elevation': 50.6, 'updated': '2018-03-11T07:03:41.000Z', 'usable_data': 0, 'view_angle': 0.9}, 'type': 'Feature'}]


## (Pdb) filt = api.filters.string_filter('id', '20180310_032901_1044')
## (Pdb) filt
## {'field_name': 'id', 'type': 'StringInFilter', 'config': ('20180310_032901_1044',)}
## (Pdb) request = api.filters.build_search_request(filt, ['PSScene4Band'])
## (Pdb) results = client.quick_search(request)
## (Pdb) results

  
if __name__ == "__main__":

  main()

##   PLANET_API_KEY = os.getenv('PL_API_KEY')
## 
##   root = os.path.basename(outputdir)
##   if (root == ''):
##     root = os.path.split(os.path.split(outputdir)[0])[1]
##   today = datetime.today()
##   ## today = datetime.today() - timedelta(days=1)
##   logfilename = "/home/dknapp4/hawaii_logs/download_log_"+("%s_%04d%02d%02d.txt" % (root, today.year, today.month, today.day))
##   f = open(logfilename, 'w+')
## 
##   settime1 = datetime(today.year, today.month, today.day, 23, 0, 0, 0, timezone.utc)
##   back1 = timedelta(days=3)
##   yesterday = settime1 - back1
##   timetxt1 = yesterday.isoformat(timespec='minutes')[0:16]
##   timetxt2 = settime1.isoformat(timespec='minutes')[0:16]
## 
##   f.write('Searching for files between %s and %s\n' % (timetxt1, timetxt2))
## 
##   client = api.ClientV1()
## 
##   ## jsonfile1 = '/scratch/dknapp4/Western_Hawaii/NW_Big_Island_Intensive_Study_Area.json'
##   ## jsonfile2 = '/scratch/dknapp4/Western_Hawaii/SW_Big_Island_Intensive_Study_Area.json'
## 
##   with open(jsonfile, 'r') as f2:
##     data = json.load(f2)
##  
##   aoi = data['features'][0]['geometry']
## 
##   query = api.filters.and_filter(api.filters.geom_filter(aoi), \
##     api.filters.date_range('acquired', gt=timetxt1, lt=timetxt2))
##     ## api.filters.range_filter('cloud_cover', lt=0.1), \
## 
##   item_types4 = ['PSScene4Band']
##   request4 = api.filters.build_search_request(query, item_types4)
##   item_types3 = ['PSScene3Band']
##   request3 = api.filters.build_search_request(query, item_types3)
## 
##   results3 = client.quick_search(request3)
##   results4 = client.quick_search(request4)
## 
##   myreps3 = []
##   myreps4 = []
##   list3 = []
##   list4 = []
##   
##   for item in results4.items_iter(limit=100):
##     list4.append(item)
##     myreps4.append(item['id'])
##     if (item['properties']['instrument'] == 'PS2.SD'):
##       f.write(('%s : %s\n') % (item['id'], 'Dove-R'))
##     else:
##       f.write(('%s : %s\n') % (item['id'], 'Dove-Classic'))
## 
##   for item in results3.items_iter(limit=100):
##     ## print(r'%s' % item['id'])
##     myreps3.append(item['id'])
## 
##   if (len(myreps3) > len(myreps4)):
##     diff34 = np.setdiff1d(myreps3, myreps4).tolist()                              
##     f.write("\nPossible 3Band data that could be made to 4Band:")                     
##     ## [ f.write("%s\n" % thisid) for thisid in diff34 ]
##     for thisid in diff34:
##       f.write("%s\n" % thisid)
##   
##   f.write("\n")
## 
##   ## urlform = 'https://api.planet.com/data/v1/item-types/{}/items/{}/assets'
##   ## for myid in myreps4:
##   ##   theassets = client.get_assets(myid).get()
##   ##   if ('analytic_sr' in theassets):
##   ##     activation = client.activate(assets['analytic_sr'])
##   ##     ## wait for activation
##   ##     theassets = client.get_assets(myid).get()
##   ##     callback = api.write_to_file(directory=outputdir, callback=None, overwrite=True)
##   ##     body = client.download(assets['analytic_sr'], callback=callback)
##   ##     body.await()
##   ## resget = requests.get(urlform.format('analytic_sr', myid), auth=HTTPBasicAuth(PLANET_API_KEY, '')) 
##     
##   mydownloader = downloader.create(client, no_sleep=True, astage__size=10, 
##     pstage__size=10, pstage__min_poll_interval=0, dstage__size=2)
## 
##   ## put the results into a regular list
##   ## mylist = []
##   ## for item in list4:
##   ##   item 
##   ##  whole[1]['properties']['instrument'] == 'PS2.SD'
## 
##   f.write(('Starting Download of %d scenes.\n') % len(myreps4))
##   mydownloader.download(results4.items_iter(limit=100), ['udm2'], outputdir)
##   f.write(('Finished with Download of udm2.\n'))
##   mydownloader.download(results4.items_iter(limit=100), ['analytic_sr'], outputdir)
##   f.write(('Finished with Download of analytic_sr.\n'))
##   mydownloader.download(results4.items_iter(limit=100), ['analytic_xml'], outputdir)
##   f.write(('Finished with Download of analytic_xml.\n'))
##   mydownloader.shutdown()
##   f.write(('Downloader has been shut down.\n'))
##   f.close()
##   return( 0 )
## 
