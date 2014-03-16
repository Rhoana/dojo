import h5py
import os
import json
import tifffile as tif
import numpy as np
import mahotas as mh
import math
from scipy import ndimage

# input = json.loads('{"name":"SPLIT","origin":"MGplo","value":{"id":4641,"brush_bbox":[124,167,805,898],"i_js":[[164,807],[162,810],[161,813],[161,817],[161,818],[161,820],[161,823],[161,824],[160,826],[159,828],[157,830],[156,833],[154,837],[154,839],[153,840],[152,842],[151,843],[151,844],[151,846],[151,847],[149,850],[148,854],[146,857],[145,860],[143,863],[143,865],[142,867],[142,868],[141,870],[141,871],[141,873],[139,876],[138,877],[138,880],[135,883],[134,885],[132,888],[132,888],[132,889],[131,891],[130,891],[130,893],[129,893],[129,893]],"z":0,"brush_size":10}}')['value']

input = json.loads('{"name":"SPLIT","origin":"2mkgC","value":{"id":4641,"brush_bbox":[115,160,812,906],"i_js":[[158,812],[157,815],[156,817],[156,817],[156,818],[156,818],[156,819],[156,820],[156,821],[156,822],[156,823],[156,823],[156,824],[156,825],[156,825],[156,826],[156,827],[156,827],[156,828],[156,829],[156,829],[156,830],[156,830],[156,830],[156,831],[156,832],[155,833],[155,835],[155,836],[154,837],[154,837],[154,838],[153,838],[153,839],[153,839],[153,840],[153,840],[152,841],[152,842],[152,842],[151,843],[151,843],[149,845],[148,846],[147,847],[147,847],[147,847],[146,848],[146,848],[145,849],[145,850],[144,850],[144,851],[143,852],[143,852],[143,853],[143,853],[142,854],[141,855],[140,856],[139,857],[139,858],[138,859],[137,861],[137,862],[137,863],[137,863],[137,864],[137,865],[137,865],[137,866],[137,866],[137,866],[138,866],[138,866],[138,867],[138,867],[138,869],[138,869],[138,870],[138,870],[138,870],[138,871],[138,871],[138,872],[138,872],[137,873],[137,873],[136,874],[136,874],[136,875],[136,875],[135,875],[135,875],[134,876],[134,876],[133,877],[132,877],[132,878],[132,878],[132,878],[132,879],[132,880],[132,880],[131,881],[131,882],[130,884],[130,884],[130,885],[130,885],[130,886],[130,886],[129,887],[129,887],[129,888],[129,888],[129,889],[129,889],[128,889],[128,890],[127,891],[127,891],[127,892],[127,892],[127,892],[127,893],[127,893],[126,894],[125,895],[125,896],[124,897],[124,897],[124,897],[123,898],[123,899],[122,900],[121,900],[121,900],[121,900],[119,902],[119,902],[118,902],[118,902],[118,902],[118,903],[118,903]],"z":0,"brush_size":5}}')
input = input['value']
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
mh.imsave('/tmp/box3.tif', sub_tile)
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

# mh.imsave('/tmp/mask.tif', mask)

grad_x = np.gradient(sub_tile)[0]
grad_y = np.gradient(sub_tile)[1]
grad = np.add(np.square(grad_x), np.square(grad_y))
#grad = np.add(np.abs(grad_x), np.abs(grad_y))
grad -= grad.min()
grad /= grad.max()
grad *= 255
grad = grad.astype(np.uint8)

# compute seeds
seeds,_ = mh.label(mask)

# remove small regions
sizes = mh.labeled.labeled_size(seeds)
min_seed_size = 5
too_small = np.where(sizes < min_seed_size)
seeds = mh.labeled.remove_regions(seeds, too_small)


#
# run watershed
#
ws = mh.cwatershed(grad, seeds)

lines_array = np.zeros(ws.shape,dtype=np.uint8)
lines = []

for y in range(ws.shape[0]-1):
  for x in range(ws.shape[1]-1):
    if ws[y,x] != ws[y,x+1]:  
      lines_array[y,x] = 1
      lines.append([x,y])
    if ws[y,x] != ws[y+1,x]:
      lines_array[y,x] = 1
      lines.append([x,y])
            

# line[line == True] = 0
# line[line==False] = 255
# print line.astype(np.uint8)
# print line.astype(int)
# mh.imsave('/tmp/lines.tif', line.astype(np.uint8))

# mh.imsave('/tmp/ws.tif', 80*ws)
