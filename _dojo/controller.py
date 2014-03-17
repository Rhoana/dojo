import h5py
import os
import json
import tifffile as tif
import numpy as np
import mahotas as mh
import math
from scipy import ndimage
from skimage import exposure

class Controller(object):

  def __init__(self, mojo_dir):
    '''
    '''
    self.__websocket = None

    self.__merge_table = {}

    self.__lock_table = {}

    self.__problem_table = []

    self.__users = []

    self.__mojo_dir = mojo_dir
    print mojo_dir

  def handshake(self, websocket):
    '''
    '''
    self.__websocket = websocket

    self.send_welcome()

    # always send the merge table first thing
    self.send_merge_table('SERVER')
    # then the lock table
    self.send_lock_table('SERVER')
    # then the problem table
    self.send_problem_table('SERVER')

    # then send the redraw command
    self.send_redraw('SERVER')


  def send_welcome(self):
    '''
    '''
    output = {}
    output['name'] = 'WELCOME'
    output['origin'] = 'SERVER'
    output['value'] = ''

    self.__websocket.send(json.dumps(output))


  def send_redraw(self, origin):
    '''
    '''
    output = {}
    output['name'] = 'REDRAW'
    output['origin'] = 'SERVER'
    output['value'] = ''

    self.__websocket.send(json.dumps(output))

  def get_merge_table(self):
    '''
    '''
    return self.__merge_table

  def get_lock_table(self):
    '''
    '''
    return self.__lock_table

  def get_problem_table(self):
    '''
    '''
    return self.__problem_table

  def send_merge_table(self, origin):
    '''
    '''

    output = {}
    output['name'] = 'MERGETABLE'
    output['origin'] = origin
    output['value'] = self.get_merge_table()

    self.__websocket.send(json.dumps(output))

  def send_lock_table(self, origin):
    '''
    '''

    output = {}
    output['name'] = 'LOCKTABLE'
    output['origin'] = origin
    output['value'] = self.get_lock_table()

    self.__websocket.send(json.dumps(output))

  def send_problem_table(self, origin):
    '''
    '''

    output = {}
    output['name'] = 'PROBLEMTABLE'
    output['origin'] = origin
    output['value'] = self.get_problem_table()

    self.__websocket.send(json.dumps(output))


  def on_message(self, message):
    '''
    '''
    print message
    input = json.loads(message)

    if input['name'] == 'WELCOME':

      self.__users.append(input['origin'])

    elif input['name'] == 'MERGETABLE':
      self.__merge_table = input['value']

      self.send_merge_table(input['origin'])

      self.send_redraw(input['origin'])

    elif input['name'] == 'LOCKTABLE':
      self.__lock_table = input['value']

      self.send_lock_table(input['origin'])

      self.send_redraw(input['origin'])

    elif input['name'] == 'PROBLEMTABLE':
      self.__problem_table = input['value']

      self.send_problem_table(input['origin'])

    elif input['name'] == 'LOG':
      # just echo it
      input['id'] = self.__users.index(input['origin'])
      self.__websocket.send(json.dumps(input))

    elif input['name'] == 'MOUSEMOVE':
      # just echo it
      input['id'] = self.__users.index(input['origin'])
      self.__websocket.send(json.dumps(input))

    elif input['name'] == 'SPLIT':
      self.split(input)

    elif input['name'] == 'FINALIZESPLIT':
      self.finalize_split(input)

  def finalize_split(self, input):
    '''
    '''
    print input


  def split(self, input):
    '''
    TODO: move to separate class
    '''
    values = input['value']
    data_path = self.__mojo_dir + '/images/tiles/w=00000000/z='+str(values["z"]).zfill(8)

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



    data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

    images = os.listdir(data_path)
    segtile = {}
    for i in images:

      location = os.path.splitext(i)[0].split(',')
      for l in location:
        l = l.split('=')
        exec(l[0]+'=int("'+l[1]+'")')

      if not x in segtile:
        segtile[x] = {}

      hdf5_file = h5py.File(os.path.join(data_path,i))
      list_of_names = []
      hdf5_file.visit(list_of_names.append)
      image_data = hdf5_file[list_of_names[0]].value
      hdf5_file.close()

      segtile[x][y] = image_data

    row2 = None
    first_row = True

    # go through rows of each tile
    for r in segtile.keys():
      column = None
      first_column = True

      for c in segtile[r]:
        if first_column:
          column = segtile[r][c]
          first_column = False
        else:
          column = np.concatenate((column, segtile[r][c]), axis=0)

      if first_row:
        row2 = column
        first_row = False
      else:
        row2 = np.concatenate((row2, column), axis=1)

    segmentation = row2


    label_id = values['id']




    #
    # crop according to bounding box
    #
    bbox = values['brush_bbox']

    sub_tile = tile[bbox[2]:bbox[3],bbox[0]:bbox[1]]
    seg_sub_tile = segmentation[bbox[2]:bbox[3],bbox[0]:bbox[1]]

    mh.imsave('/tmp/dojobox.tif', sub_tile);

    sub_tile = mh.gaussian_filter(sub_tile, 1).astype(np.uint8) # gaussian filter
    # sub_tile = (255 * exposure.equalize_hist(sub_tile)).astype(np.uint8) # enhance contrast


    brush_mask = np.zeros((1024,1024),dtype=bool)
    brush_size = values['brush_size']

    i_js = values['i_js']

    for c in i_js:
      brush_mask[c[1],c[0]-math.floor(brush_size/2)] = True
      brush_mask[c[1],c[0]+math.floor(brush_size/2)] = True
        
    brush_mask = brush_mask[bbox[2]:bbox[3],bbox[0]:bbox[1]]
        
    for i in range(brush_size):
        brush_mask = mh.morph.dilate(brush_mask)

    brush_image = np.copy(sub_tile)
    brush_image[~brush_mask] = 0



    outside_brush_mask = np.copy(~brush_mask)
    for i in range(brush_size / 2):
        outside_brush_mask = mh.morph.dilate(outside_brush_mask)

    brush_boundary_mask = brush_mask & outside_brush_mask

    seeds,n = mh.label(brush_boundary_mask)

    print n

    # remove small regions
    sizes = mh.labeled.labeled_size(seeds)
    min_seed_size = 5
    too_small = np.where(sizes < min_seed_size)
    seeds = mh.labeled.remove_regions(seeds, too_small).astype(np.uint8)


    #
    # run watershed
    #
    ws = mh.cwatershed(brush_image.max() - brush_image, seeds)

    lines_array = np.zeros(ws.shape,dtype=np.uint8)
    lines = []

    for y in range(ws.shape[0]-1):
      for x in range(ws.shape[1]-1):
        if ws[y,x] != ws[y,x+1] and seg_sub_tile[y,x] == label_id:  
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])
        if ws[y,x] != ws[y+1,x] and seg_sub_tile[y,x] == label_id:
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])

    for y in range(1,ws.shape[0]):
      for x in range(1,ws.shape[1]):
        if ws[y,x] != ws[y,x-1] and seg_sub_tile[y,x] == label_id:  
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])
        if ws[y,x] != ws[y-1,x] and seg_sub_tile[y,x] == label_id:
          lines_array[y,x] = 1
          #lines_array[y-1,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])          
                
    output = {}
    output['name'] = 'SPLITRESULT'
    output['origin'] = input['origin']
    output['value'] = lines
    self.__websocket.send(json.dumps(output))

