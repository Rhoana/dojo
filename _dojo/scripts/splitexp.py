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


# crop according to bounding box
bbox = input['brush_bbox']

sub_tile = tile[bbox[2]:bbox[3],bbox[0]:bbox[1]]

# create mask
mask = np.zeros((1024,1024),dtype=np.uint8)
mask2 = np.zeros((1024,1024),dtype=np.uint8)
# print tile.shape
bs = input['brush_size']

i_js = input['i_js']

for c in i_js:
  x = c[0]
  y = c[1]
  mask[y,x-math.floor(bs/2)] = 255
  mask[y,x+math.floor(bs/2)] = 255

for d in i_js:
  mask2[d[1], d[0]] = 255

mask2 = mh.morph.dilate(mask2)
mask2 = mh.morph.dilate(mask2)
mask2 = mh.morph.dilate(mask2)
mask2 = mh.morph.dilate(mask2)
mask2 = mh.morph.dilate(mask2)
mask2 = mh.morph.dilate(mask2)
mask2 = mh.morph.dilate(mask2)
mask2 = mh.morph.dilate(mask2)
mask2 = mh.morph.dilate(mask2)
mask2 = mh.morph.dilate(mask2)
# mask2 = mh.morph.erode(mask2)





# mask2 = mh.gaussian_filter(mask2,4)

mask2 = np.invert(mask2)

# print bbox
mask = mask[bbox[2]:bbox[3],bbox[0]:bbox[1]]
# mask2 = mask2[bbox[2]:bbox[3],bbox[0]:bbox[1]]


# new_sub_tile = np.copy(sub_tile)
# new_sub_tile[mask2 == 0] = 0

# grad_x = np.gradient(new_sub_tile)
# # grad_y = np.gradient(new_sub_tile,1)

# grad = np.add(np.square(grad_x[0]), np.square(grad_x[1]))

# grad /= np.max(grad)
# grad *= 255
# print grad.shape

# mh.imsave('/tmp/grad.tif', grad.astype(np.uint8))

# # mask = mask[100:200,800:900]
# mh.imsave('/tmp/mask.tif', mask)
mh.imsave('/tmp/mask2.tif', mask2)

mh.imsave('/tmp/box.tif', sub_tile)
# mh.imsave('/tmp/box2.tif', new_sub_tile)



seeds,n = mh.label(mask2)
sizes = mh.labeled.labeled_size(seeds)
print sizes
too_small = np.where(sizes < 5)
seeds = mh.labeled.remove_regions(seeds, too_small)
# sizes = mh.labeled.labeled_size(seeds)
# im = np.zeros((mask.shape[0],mask.shape[1],3),dtype=np.uint8)
# im[seeds==0] = (255,0,0)
# im[seeds==1] = (0,255,0)
# im[seeds==3] = (0,0,255)
# mh.imsave('/tmp/seeds.tif', 125*seeds.astype(np.uint8))
# mh.imsave('/tmp/im.tif', im)

# distances = mh.stretch(mh.distance(seeds > 0))
# surface = np.int32(distances.max() - distances)
# w = mh.cwatershed(grad.astype(np.uint8), seeds)

# print np.unique(new_sub_tile)

# seeds,_ = mh.label(new_sub_tile < 50)
# seeds,_ = mh.label(mask2)

# gradient = ndimage.morphology.morphological_gradient(new_sub_tile, size=(3,3))
# gradient = gradient.astype(np.uint8)



mh.imsave('/tmp/seeds.tif', 50*seeds.astype(np.uint8))

w = mh.cwatershed(tile, seeds)


# seeds = new_sub_tile[np.where(new_sub_tile < 10)]

# seeds,n = mh.label(seeds)
# print n


# w = mh.cwatershed(new_sub_tile, seeds)

mh.imsave('/tmp/ws.tif', w)

# load tile
# tile_file = os.path.join(self.__mojo_dir, self.__sub_dir, 'tiles', 'w='+str(zoomlevel).zfill(8), 'z='+slice_number.zfill(8), 'y='+tile_y.zfill(8)+','+'x='+tile_x.zfill(8)+'.hdf5')