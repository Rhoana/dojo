import cv2
import glob
import h5py
import os, errno
import json
import tifffile as tif
import numpy as np
import mahotas as mh
import math
import shutil
from scipy import ndimage
from skimage import exposure

class Controller(object):

  def __init__(self, mojo_dir, out_dir, tmp_dir, database, dojoserver):


    self.__websocket = None

    self.__mojo_dir = mojo_dir

    self.__mojo_tmp_dir = tmp_dir

    self.__mojo_out_dir = out_dir

    self.__database = database

    self.__users = []

    self.__problem_table = []

    self.__new_merge_table = {}

    self.__old_lock_table = {'0':True}

    self.__hard_merge_table = self.__database._merge_table

    self.__lock_table = self.__database._lock_table

    self.__dojoserver = dojoserver

    self.__actions = {}

    if self.__database:
      self.__largest_id = self.__database.get_largest_id()
    else:
      self.__largest_id = 0

    self.__split_count = 0

  def handshake(self, websocket):

    self.__websocket = websocket

    self.send_welcome()

  def send_welcome(self):

    output = {}
    output['name'] = 'WELCOME'
    output['origin'] = 'SERVER'
    output['value'] = ''

    self.__websocket.send(json.dumps(output))

  def send_orphans(self):

    if not self.__database:
      return

    output = {}
    output['name'] = 'ORPHANS'
    output['origin'] = 'SERVER'
    output['value'] = str(self.__database.get_orphans())

    self.__websocket.send(json.dumps(output))

    output = {}
    output['name'] = 'POTENTIAL_ORPHANS'
    output['origin'] = 'SERVER'
    output['value'] = str(self.__database.get_potential_orphans())

    self.__websocket.send(json.dumps(output))

  def send_redraw(self, origin):

    output = {}
    output['name'] = 'REDRAW'
    output['origin'] = 'SERVER'
    output['value'] = ''

    self.__websocket.send(json.dumps(output))

  def get_hard_merge_table(self):

    return self.__hard_merge_table

  def get_problem_table(self):

    return self.__problem_table

  def send_new_merge_table(self, origin):


    output = {}
    output['name'] = 'MERGETABLE'
    output['origin'] = origin
    output['value'] = self.__new_merge_table

    self.__websocket.send(json.dumps(output))

  def send_undo_merge(self, origin, ids):

    output = {}
    output['name'] = 'UNDO_MERGE_GROUP'
    output['origin'] = origin
    output['value'] = ids
    self.__websocket.send(json.dumps(output))

  def send_redo_merge(self, origin, values):

    output = {}
    output['name'] = 'REDO_MERGE_GROUP'
    output['origin'] = origin
    output['value'] = values

    self.__websocket.send(json.dumps(output))

  def send_lock_table(self, origin):


    output = {}
    output['name'] = 'LOCKTABLE'
    output['origin'] = origin
    output['value'] = self.__lock_table

    self.__websocket.send(json.dumps(output))

  def send_problem_table(self, origin):


    output = {}
    output['name'] = 'PROBLEMTABLE'
    output['origin'] = origin
    output['value'] = self.get_problem_table()

    self.__websocket.send(json.dumps(output))

  def send_unblock(self, origin):


    output = {}
    output['name'] = 'UNBLOCK'
    output['origin'] = origin
    output['value'] = ''

    self.__websocket.send(json.dumps(output))

  def on_message(self, message):


    input = json.loads(message)

    if input['name'] == 'WELCOME':

      self.__users.append(input['origin'])

      # always send the merge table first thing
      self.send_new_merge_table(input['origin'])
      # then the lock table
      self.send_lock_table(input['origin'])
      # then the problem table
      self.send_problem_table(input['origin'])
      # and the orphans
      self.send_orphans()

      self.send_unblock(input['origin'])

      # then send the redraw command
      self.send_redraw('SERVER')

    elif input['name'] == 'MERGETABLE_SUBSET':
      merge_table_subset = input['value']
      for m in merge_table_subset:
        self.__new_merge_table[m] = merge_table_subset[m]

      input['value'] = self.__new_merge_table
      self.send_new_merge_table(input['origin'])

      self.send_redraw(input['origin'])

    elif input['name'] == 'LOCKTABLE':
      new_locks = dict((int(k), v) for k, v in input['value'].iteritems())
      old_locks = self.__lock_table.viewkeys() - new_locks.viewkeys()
      old_locks = old_locks | self.__old_lock_table.viewkeys()
      self.__old_lock_table = dict((k,True) for k in old_locks)

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

    elif input['name'] == 'ADJUST':
      print 'Not Adjusted'

    elif input['name'] == 'SAVE':
      input['name'] = 'SAVING'
      input['origin'] = 'SERVER'
      self.__websocket.send(json.dumps(input))
      self.save(input)

    elif input['name'] == 'ACTION':
      self.add_action(input)

    elif input['name'] == 'UNDO':
      self.undo_action(input)

    elif input['name'] == 'REDO':
      self.redo_action(input)

    elif input['name'] == 'UPDATE_ORPHAN':
      self.update_orphan(input)

  def add_action(self, input):

    values = list(input['value'])
    current_action = values[0]
    value = values[1]
    username = input['origin']

    # check if we have an action stack for this user
    if not username in self.__actions:
      self.__actions[username] = []

    if current_action < len(self.__actions[username]) - 1:
      # remove all actions from the last undo'ed one to the current
      self.__actions[username] = self.__actions[username][0:current_action+1]

    self.__actions[username].append(value)

    #
    # send the action index
    #
    output = {}
    output['name'] = 'CURRENT_ACTION'
    output['origin'] = username
    output['value'] = len(self.__actions[username]) - 1
    self.__websocket.send(json.dumps(output))

  def undo_action(self, input):

    value = input['value']
    username = input['origin']

    if username in self.__actions:
      # actions available
      action = self.__actions[username][value]

      #
      # undo merge and split
      #
      if action['type'] == 'MERGE_GROUP':

        ids = action['value'][0]

        for i in ids:

          key = str(i)

          if key in self.__new_merge_table:
            del self.__new_merge_table[key]
          else:
            # this was already undo'ed before
            pass

        self.send_undo_merge('SERVER', ids)
        self.send_redraw('SERVER')

      elif action['type'] == 'SPLIT':

        z = action['value'][0]
        bb = action['value'][1]
        old_area = action['value'][2]
        new_area = action['value'][3]

        x_tiles = range((bb[0]//512), (((bb[2]-1)//512) + 1))
        y_tiles = range((bb[1]//512), (((bb[3]-1)//512) + 1))

        print x_tiles, y_tiles, bb

        tile_dict = {} # here this is the segmentation

        for x in x_tiles:
          for y in y_tiles:

            if not x in tile_dict:
              tile_dict[x] = {}

            i = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_image().get_input_format()

            s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_segmentation().get_input_format()

            # tile[x][y] = cv2.imread(os.path.join(data_path,i),0)

            # try the temporary data first
            ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)

            if not os.path.exists(os.path.join(ids_data_path,s)):
              ids_data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)

            # print os.path.join(ids_data_path,s)

            hdf5_file = h5py.File(os.path.join(ids_data_path,s))
            list_of_names = []
            hdf5_file.visit(list_of_names.append)
            image_data = hdf5_file[list_of_names[0]].value
            hdf5_file.close()

            tile_dict[x][y] = image_data

        # go through rows of each tile and segmentation
        row_val = self.tile_iter(tile_dict)

        #
        # NOW REPLACE THE PIXEL DATA
        #
        bbox_relative = np.array(bb)

        #
        # but take offset of tile into account
        #
        offset_x = x_tiles[0]*512
        offset_y = y_tiles[0]*512

        bbox_relative[0] -= offset_x
        bbox_relative[1] -= offset_y
        bbox_relative[2] -= offset_x
        bbox_relative[3] -= offset_y

        print row_val.shape

        row_val[bbox_relative[1]:bbox_relative[3],bbox_relative[0]:bbox_relative[2]] = old_area

        # now create all zoomlevels
        max_zoomlevel = self.__dojoserver.get_segmentation().get_max_zoomlevel()

        target_i = 512*x_tiles[0]
        target_j = 512*y_tiles[0]
        target_width = row_val.shape[1]
        target_height = row_val.shape[0]

        for w in range(0, max_zoomlevel+1):

          output_folder = self.__mojo_tmp_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(z).zfill(8)+'/'

          try:
            os.makedirs(output_folder)
          except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
              pass
            else: raise

          if w!=0:
            tile = ndimage.interpolation.zoom(tile, .5, order=0, mode='nearest')

          print '='*80
          print 'W', w

          # find tiles
          x_tiles = range((target_i//512), (((target_i + target_width-1)//512) + 1))
          y_tiles = range((target_j//512), (((target_j + target_height-1)//512) + 1))

          print 'TILES', x_tiles, y_tiles

          tile_width = 0
          pixel_written_x = 0

          for i,x in enumerate(x_tiles):

              # let's grab the pixel coordinate of all tiles of this column
              tile_x = x*512

              # now the offset in x for this column
              if (i==0):
                  offset_x = target_i - tile_x + i*512
              else:
                  offset_x = 0

              pixel_written_y = 0

              for j,y in enumerate(y_tiles):

                  #
                  # load old tile
                  #

                  s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.hdf5'

                  # try the temporary data first
                  ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(z).zfill(8)

                  if not os.path.exists(os.path.join(ids_data_path,s)):
                    ids_data_path = self.__mojo_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(z).zfill(8)

                  # print os.path.join(ids_data_path,s)

                  hdf5_file = h5py.File(os.path.join(ids_data_path,s))
                  list_of_names = []
                  hdf5_file.visit(list_of_names.append)
                  image_data = hdf5_file[list_of_names[0]].value
                  hdf5_file.close()

                  # let's grab the pixel coordinate of this tile
                  tile_y = y*512

                  if (j==0):
                      offset_y = target_j - tile_y + j*512
                  else:
                      offset_y = 0

                  tile_width = min(512-offset_x, target_width-pixel_written_x)
                  tile_height = min(512-offset_y, target_height-pixel_written_y)

                  print 'pixel X,Y', tile_x, tile_y
                  print 'copying', pixel_written_y,':',pixel_written_y+tile_height,',',pixel_written_x,':',pixel_written_x+tile_width
                  print '     to', offset_y,':',offset_y+tile_height,',', offset_x,':',offset_x+tile_width

                  image_data[offset_y:offset_y+tile_height,offset_x:offset_x+tile_width] = tile[pixel_written_y:pixel_written_y+tile_height,pixel_written_x:pixel_written_x+tile_width]

                  hdf5filename = output_folder+s
                  h5f = h5py.File(hdf5filename, 'w')
                  h5f.create_dataset('dataset_1', data=image_data)
                  h5f.close()

                  print 'written', hdf5filename

                  pixel_written_y += tile_height

              pixel_written_x += tile_width



          # update target values
          target_i /= 2
          target_j /= 2
          target_width /= 2
          target_height /= 2

        # send reload event
        output = {}
        output['name'] = 'HARD_RELOAD'
        output['origin'] = 'SERVER'
        output['value'] = {'z':z, 'full_bbox':str(bb)}
        # print output
        self.__websocket.send(json.dumps(output))

      # decrease value
      value = max(0, value-1)

    #
    # send the action index
    #
    output = {}
    output['name'] = 'CURRENT_ACTION'
    output['origin'] = username
    output['value'] = value
    self.__websocket.send(json.dumps(output))

  def redo_action(self, input):

    value = input['value']
    username = input['origin']

    if username in self.__actions:

      # actions available
      action = self.__actions[username][value]
      # print 'Redoing', action

      #
      # redo merge
      #
      if action['type'] == 'MERGE':

        print 'DEPRECATED'

      elif action['type'] == 'MERGE_GROUP':

        ids = action['value'][0]

        for i in ids:

          if i == action['value'][1]:
            # avoid GPU crash
            continue

          key = str(i)

          self.__new_merge_table[key] = action['value'][1]

        self.send_redo_merge('SERVER', action['value'])
        self.send_redraw('SERVER')

      elif action['type'] == 'SPLIT':

        z = action['value'][0]
        bb = action['value'][1]
        old_area = action['value'][2]
        new_area = action['value'][3]

        x_tiles = range((bb[0]//512), (((bb[2]-1)//512) + 1))
        y_tiles = range((bb[1]//512), (((bb[3]-1)//512) + 1))

        print x_tiles, y_tiles, bb

        tile_dict = {} # here this is the segmentation

        for x in x_tiles:
          for y in y_tiles:

            if not x in tile_dict:
              tile_dict[x] = {}

            i = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_image().get_input_format()

            s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_segmentation().get_input_format()

            # try the temporary data first
            ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)

            if not os.path.exists(os.path.join(ids_data_path,s)):
              ids_data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)

            hdf5_file = h5py.File(os.path.join(ids_data_path,s))
            list_of_names = []
            hdf5_file.visit(list_of_names.append)
            image_data = hdf5_file[list_of_names[0]].value
            hdf5_file.close()

            tile_dict[x][y] = image_data

        # go through rows of each tile and segmentation
        row_val = self.tile_iter(tile_dict)

        #
        # NOW REPLACE THE PIXEL DATA
        #
        bbox_relative = np.array(bb)

        #
        # but take offset of tile into account
        #
        offset_x = x_tiles[0]*512
        offset_y = y_tiles[0]*512

        bbox_relative[0] -= offset_x
        bbox_relative[1] -= offset_y
        bbox_relative[2] -= offset_x
        bbox_relative[3] -= offset_y

        row_val[bbox_relative[1]:bbox_relative[3],bbox_relative[0]:bbox_relative[2]] = new_area

        # now create all zoomlevels
        max_zoomlevel = self.__dojoserver.get_segmentation().get_max_zoomlevel()

        target_i = 512*x_tiles[0]
        target_j = 512*y_tiles[0]
        target_width = row_val.shape[1]
        target_height = row_val.shape[0]

        for w in range(0, max_zoomlevel+1):

          output_folder = self.__mojo_tmp_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(z).zfill(8)+'/'

          try:
            os.makedirs(output_folder)
          except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
              pass
            else: raise

          if w!=0:
            tile = ndimage.interpolation.zoom(tile, .5, order=0, mode='nearest')

          print '='*80
          print 'W', w

          # find tiles
          x_tiles = range((target_i//512), (((target_i + target_width-1)//512) + 1))
          y_tiles = range((target_j//512), (((target_j + target_height-1)//512) + 1))

          print 'TILES', x_tiles, y_tiles

          tile_width = 0
          pixel_written_x = 0


          for i,x in enumerate(x_tiles):

              # let's grab the pixel coordinate of all tiles of this column
              tile_x = x*512

              # now the offset in x for this column
              if (i==0):
                  offset_x = target_i - tile_x + i*512
              else:
                  offset_x = 0

              pixel_written_y = 0

              for j,y in enumerate(y_tiles):

                  #
                  # load old tile
                  #

                  s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.hdf5'

                  # try the temporary data first
                  ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(z).zfill(8)

                  if not os.path.exists(os.path.join(ids_data_path,s)):
                    ids_data_path = self.__mojo_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(z).zfill(8)

                  # print os.path.join(ids_data_path,s)

                  hdf5_file = h5py.File(os.path.join(ids_data_path,s))
                  list_of_names = []
                  hdf5_file.visit(list_of_names.append)
                  image_data = hdf5_file[list_of_names[0]].value
                  hdf5_file.close()

                  # let's grab the pixel coordinate of this tile
                  tile_y = y*512

                  if (j==0):
                      offset_y = target_j - tile_y + j*512
                  else:
                      offset_y = 0

                  tile_width = min(512-offset_x, target_width-pixel_written_x)
                  tile_height = min(512-offset_y, target_height-pixel_written_y)

                  print 'pixel X,Y', tile_x, tile_y
                  print 'copying', pixel_written_y,':',pixel_written_y+tile_height,',',pixel_written_x,':',pixel_written_x+tile_width
                  print '     to', offset_y,':',offset_y+tile_height,',', offset_x,':',offset_x+tile_width

                  image_data[offset_y:offset_y+tile_height,offset_x:offset_x+tile_width] = tile[pixel_written_y:pixel_written_y+tile_height,pixel_written_x:pixel_written_x+tile_width]

                  hdf5filename = output_folder+s
                  h5f = h5py.File(hdf5filename, 'w')
                  h5f.create_dataset('dataset_1', data=image_data)
                  h5f.close()

                  print 'written', hdf5filename

                  pixel_written_y += tile_height

              pixel_written_x += tile_width



          # update target values
          target_i /= 2
          target_j /= 2
          target_width /= 2
          target_height /= 2

        # send reload event
        output = {}
        output['name'] = 'HARD_RELOAD'
        output['origin'] = 'SERVER'
        output['value'] = {'z':z, 'full_bbox':str(bb)}
        # print output
        self.__websocket.send(json.dumps(output))

      # increase value
      value = min(len(self.__actions[username])-1, value+1)

    #
    # send the action index
    #
    output = {}
    output['name'] = 'CURRENT_ACTION'
    output['origin'] = username
    output['value'] = value
    self.__websocket.send(json.dumps(output))

  def update_orphan(self, input):

    index = input['value']['current_orphan'];
    orphan = input['value']['orphan'];

    self.__database.get_orphans()[index] = orphan;

    self.send_orphans()

  def save(self, input):

    print 'SAVING..'
    self.__actions = {}
    for username in self.__actions:
      # empty user actions
      output = {}
      output['value'] = 0
      output['origin'] = username
      output['name'] = 'CURRENT_ACTION'
      self.__websocket.send(json.dumps(output))


    for i in self.__new_merge_table:
      self.__database.insert_merge(i, self.__new_merge_table[i])
      # self.__database.store()

    print 'STORED MERGE TABLE'

    # print self.__lock_table
    for i in self.__lock_table:
      if i=='0':
        continue
      self.__database.insert_lock(i)
      # self.__database.store()

    for i in self.__old_lock_table:
      if i=='0':
        continue
      self.__database.remove_lock(i)

    print 'STORED LOCK TABLE'

    self.__database.store()

    print 'ALL STORED'

    # re-harden updated merge table from database
    self.__database._merge_table = self.__database.get_merge_table()
    self.__hard_merge_table = self.__database._merge_table

    print 'Splits', self.__split_count
    print 'All saved! Yahoo!'

    z = 0
    bb = [0, 0, 512, 512]
    # send reload event
    output = {}
    output['name'] = 'HARD_RELOAD'
    output['origin'] = 'SERVER'
    output['value'] = {'z':z, 'full_bbox':str(bb)}
    # print output
    self.__websocket.send(json.dumps(output))

    # ping back
    output = {}
    output['name'] = 'SAVED'
    output['origin'] = 'SERVER'
    output['value'] = {}
    if self.__websocket:
      self.__websocket.send(json.dumps(output))

    # send merge table
    self.__new_merge_table = {}
    self.send_new_merge_table('SERVER')

  def finalize_split(self, input):


    values = input['value']

    # find tiles we need for this split on highest res
    bb = values['bbox']
    print 'bb', bb
    #
    # make sure the bb is valid
    #
    max_width = self.__dojoserver.get_image()._width
    max_height = self.__dojoserver.get_image()._height
    bb[1] = min(max_width, bb[1])
    bb[3] = min(max_height, bb[3])

    x_tiles = range((bb[0]//512), (((bb[1]-1)//512) + 1))
    y_tiles = range((bb[2]//512), (((bb[3]-1)//512) + 1))

    tile_dict = {} # here this is the segmentation

    for x in x_tiles:
      for y in y_tiles:

        if not x in tile_dict:
          tile_dict[x] = {}

        i = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_image().get_input_format()

        s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_segmentation().get_input_format()

        # try the temporary data first
        ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

        if not os.path.exists(os.path.join(ids_data_path,s)):
          ids_data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

        hdf5_file = h5py.File(os.path.join(ids_data_path,s))
        list_of_names = []
        hdf5_file.visit(list_of_names.append)
        image_data = hdf5_file[list_of_names[0]].value
        hdf5_file.close()

        tile_dict[x][y] = image_data

    # go through rows of each tile and segmentation
    row_val = self.tile_iter(tile_dict)

    old_tile = row_val

    #
    label_id = values['id']

    label_touches_border = True

    ##
    #
    # important: we need to detect if the label_id touches one of the borders of our segmentation
    # we need to load additional tiles until this is not the case anymore
    #

    max_x_tiles = self.__dojoserver.get_image()._width / 512
    max_y_tiles = self.__dojoserver.get_image()._height / 512

    while label_touches_border:

      touches_left = label_id in row_val[:,0]
      touches_right = label_id in row_val[:,row_val.shape[1]-1]
      touches_top = label_id in row_val[0,:]
      touches_bottom = label_id in row_val[row_val.shape[0]-1, :]

      label_touches_border = touches_left or touches_right or touches_bottom or touches_top

      if not label_touches_border:
        break

      new_data = False

      if touches_left and x_tiles[0] > 0:

        # alright, we need to include more tiles in left x direction
        x_tiles = [x_tiles[0]-1] + x_tiles
        new_data = True

      if touches_top and y_tiles[0] > 0:

        y_tiles = [y_tiles[0]-1] + y_tiles
        new_data = True

      if touches_right and x_tiles[-1] < max_x_tiles-1:

        x_tiles = x_tiles + [x_tiles[-1] + 1]
        new_data = True

      if touches_bottom and y_tiles[-1] < max_y_tiles-1:

        y_tiles = y_tiles + [y_tiles[-1] + 1]
        new_data = True

      if new_data:

        # print 'WE NEED MORE DATA'

        # we got new tiles to process
        for x in x_tiles:
          for y in y_tiles:

            if not x in tile_dict:
              tile_dict[x] = {}
            else:
              # let's check if this is old data
              if y in tile_dict[x]:
                # yes, old data
                continue

            i = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_image().get_input_format()

            s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_segmentation().get_input_format()

            # try the temporary data first
            ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

            if not os.path.exists(os.path.join(ids_data_path,s)):
              ids_data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

            print os.path.join(ids_data_path,s)

            hdf5_file = h5py.File(os.path.join(ids_data_path,s))
            list_of_names = []
            hdf5_file.visit(list_of_names.append)
            image_data = hdf5_file[list_of_names[0]].value
            hdf5_file.close()

            tile_dict[x][y] = image_data

        # go through rows of each tile and segmentation, AGAIN!
        row_val = self.tile_iter(tile_dict)

        old_tile = row_val

      else:

        label_touches_border = False

    # print 'label_touches_border done'

    i_js = values['line']
    bbox = values['bbox']
    click = values['click']

    bbox_relative = np.array(bbox)

    #
    # but take offset of tile into account
    #
    offset_x = x_tiles[0]*512
    offset_y = y_tiles[0]*512

    bbox_relative[0] -= offset_x
    bbox_relative[1] -= offset_x
    bbox_relative[2] -= offset_y
    bbox_relative[3] -= offset_y

    # run through tile
    # lookup each label
    for i in range(row_val.shape[0]):
      for j in range(row_val.shape[1]):
        row_val[i,j] = self.lookup_label(row_val[i,j])

    print '0'

    s_tile = np.zeros(row_val.shape)

    # for l in self.lookup_merge_label(label_id):

    #   s_tile[tile == int(l)] = 1
    #   tile[tile == int(l)] = label_id

    s_tile[row_val == label_id] = 1

    #mh.imsave('/tmp/seg.tif', s_tile.astype(np.uint8))
    #mh.imsave('/tmp/tile.tif', tile.astype(np.uint8))

    for c in i_js:
      s_tile[c[1]-offset_y, c[0]-offset_x] = 0

    label_image,n = mh.label(s_tile)

    print '1'

    # if (n!=3):
    #   print 'ERROR',n

    # check which label was selected
    selected_label = label_image[click[1]-offset_y, click[0]-offset_x]

    # print 'selected', selected_label

    for c in i_js:
      label_image[c[1]-offset_y, c[0]-offset_x] = selected_label # the line belongs to the selected label

    # mh.imsave('/tmp/seg2.tif', 10*label_image.astype(np.uint8))
    print '2'

    # update the segmentation data

    print 'largest id', self.__largest_id

    self.__largest_id += 1
    new_id = self.__largest_id
    print 'new largest id', new_id - self.lookup_label(label_id)

    # unselected_label = selected_label==1 ? unselected_label=2 : unselected_label:1

    if selected_label == 1:
      unselected_label = 2
    else:
      unselected_label = 1

    full_coords = np.where(label_image > 0)
    full_bbox = [min(full_coords[1]), min(full_coords[0]), max(full_coords[1]), max(full_coords[0])]

    # tif.imsave('/tmp/labelimage_bef.tif', label_image.astype(np.uint32))

    label_image[label_image == selected_label] = 0 # should be zero then
    label_image[label_image == unselected_label] = new_id - self.lookup_label(label_id)

    tile = np.add(row_val, label_image).astype(np.uint32)

    print '3'

    # tif.imsave('/tmp/labelimage_aft.tif', label_image.astype(np.uint32))

    # mh.imsave('/tmp/old_tile.tif', old_tile[full_bbox[]].astype(np.uint32))
    tif.imsave('/tmp/new_tile.tif', tile.astype(np.uint32))

    #
    # this is for undo
    #
    old_area = old_tile[full_bbox[1]:full_bbox[3],full_bbox[0]:full_bbox[2]]
    new_area = tile[full_bbox[1]:full_bbox[3],full_bbox[0]:full_bbox[2]]
    current_action = values['current_action']

    print 'FULL BBOX', full_bbox, offset_x, offset_y

    upd_full_bbox = [0,0,0,0]
    upd_full_bbox[0] = full_bbox[0] + offset_x
    upd_full_bbox[1] = full_bbox[1] + offset_y
    upd_full_bbox[2] = full_bbox[2] + offset_x
    upd_full_bbox[3] = full_bbox[3] + offset_y

    action = {}
    action['origin'] = input['origin']
    action['name'] = 'ACTION'
    action_value = {}
    action_value['type'] = 'SPLIT'
    action_value['value'] = [values["z"], upd_full_bbox, old_area, new_area]
    action['value'] = [current_action, action_value]

    self.add_action(action)

    # now create all zoomlevels
    zoomed_tile = tile
    max_zoomlevel = self.__dojoserver.get_segmentation().get_max_zoomlevel()

    target_i = 512*x_tiles[0]
    target_j = 512*y_tiles[0]
    target_width = tile.shape[1]
    target_height = tile.shape[0]

    for w in range(0, max_zoomlevel+1):

      output_folder = self.__mojo_tmp_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(values["z"]).zfill(8)+'/'

      try:
        os.makedirs(output_folder)
      except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
          pass
        else: raise

      if w!=0:
        tile = ndimage.interpolation.zoom(tile, .5, order=0, mode='nearest')

      print '='*80
      print 'W', w

      # find tiles
      x_tiles = range((target_i//512), (((target_i + target_width-1)//512) + 1))
      y_tiles = range((target_j//512), (((target_j + target_height-1)//512) + 1))

      print 'TILES', x_tiles, y_tiles

      tile_width = 0
      tile_height = 0

      pixel_written_x = 0


      for i,x in enumerate(x_tiles):

          # let's grab the pixel coordinate of all tiles of this column
          tile_x = x*512

          # now the offset in x for this column
          if (i==0):
              offset_x = target_i - tile_x + i*512
          else:
              offset_x = 0

          pixel_written_y = 0

          for j,y in enumerate(y_tiles):

              #
              # load old tile
              #

              s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.hdf5'

              # try the temporary data first
              ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(values["z"]).zfill(8)

              if not os.path.exists(os.path.join(ids_data_path,s)):
                ids_data_path = self.__mojo_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(values["z"]).zfill(8)

              # print os.path.join(ids_data_path,s)

              hdf5_file = h5py.File(os.path.join(ids_data_path,s))
              list_of_names = []
              hdf5_file.visit(list_of_names.append)
              image_data = hdf5_file[list_of_names[0]].value
              hdf5_file.close()

              # let's grab the pixel coordinate of this tile
              tile_y = y*512

              if (j==0):
                  offset_y = target_j - tile_y + j*512
              else:
                  offset_y = 0

              tile_width = min(512-offset_x, target_width-pixel_written_x)
              tile_height = min(512-offset_y, target_height-pixel_written_y)

              print 'pixel X,Y', tile_x, tile_y

              print 'copying', pixel_written_y,':',pixel_written_y+tile_height,',',pixel_written_x,':',pixel_written_x+tile_width
              print '     to', offset_y,':',offset_y+tile_height,',', offset_x,':',offset_x+tile_width

              image_data[offset_y:offset_y+tile_height,offset_x:offset_x+tile_width] = tile[pixel_written_y:pixel_written_y+tile_height,pixel_written_x:pixel_written_x+tile_width]

              hdf5filename = output_folder+s
              h5f = h5py.File(hdf5filename, 'w')
              h5f.create_dataset('dataset_1', data=image_data)
              h5f.close()

              print 'written', hdf5filename

              pixel_written_y += tile_height

          pixel_written_x += tile_width

      # update target values
      target_i /= 2
      target_j /= 2
      target_width /= 2
      target_height /= 2

    full_bbox[0] += offset_x
    full_bbox[1] += offset_y
    full_bbox[2] += offset_x
    full_bbox[3] += offset_y

    output = {}
    output['name'] = 'RELOAD'
    output['origin'] = input['origin']
    output['value'] = {'z':values["z"], 'full_bbox':str(full_bbox)}
    # print output
    self.__websocket.send(json.dumps(output))

    output = {}
    output['name'] = 'SPLITDONE'
    output['origin'] = input['origin']
    output['value'] = {'z':values["z"], 'full_bbox':str(full_bbox)}
    self.__websocket.send(json.dumps(output))

    self.__split_count += 1

  def split(self, input):
    '''
    TODO: move to separate class
    '''
    values = input['value']
    data_path = self.__mojo_dir + '/images/tiles/w=00000000/z='+str(values["z"]).zfill(8)

    # find tiles we need for this split on highest res
    bb = values['brush_bbox']

    #
    # make sure the bb is valid
    #
    max_width = self.__dojoserver.get_image()._width
    max_height = self.__dojoserver.get_image()._height
    bb[1] = min(max_width, bb[1])
    bb[3] = min(max_height, bb[3])

    # print 'newbb',bb
    x_tiles = range((bb[0]//512), (((bb[1]-1)//512) + 1))
    y_tiles = range((bb[2]//512), (((bb[3]-1)//512) + 1))

    print x_tiles, y_tiles

    tile_dict = {}
    seg_dict = {}

    for x in x_tiles:
      for y in y_tiles:

        if not x in tile_dict:
          tile_dict[x] = {}

        if not x in seg_dict:
          seg_dict[x] = {}

        i = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_image().get_input_format()

        s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_segmentation().get_input_format()

        tile_dict[x][y] = cv2.imread(os.path.join(data_path,i),0)

        # try the temporary data first
        ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

        if not os.path.exists(os.path.join(ids_data_path,s)):
          ids_data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

        print os.path.join(ids_data_path,s)

        hdf5_file = h5py.File(os.path.join(ids_data_path,s))
        list_of_names = []
        hdf5_file.visit(list_of_names.append)
        image_data = hdf5_file[list_of_names[0]].value
        hdf5_file.close()

        seg_dict[x][y] = image_data

    # go through rows of each tile and segmentation
    [row_val,row_seg] = self.tile_iter(tile_dict,seg_dict)

    label_id = values['id']

    label_touches_border = True

    ##
    #
    # important: we need to detect if the label_id touches one of the borders of our segmentation
    # we need to load additional tiles until this is not the case anymore
    #

    max_x_tiles = self.__dojoserver.get_image()._width / 512
    max_y_tiles = self.__dojoserver.get_image()._height / 512

    while label_touches_border:

      touches_left = label_id in row_seg[:,0]
      touches_right = label_id in row_seg[:,row_seg.shape[1]-1]
      touches_top = label_id in row_seg[0,:]
      touches_bottom = label_id in row_seg[row_seg.shape[0]-1, :]

      label_touches_border = touches_left or touches_right or touches_bottom or touches_top

      if not label_touches_border:
        break

      new_data = False

      print touches_left, touches_right, touches_top, touches_bottom, x_tiles[0]

      if touches_left and x_tiles[0] > 0:

        # print 'left'

        # alright, we need to include more tiles in left x direction
        x_tiles = [x_tiles[0]-1] + x_tiles
        new_data = True

      if touches_top and y_tiles[0] > 0:

        y_tiles = [y_tiles[0]-1] + y_tiles
        new_data = True

      if touches_right and x_tiles[-1] < max_x_tiles-1:

        x_tiles = x_tiles + [x_tiles[-1] + 1]
        new_data = True

      if touches_bottom and y_tiles[-1] < max_y_tiles-1:

        # print 'bottom', max_y_tiles-1

        y_tiles = y_tiles + [y_tiles[-1] + 1]
        new_data = True

      print new_data

      if new_data:

        # we got new tiles to process
        for x in x_tiles:
          for y in y_tiles:
            if not x in tile_dict:
              tile_dict[x] = {}
            else:
              # let's check if this is old data
              if y in tile_dict[x]:
                # yes, old data
                continue

            if not x in seg_dict:
              seg_dict[x] = {}

            i = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_image().get_input_format()

            s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_segmentation().get_input_format()

            tile_dict[x][y] = cv2.imread(os.path.join(data_path,i),0)

            # try the temporary data first
            ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

            if not os.path.exists(os.path.join(ids_data_path,s)):
              ids_data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

            hdf5_file = h5py.File(os.path.join(ids_data_path,s))
            list_of_names = []
            hdf5_file.visit(list_of_names.append)
            image_data = hdf5_file[list_of_names[0]].value
            hdf5_file.close()

            seg_dict[x][y] = image_data

        # go through rows of each tile and segmentation, AGAIN!
        [row_val,row_seg] = self.tile_iter(tile_dict,seg_dict)

      else:

        label_touches_border = False
    #
    # crop according to bounding box
    #
    bbox = values['brush_bbox']
    bbox_relative = np.array(bbox)

    #
    # but take offset of tile into account
    #
    offset_x = x_tiles[0]*512
    offset_y = y_tiles[0]*512

    bbox_relative[0] -= offset_x
    bbox_relative[1] -= offset_x
    bbox_relative[2] -= offset_y
    bbox_relative[3] -= offset_y

    sub_tile = row_val[bbox_relative[2]:bbox_relative[3],bbox_relative[0]:bbox_relative[1]]
    seg_sub_tile = row_seg[bbox_relative[2]:bbox_relative[3],bbox_relative[0]:bbox_relative[1]]

    # mh.imsave('/tmp/dojobox.tif', sub_tile);

    print sub_tile.shape

    sub_tile = mh.gaussian_filter(sub_tile, 1).astype(np.uint8) # gaussian filter
    sub_tile = (255 * exposure.equalize_hist(sub_tile)).astype(np.uint8) # enhance contrast

    # brush_mask = np.zeros((1024,1024),dtype=bool)
    brush_size = values['brush_size']

    i_js = values['i_js']

    # make sparse points in i_js a dense line (with linear interpolation)
    dense_brush = []
    print 'starting loop'
    for i in range(len(i_js)-1):
      # two sparse points
      p0 = i_js[i]
      p1 = i_js[i+1]

      # x and y coordinates of sparse points
      xp = [p0[1], p1[1]] if p0[1] < p1[1] else [p1[1], p0[1]]
      yp = [p0[0], p1[0]] if p0[1] < p1[1] else [p1[0], p0[0]]

      # linear interpolation between p0 and p1
      xs = [x for x in range(xp[0], xp[1]+1)]
      ys = np.round(np.interp(xs, xp, yp)).astype(np.int32)

      # add linear interpolation to brush stroke
      dense_brush += zip(ys,xs)

      # make x axis dense

      # x and y coordinates of sparse points
      xp = [p0[1], p1[1]] if p0[0] < p1[0] else [p1[1], p0[1]]
      yp = [p0[0], p1[0]] if p0[0] < p1[0] else [p1[0], p0[0]]

      # linear interpolation between p0 and p1
      ys = [y for y in range(yp[0], yp[1]+1)]
      xs = np.round(np.interp(ys, yp, xp)).astype(np.int32)

      # add linear interpolation to brush stroke
      dense_brush += zip(ys,xs)

    width = self.__dojoserver.get_image()._width
    height = self.__dojoserver.get_image()._height

    # add dense brush stroke to mask image
    brush_mask = np.zeros((height, width),dtype=bool)

    # for c in i_js:
    for c in dense_brush:
        brush_mask[c[1],c[0]] = True

    # crop
    brush_mask = brush_mask[bbox[2]:bbox[3],bbox[0]:bbox[1]]
    brush_mask = mh.morph.dilate(brush_mask, np.ones((2*brush_size, 2*brush_size)))

    brush_image = np.copy(sub_tile)
    brush_image[~brush_mask] = 0

    # compute frame
    frame = np.zeros(brush_mask.shape,dtype=bool)
    frame[0,:] = True
    frame[:,0] = True
    frame[-1,:] = True
    frame[:,-1] = True

    # dilate non-brush segments
    outside_brush_mask = np.copy(~brush_mask)
    outside_brush_mask = mh.morph.dilate(outside_brush_mask, np.ones((brush_size, brush_size)))

    # compute end points of line
    end_points = np.zeros(brush_mask.shape,dtype=bool)

    first_point = i_js[0]
    last_point = i_js[-1]

    first_point_x = min(first_point[0] - bbox[0],brush_mask.shape[1]-1)
    first_point_y = min(first_point[1] - bbox[2], brush_mask.shape[0]-1)
    last_point_x = min(last_point[0] - bbox[0], brush_mask.shape[1]-1)
    last_point_y = min(last_point[1] - bbox[2], brush_mask.shape[0]-1)
    end_points[first_point_y, first_point_x] = True
    end_points[last_point_y, last_point_x] = True
    end_points = mh.morph.dilate(end_points, np.ones((2*brush_size, 2*brush_size)))

    # compute seeds
    seed_mask = np.zeros(brush_mask.shape,dtype=bool)
    # seed_mask[outside_brush_mask & brush_mask] = True
    seed_mask[outside_brush_mask] = True
    seed_mask[frame] = True
    # seed_mask[corners] = False
    seed_mask[end_points] = False
    seeds,n = mh.label(seed_mask)

    # remove small regions
    sizes = mh.labeled.labeled_size(seeds)
    min_seed_size = 5
    too_small = np.where(sizes < min_seed_size)
    seeds = mh.labeled.remove_regions(seeds, too_small).astype(np.uint8)

    #
    # run watershed
    #
    ws = mh.cwatershed(brush_image.max() - brush_image, seeds)

    mh.imsave('/tmp/end_points.tif', 50*end_points.astype(np.uint8))
    mh.imsave('/tmp/seeds_mask.tif', 50*seed_mask.astype(np.uint8))
    mh.imsave('/tmp/seeds.tif', 50*seeds.astype(np.uint8))
    mh.imsave('/tmp/ws.tif', 50*ws.astype(np.uint8))

    lines_array = np.zeros(ws.shape,dtype=np.uint8)
    lines = []

    print 'long loop start'
    print 'Looking for ', label_id
    print 'new mt', self.__new_merge_table

    for y in range(ws.shape[0]-1):
      for x in range(ws.shape[1]-1):

        # print 'looking for', seg_sub_tile[y,x]

        if self.lookup_label(seg_sub_tile[y,x]) != label_id:
          continue

        if ws[y,x] != ws[y,x+1]:
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])
        if ws[y,x] != ws[y+1,x]:
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])

    for y in range(1,ws.shape[0]):
      for x in range(1,ws.shape[1]):

        if self.lookup_label(seg_sub_tile[y,x]) != label_id:
          continue

        if ws[y,x] != ws[y,x-1]:
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])
        if ws[y,x] != ws[y-1,x]:
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])

    print 'long loop end'

    # mh.imsave('/tmp/lines.tif', 50*lines_array.astype(np.uint8))

    print 'split done'

    output = {}
    output['name'] = 'SPLITRESULT'
    output['origin'] = input['origin']
    output['value'] = lines
    # print output
    self.__websocket.send(json.dumps(output))

  def tile_iter(self,*dicts):
    lend = range(len(dicts))
    rows = [None]*len(dicts)
    first_row = True
    for r in dicts[0].keys():
      cols = [None]*len(dicts)
      first_col = True

      for c in dicts[0][r]:
        if first_col:
          cols = [dicts[i][r][c] for i in lend]
          first_col = False
        else:
          cols = [np.concatenate((cols[i], dicts[i][r][c]), axis=0) for i in lend]

      if first_row:
        rows = cols
        first_row = False
      else:
        rows = [np.concatenate((rows[i], cols[i]), axis=1) for i in lend]

    # Return the only tile value or all tile values
    return rows[0] if len(dicts) == 1 else rows

  def lookup_label(self, label_id):

    label_id = str(label_id)

    while label_id in self.__new_merge_table:

      label_id = self.__new_merge_table[label_id]

    while label_id in self.__hard_merge_table:

      # old_label_id = label_id
      label_id = self.__hard_merge_table[label_id]

    return int(label_id)

  def lookup_merge_label(self,label_id):


    labels = [str(label_id)]

    for (k,v) in self.__hard_merge_table.items():

      if v == int(label_id):
        labels = labels + self.lookup_merge_label(k)

    return labels

