#!/bin.env python3
import numpy as np
import os, sys


quad_list = [['descending', 'L15-0112E-1150N'], ['descending', 'L15-0112E-1151N'], 
['descending', 'L15-0112E-1152N'], ['descending', 'L15-0113E-1151N'], 
['descending', 'L15-0113E-1152N'], ['descending', 'L15-0114E-1152N'], 
['descending', 'L15-0115E-1151N'], ['descending', 'L15-0115E-1152N'], 
['descending', 'L15-0115E-1153N'], ['ascending', 'L15-0116E-1151N'], 
['ascending', 'L15-0116E-1153N'], ['ascending', 'L15-0117E-1151N'], 
['ascending', 'L15-0117E-1152N'], ['ascending', 'L15-0117E-1153N'], 
['descending', 'L15-0123E-1148N'], ['descending', 'L15-0123E-1149N'], 
['descending', 'L15-0124E-1147N'], ['descending', 'L15-0124E-1148N'], 
['descending', 'L15-0124E-1149N'], ['descending', 'L15-0124E-1150N'], 
['descending', 'L15-0125E-1147N'], ['descending', 'L15-0125E-1148N'], 
['descending', 'L15-0125E-1149N'], ['descending', 'L15-0125E-1150N'], 
['descending', 'L15-0126E-1147N'], ['descending', 'L15-0126E-1148N'], 
['descending', 'L15-0126E-1149N'], ['descending', 'L15-0127E-1147N'], 
['descending', 'L15-0127E-1148N'], ['descending', 'L15-0128E-1146N'], 
['descending', 'L15-0129E-1146N'], ['descending', 'L15-0129E-1147N'], 
['descending', 'L15-0130E-1144N'], ['descending', 'L15-0130E-1145N'], 
['descending', 'L15-0130E-1146N'], ['descending', 'L15-0130E-1147N'], 
['descending', 'L15-0131E-1144N'], ['descending', 'L15-0131E-1145N'], 
['descending', 'L15-0131E-1146N'], ['descending', 'L15-0131E-1147N'], 
['descending', 'L15-0132E-1143N'], ['descending', 'L15-0132E-1144N'], 
['descending', 'L15-0132E-1145N'], ['descending', 'L15-0132E-1146N'], 
['descending', 'L15-0132E-1147N'], ['descending', 'L15-0133E-1143N'], 
['descending', 'L15-0133E-1144N'], ['descending', 'L15-0133E-1145N'], 
['descending', 'L15-0133E-1146N'], ['descending', 'L15-0134E-1143N'], 
['descending', 'L15-0134E-1144N'], ['descending', 'L15-0134E-1145N'], 
['descending', 'L15-0135E-1143N'], ['descending', 'L15-0135E-1144N'], 
['descending', 'L15-0135E-1145N'], ['descending', 'L15-0136E-1134N'], 
['ascending', 'L15-0136E-1135N'], ['ascending', 'L15-0136E-1136N'], 
['ascending', 'L15-0136E-1137N'], ['ascending', 'L15-0136E-1138N'], 
['ascending', 'L15-0136E-1139N'], ['descending', 'L15-0136E-1144N'], 
['descending', 'L15-0136E-1145N'], ['ascending', 'L15-0137E-1133N'], 
['ascending', 'L15-0137E-1134N'], ['ascending', 'L15-0137E-1135N'], 
['ascending', 'L15-0137E-1136N'], ['ascending', 'L15-0137E-1139N'], 
['ascending', 'L15-0137E-1140N'], ['ascending', 'L15-0137E-1141N'], 
['ascending', 'L15-0138E-1133N'], ['descending', 'L15-0138E-1134N'], 
['descending', 'L15-0138E-1140N'], ['descending', 'L15-0138E-1141N'], 
['descending', 'L15-0139E-1134N'], ['descending', 'L15-0139E-1135N'], 
['descending', 'L15-0139E-1140N'], ['descending', 'L15-0140E-1135N'], 
['descending', 'L15-0140E-1140N'], ['descending', 'L15-0141E-1135N'], 
['descending', 'L15-0141E-1136N'], ['descending', 'L15-0141E-1138N'], 
['descending', 'L15-0141E-1139N'], ['descending', 'L15-0141E-1140N'], 
['descending', 'L15-0142E-1136N'], ['descending', 'L15-0142E-1137N'], 
['descending', 'L15-0142E-1138N'], ['descending', 'L15-0143E-1136N'], 
['descending', 'L15-0143E-1137N'], ['descending', 'L15-0170E-0921N'], 
['descending', 'L15-0170E-0922N'], ['descending', 'L15-0171E-0922N'], 
['descending', 'L15-0171E-0923N'], ['descending', 'L15-0172E-0921N'], 
['descending', 'L15-0172E-0922N'], ['descending', 'L15-0172E-0923N'], 
['descending', 'L15-0173E-0920N'], ['descending', 'L15-0173E-0921N'], 
['descending', 'L15-0173E-0922N'], ['descending', 'L15-0173E-0923N'], 
['descending', 'L15-0174E-0920N'], ['descending', 'L15-0174E-0921N'], 
['descending', 'L15-0174E-0922N'], ['descending', 'L15-0174E-0923N'], 
['descending', 'L15-0175E-0920N'], ['descending', 'L15-0175E-0921N']] 

def tile_orbit_list(tileid):
  orbit = [ x[0] for x in quad_list if x[1] == tileid ]
  if (len(orbit) > 0):
    return orbit[0]
  else:
    return None
