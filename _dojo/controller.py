import h5py
import os
import json
import tifffile as tif
import numpy as np
import mahotas as mh
import math
from scipy import ndimage

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

    #
    # crop according to bounding box
    #
    bbox = values['brush_bbox']

    sub_tile = tile[bbox[2]:bbox[3],bbox[0]:bbox[1]]

    #
    # create mask
    #
    mask = np.zeros((1024,1024),dtype=np.uint8)

    bs = values['brush_size']

    i_js = values['i_js']

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
                
    output = {}
    output['name'] = 'SPLITRESULT'
    output['origin'] = input['origin']
    output['value'] = lines
    self.__websocket.send(json.dumps(output))
