import json
import h5py
import os, errno
import numpy as np
import mahotas as mh

input = json.loads('{"name":"FINALIZESPLIT","origin":"pBAVI","value":{"id":4641,"line":[[153,803],[153,804],[153,805],[153,806],[153,807],[154,807],[154,808],[155,808],[155,809],[155,810],[156,810],[156,811],[157,811],[157,812],[158,812],[158,813],[158,814],[158,815],[158,816],[158,817],[158,818],[158,818],[157,819],[157,819],[156,820],[156,821],[156,821],[155,822],[155,823],[155,824],[155,825],[155,826],[155,827],[156,827],[156,828],[157,828],[157,829],[158,829],[158,830],[158,831],[158,832],[158,832],[154,833],[155,833],[156,833],[157,833],[157,833],[153,834],[153,834],[152,835],[152,835],[151,836],[151,837],[151,837],[150,838],[150,839],[150,840],[150,840],[149,841],[149,842],[149,843],[149,844],[149,845],[149,845],[148,846],[148,847],[148,847],[147,848],[147,848],[146,849],[146,850],[146,850],[145,851],[145,851],[144,852],[144,852],[143,853],[143,854],[143,854],[142,855],[142,856],[142,856],[140,857],[141,857],[141,857],[139,858],[139,858],[138,859],[138,859],[137,860],[137,861],[137,862],[137,863],[137,864],[138,864],[138,865],[138,866],[138,867],[138,868],[138,869],[138,870],[138,870],[137,871],[137,872],[137,872],[135,873],[136,873],[136,873],[134,874],[134,874],[133,875],[133,876],[133,876],[132,877],[132,878],[132,879],[132,879],[131,880],[131,881],[131,882],[131,882],[130,883],[130,884],[130,885],[130,886],[130,887],[130,887],[129,888],[129,889],[129,889],[128,890],[128,891],[128,891],[127,892],[127,893],[154,803],[154,803],[154,804],[154,805],[154,806],[154,807],[154,808],[155,808],[155,809],[156,809],[156,810],[156,811],[157,811],[157,812],[158,812],[158,813],[159,813],[159,814],[159,815],[159,816],[159,817],[159,818],[158,819],[158,819],[157,820],[157,820],[157,821],[156,822],[156,822],[156,823],[156,824],[156,825],[156,826],[156,827],[156,828],[157,828],[157,829],[158,829],[158,830],[159,830],[159,831],[159,832],[158,833],[158,833],[154,834],[154,834],[155,834],[156,834],[157,834],[153,835],[153,835],[152,836],[152,836],[152,837],[151,838],[151,838],[151,839],[151,840],[150,841],[150,841],[150,842],[150,843],[150,844],[150,845],[149,846],[149,846],[149,847],[148,848],[148,848],[147,849],[147,849],[147,850],[146,851],[146,851],[145,852],[145,852],[144,853],[144,853],[144,854],[143,855],[143,855],[143,856],[142,857],[142,857],[140,858],[140,858],[141,858],[139,859],[139,859],[138,860],[138,860],[138,861],[138,862],[138,863],[138,864],[138,865],[139,865],[139,866],[139,867],[139,868],[139,869],[139,870],[138,871],[138,871],[138,872],[137,873],[137,873],[135,874],[135,874],[136,874],[134,875],[134,875],[134,876],[133,877],[133,877],[133,878],[133,879],[132,880],[132,880],[132,881],[132,882],[131,883],[131,883],[131,884],[131,885],[131,886],[131,887],[130,888],[130,888],[130,889],[129,890],[129,890],[129,891],[128,892],[128,892]],"z":0,"click":[104,855],"bbox":[122,164,792,901]}}')['value']




data_path = os.path.join('/home/d/TMP/MOJO/ac3x75/mojo/ids/tiles/w=00000000/z='+str(input["z"]).zfill(8))

images = os.listdir(data_path)
tile = {}
for i in images:

  location = os.path.splitext(i)[0].split(',')
  for l in location:
    l = l.split('=')
    exec(l[0]+'=int("'+l[1]+'")')

  if not x in tile:
    tile[x] = {}

  hdf5_file = h5py.File(os.path.join(data_path,i))
  list_of_names = []
  hdf5_file.visit(list_of_names.append)
  image_data = hdf5_file[list_of_names[0]].value
  hdf5_file.close()

  tile[x][y] = image_data

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
label_id = input['id']
i_js = input['line']
bbox = input['bbox']
click = input['click']

s_tile = np.zeros(tile.shape)

s_tile[tile == label_id] = 1

#mh.imsave('/tmp/seg.tif', s_tile.astype(np.uint8))


for c in i_js:
  s_tile[c[1], c[0]] = 0

label_image,n = mh.label(s_tile)

if (n!=3):
  print 'ERROR',n

# check which label was selected
selected_label = label_image[click[1], click[0]]

for c in i_js:
  label_image[c[1], c[0]] = selected_label # the line belongs to the selected label


mh.imsave('/tmp/seg2.tif', 10*label_image.astype(np.uint8))


# update the segmentation data

new_id = 6184


label_image[label_image == 1] = 0 # should be zero then
label_image[label_image == 2] = new_id - label_id

tile = np.add(tile, label_image).astype(np.uint32)


#mh.imsave('/tmp/newtile.tif', tile.astype(np.uint32))

# split tile and save as hdf5
x0y0 = tile[0:512,0:512]
x1y0 = tile[0:512,512:1024]
x0y1 = tile[512:1024,0:512]
x1y1 = tile[512:1024,512:1024]

output_folder = '/tmp/dojo/ids/tiles/w=00000000/z='+str(input["z"]).zfill(8)+'/'
try:
  os.makedirs(output_folder)
except OSError as exc: # Python >2.5
  if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
    pass
  else: raise

h5f = h5py.File(output_folder+'y=00000000,x=00000000.hdf5', 'w')
h5f.create_dataset('dataset_1', data=x0y0)
h5f.close()

h5f = h5py.File(output_folder+'y=00000001,x=00000000.hdf5', 'w')
h5f.create_dataset('dataset_1', data=x0y1)
h5f.close()

h5f = h5py.File(output_folder+'y=00000000,x=00000001.hdf5', 'w')
h5f.create_dataset('dataset_1', data=x1y0)
h5f.close()

h5f = h5py.File(output_folder+'y=00000001,x=00000001.hdf5', 'w')
h5f.create_dataset('dataset_1', data=x1y1)
h5f.close()









# 1. threshold for id

# 
