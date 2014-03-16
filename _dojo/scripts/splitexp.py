import h5py
import os
import json
import tifffile as tif
import numpy as np
import mahotas as mh
import math
from scipy import ndimage

input = json.loads('{"name":"SPLIT","origin":"MGplo","value":{"id":4641,"brush_bbox":[124,167,805,898],"i_js":[[164,807],[162,810],[161,813],[161,817],[161,818],[161,820],[161,823],[161,824],[160,826],[159,828],[157,830],[156,833],[154,837],[154,839],[153,840],[152,842],[151,843],[151,844],[151,846],[151,847],[149,850],[148,854],[146,857],[145,860],[143,863],[143,865],[142,867],[142,868],[141,870],[141,871],[141,873],[139,876],[138,877],[138,880],[135,883],[134,885],[132,888],[132,888],[132,889],[131,891],[130,891],[130,893],[129,893],[129,893]],"z":0,"brush_size":10}}')['value']

# stitch together tile

data_path = os.path.join('/home/d/TMP/MOJO/ac3x75/mojo/images/tiles/w=00000000/z='+str(input["z"]).zfill(8))

images = os.listdir(data_path)
tile = {}
for i in images:

  location = os.path.splitext(i)[0].split(',')
  for l in location:
    l = l.split('=')
    exec(l[0]+'=int("'+l[1]+'")')

  if not x in tile:
    tile[x] = {}
  tile[x][y] = tif.imread(os.path.join(data_path,i))

row = None
first_row = True

# go through rows of each tile
for r in tile.keys():
  column = None
  first_column = True

  for c in tile[r]:
    if first_column:
      column = tile[r][c]
      first_column = False
    else:
      column = np.concatenate((column, tile[r][c]), axis=0)

  if first_row:
    row = column
    first_row = False
  else:
    row = np.concatenate((row, column), axis=1)

tile = row

#
# crop according to bounding box
#
bbox = input['brush_bbox']

sub_tile = tile[bbox[2]:bbox[3],bbox[0]:bbox[1]]

#
# create mask
#
mask = np.zeros((1024,1024),dtype=np.uint8)

bs = input['brush_size']

i_js = input['i_js']

for d in i_js:
  mask[d[1], d[0]] = 255

for i in range(bs):
  mask = mh.morph.dilate(mask)

mask = np.invert(mask)

mask = mask[bbox[2]:bbox[3],bbox[0]:bbox[1]]

mh.imsave('/tmp/mask.tif', mask)
#
# run watershed
#
seeds,n = mh.label(mask)
sizes = mh.labeled.labeled_size(seeds)
too_small = np.where(sizes < 5)
seeds = mh.labeled.remove_regions(seeds, too_small)

distances = mh.stretch(mh.distance(mask > 0))
surface = np.int32(distances.max() - distances)
w = mh.cwatershed(surface, seeds, return_lines=True)
print w[1]
# line[line == True] = 0
# line[line==False] = 255
# print line.astype(np.uint8)
# print line.astype(int)
# mh.imsave('/tmp/lines.tif', line.astype(np.uint8))

mh.imsave('/tmp/ws.tif', w[0])
