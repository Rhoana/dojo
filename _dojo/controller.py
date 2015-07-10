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
    '''
    '''
    self.__websocket = None

    self.__merge_table = {}

    self.__lock_table = {'0':True}

    self.__problem_table = []

    self.__users = []

    self.__mojo_dir = mojo_dir

    self.__mojo_tmp_dir = tmp_dir

    self.__mojo_out_dir = out_dir
    
    self.__database = database

    self.__dojoserver = dojoserver

    self.__actions = {}

    if self.__database:
      self.__largest_id = self.__database.get_largest_id()
    else:
      self.__largest_id = 0

    self.__split_count = 0

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
    # and the orphans
    self.send_orphans()

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

  def send_orphans(self):
    '''
    '''
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

    elif input['name'] == 'ADJUST':
      self.adjust(input)

    elif input['name'] == 'SAVE':
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
    '''
    '''
    values = list(input['value'])
    current_action = values[0]
    value = values[1]
    username = input['origin']

    # check if we have an action stack for this user
    if not username in self.__actions:
      self.__actions[username] = []

    # action_type = values['type']
    # action_value = values['value']

    if current_action < len(self.__actions[username]) - 1:
      # remove all actions from the last undo'ed one to the current
      # print 'removing', current_action, len(self.__actions[username])
      self.__actions[username] = self.__actions[username][0:current_action+1]

    self.__actions[username].append(value)

    # print 'added action', value

    #
    # send the action index
    #
    output = {}
    output['name'] = 'CURRENT_ACTION'
    output['origin'] = username
    output['value'] = len(self.__actions[username]) - 1
    self.__websocket.send(json.dumps(output))


  def undo_action(self, input):
    '''
    '''
    value = input['value']
    username = input['origin']

    if username in self.__actions:
      # actions available
      action = self.__actions[username][value]
      # print 'Undoing', action

      #
      # undo merge and split
      #
      if action['type'] == 'MERGE':

        key = str(action['value'][0])

        if key in self.__merge_table:
          del self.__merge_table[key]
        else:
          # this was already undo'ed before
          pass     

        self.send_merge_table('SERVER')
        self.send_redraw('SERVER')

      elif action['type'] == 'SPLIT':

        z = action['value'][0]
        full_bbox = action['value'][1]
        old_area = action['value'][2]
        new_area = action['value'][3]

        # try the temporary data first
        data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)

        if not os.path.isdir(data_path):
          data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)

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


        # replace the area in tile with old_area
        tile[full_bbox[1]:full_bbox[3],full_bbox[0]:full_bbox[2]] = old_area


        # split tile and save as hdf5
        x0y0 = tile[0:512,0:512]
        x1y0 = tile[0:512,512:1024]
        x0y1 = tile[512:1024,0:512]
        x1y1 = tile[512:1024,512:1024]

        output_folder = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)+'/'

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

        output_folder = self.__mojo_tmp_dir + '/ids/tiles/w=00000001/z='+str(z).zfill(8)+'/'

        try:
          os.makedirs(output_folder)
        except OSError as exc: # Python >2.5
          if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
            pass
          else: raise

        # zoomed_tile = tile.reshape(512,512)
        zoomed_tile = ndimage.interpolation.zoom(tile, .5, order=0, mode='nearest')
        h5f = h5py.File(output_folder+'y=00000000,x=00000000.hdf5', 'w')
        h5f.create_dataset('dataset_1', data=zoomed_tile)
        h5f.close()

        # send reload event
        output = {}
        output['name'] = 'HARD_RELOAD'
        output['origin'] = 'SERVER'
        output['value'] = {'z':z, 'full_bbox':str(full_bbox)}
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
    '''
    '''
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

        key = str(action['value'][0])

        self.__merge_table[key] = action['value'][1]

        self.send_merge_table('SERVER')
        self.send_redraw('SERVER')



      elif action['type'] == 'SPLIT':

        z = action['value'][0]
        full_bbox = action['value'][1]
        old_area = action['value'][2]
        new_area = action['value'][3]

        # try the temporary data first
        data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)

        if not os.path.isdir(data_path):
          data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)

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


        # replace the area in tile with new_area
        tile[full_bbox[1]:full_bbox[3],full_bbox[0]:full_bbox[2]] = new_area


        # split tile and save as hdf5
        x0y0 = tile[0:512,0:512]
        x1y0 = tile[0:512,512:1024]
        x0y1 = tile[512:1024,0:512]
        x1y1 = tile[512:1024,512:1024]

        output_folder = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(z).zfill(8)+'/'

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

        output_folder = self.__mojo_tmp_dir + '/ids/tiles/w=00000001/z='+str(z).zfill(8)+'/'

        try:
          os.makedirs(output_folder)
        except OSError as exc: # Python >2.5
          if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
            pass
          else: raise

        # zoomed_tile = tile.reshape(512,512)
        zoomed_tile = ndimage.interpolation.zoom(tile, .5, order=0, mode='nearest')
        h5f = h5py.File(output_folder+'y=00000000,x=00000000.hdf5', 'w')
        h5f.create_dataset('dataset_1', data=zoomed_tile)
        h5f.close()

        # send reload event
        output = {}
        output['name'] = 'HARD_RELOAD'
        output['origin'] = 'SERVER'
        output['value'] = {'z':z, 'full_bbox':str(full_bbox)}
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
    '''
    '''
    index = input['value']['current_orphan'];
    orphan = input['value']['orphan'];

    self.__database.get_orphans()[index] = orphan;

    self.send_orphans()


  def adjust(self, input):
    '''
    '''
    values = input['value']

    print 'adjust'

    # try the temporary data first
    data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

    if not os.path.isdir(data_path):
      data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

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
    label_id = values['id']
    i_js = values['i_js']
    brush_size = values['brush_size']

    for c in i_js:

      x = int(c[0])# - brush_size/2)
      y = int(c[1])# - brush_size/2)

      for i in range(brush_size):
        for j in range(brush_size):

          tile[y+j,x+i] = label_id


    full_coords = np.where(tile == label_id)
    full_bbox = [min(full_coords[1]), min(full_coords[0]), max(full_coords[1]), max(full_coords[0])]



    # split tile and save as hdf5
    x0y0 = tile[0:512,0:512]
    x1y0 = tile[0:512,512:1024]
    x0y1 = tile[512:1024,0:512]
    x1y1 = tile[512:1024,512:1024]

    output_folder = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)+'/'

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

    output_folder = self.__mojo_tmp_dir + '/ids/tiles/w=00000001/z='+str(values["z"]).zfill(8)+'/'

    try:
      os.makedirs(output_folder)
    except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
        pass
      else: raise

    # zoomed_tile = tile.reshape(512,512)
    zoomed_tile = ndimage.interpolation.zoom(tile, .5, order=0, mode='nearest')
    h5f = h5py.File(output_folder+'y=00000000,x=00000000.hdf5', 'w')
    h5f.create_dataset('dataset_1', data=zoomed_tile)
    h5f.close()

    output = {}
    output['name'] = 'RELOAD'
    output['origin'] = input['origin']
    output['value'] = {'z':values["z"], 'full_bbox':str(full_bbox)}
    # print output
    self.__websocket.send(json.dumps(output))

    output = {}
    output['name'] = 'ADJUSTDONE'
    output['origin'] = input['origin']
    output['value'] = {'z':values["z"], 'full_bbox':str(full_bbox)}
    self.__websocket.send(json.dumps(output))    

  def save(self, input):
    '''
    '''

    # parse the mojo directory for w=0 (largest images)
    mojo_dir = (os.path.join(self.__mojo_dir, 'ids','tiles','w='+str(0).zfill(8)))
    mojo_tmp_dir = (os.path.join(self.__mojo_tmp_dir, 'ids','tiles','w='+str(0).zfill(8)))

    # first, copy the mojo dir to the output dir
    shutil.rmtree(self.__mojo_out_dir, True)
    shutil.copytree(self.__mojo_dir, self.__mojo_out_dir)

    for root, dirs, files in os.walk(mojo_dir):  

      for f in files:

        # grab z
        z_dir = os.path.dirname(os.path.join(root,f)).split('/')[-1]
        print z_dir
        # check if there is a temporary file (==newer data)
        if os.path.exists(os.path.join(mojo_tmp_dir,z_dir,f)):
          print 'Found TEMP'
          segfile = os.path.join(mojo_tmp_dir, z_dir, f)
        else:
          segfile = os.path.join(root,f)

        # now open the segfile and apply the merge table
        hdf5_file = h5py.File(segfile)
        list_of_names = []
        hdf5_file.visit(list_of_names.append)
        image_data = hdf5_file[list_of_names[0]].value
        hdf5_file.close()

        # for y in range(image_data.shape[0]):
        #   for x in range(image_data.shape[1]):

        #     image_data[y,x] = self.lookup_label(image_data[y,x])

        for m in self.__merge_table.keys():
          m_id = self.lookup_label(m)
          image_data[np.where(image_data == int(m))] = m_id

        # now store the image data
        out_seg_file = os.path.join(self.__mojo_out_dir, 'ids', 'tiles', 'w='+str(0).zfill(8), z_dir, f)
        h5f = h5py.File(out_seg_file, 'w')
        h5f.create_dataset('dataset_1', data=image_data)
        h5f.close()

        print 'stored', out_seg_file


    # now we need to create the zoomlevel 1
    # TODO support multiple zoomlevels

    w0_new_dir = os.path.join(self.__mojo_out_dir, 'ids', 'tiles', 'w='+str(0).zfill(8))
    for z in os.listdir(w0_new_dir):

      data_path = os.path.join(w0_new_dir, z)

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

      # now downsample and save as w=00000001
      zoomed_tile = ndimage.interpolation.zoom(tile, .5, order=0, mode='nearest')

      out_seg_file = os.path.join(self.__mojo_out_dir, 'ids', 'tiles', 'w='+str(1).zfill(8), z, 'y=00000000,x=00000000.hdf5')
      h5f = h5py.File(out_seg_file, 'w')
      h5f.create_dataset('dataset_1', data=zoomed_tile)
      h5f.close()

    print 'Splits', self.__split_count
    print 'Merges', len(self.__merge_table.keys())
    print 'All saved! Yahoo!'

    # ping back
    output = {}
    output['name'] = 'SAVED'
    output['origin'] = input['origin']
    output['value'] = {}
    if self.__websocket:    
      self.__websocket.send(json.dumps(output))  


  def finalize_split(self, input):
    '''
    '''
    # values = input['value']

    # # try the temporary data first
    # data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

    # if not os.path.isdir(data_path):
    #   data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

    # images = os.listdir(data_path)
    # print 'images',len(images)
    # tile = {}
    # for i in images:

    #   location = os.path.splitext(i)[0].split(',')
    #   for l in location:
    #     l = l.split('=')
    #     exec(l[0]+'=int("'+l[1]+'")')

    #   if not x in tile:
    #     tile[x] = {}

    #   hdf5_file = h5py.File(os.path.join(data_path,i))
    #   list_of_names = []
    #   hdf5_file.visit(list_of_names.append)
    #   image_data = hdf5_file[list_of_names[0]].value
    #   hdf5_file.close()

    #   tile[x][y] = image_data

    # row = None
    # first_row = True

    # # go through rows of each tile
    # for r in tile.keys():
    #   column = None
    #   first_column = True

    #   for c in tile[r]:
    #     if first_column:
    #       column = tile[r][c]
    #       first_column = False
    #     else:
    #       column = np.concatenate((column, tile[r][c]), axis=0)

    #   if first_row:
    #     row = column
    #     first_row = False
    #   else:
    #     row = np.concatenate((row, column), axis=1)

    # tile = row
    # old_tile = tile

    # print tile.shape



    values = input['value']


    # find tiles we need for this split on highest res
    bb = values['bbox']

    x_tiles = range((bb[0]//512), (((bb[0] + bb[1]-bb[0]-1)//512) + 1))
    y_tiles = range((bb[2]//512), (((bb[2] + bb[3]-bb[2]-1)//512) + 1))    


    tile = {} # here this is the segmentation
    # segtile = {}

    for x in x_tiles:
      for y in y_tiles:

        if not x in tile:
          tile[x] = {}

        # if not x in segtile:
        #   segtile[x] = {}        

        i = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_image().get_input_format()

        s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_segmentation().get_input_format()

        # tile[x][y] = cv2.imread(os.path.join(data_path,i),0)

        # try the temporary data first
        ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

        if not os.path.exists(os.path.join(ids_data_path,s)):
          ids_data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

        # print os.path.join(ids_data_path,s)

        hdf5_file = h5py.File(os.path.join(ids_data_path,s))
        list_of_names = []
        hdf5_file.visit(list_of_names.append)
        image_data = hdf5_file[list_of_names[0]].value
        hdf5_file.close()

        tile[x][y] = image_data



    # go through rows of each tile and segmentation
    row = None
    first_row = True    
    for r in tile.keys():
      column = None
      first_column = True

      for c in tile[r]:
        if first_column:
          column = tile[r][c]
          # column_seg = segtile[r][c]
          first_column = False
        else:
          column = np.concatenate((column, tile[r][c]), axis=0)
          # column_seg = np.concatenate((column_seg, segtile[r][c]), axis=0)

      if first_row:
        row = column
        # row_seg = column_seg
        first_row = False
      else:
        row = np.concatenate((row, column), axis=1)
        # row_seg = np.concatenate((row_seg, column_seg), axis=1)

    tile_dict = tile

    tile = row
    segmentation = tile
    old_tile = np.array(tile)
    # segmentation = row_seg



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

      touches_left = label_id in segmentation[:,0]
      touches_right = label_id in segmentation[:,segmentation.shape[1]-1]
      touches_top = label_id in segmentation[0,:]
      touches_bottom = label_id in segmentation[segmentation.shape[0]-1, :]

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

            # tile_dict[x][y] = cv2.imread(os.path.join(data_path,i),0)

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
        row = None
        first_row = True    
        for r in tile_dict.keys():
          column = None
          first_column = True

          for c in tile_dict[r]:
            if first_column:
              column = tile_dict[r][c]
              # column_seg = segtile[r][c]
              first_column = False
            else:
              column = np.concatenate((column, tile_dict[r][c]), axis=0)
              # column_seg = np.concatenate((column_seg, segtile[r][c]), axis=0)

          if first_row:
            row = column
            # row_seg = column_seg
            first_row = False
          else:
            row = np.concatenate((row, column), axis=1)
            # row_seg = np.concatenate((row_seg, column_seg), axis=1)

        tile = row
        segmentation = tile
        old_tile = np.array(tile)        
        # segmentation = row_seg




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
    # for i in range(tile.shape[0]):
    #   for j in range(tile.shape[1]):
    #     tile[i,j] = self.lookup_label(tile[i,j])

    s_tile = np.zeros(tile.shape)

    for l in self.lookup_merge_label(label_id):

      s_tile[tile == int(l)] = 1
      tile[tile == int(l)] = label_id

    #mh.imsave('/tmp/seg.tif', s_tile.astype(np.uint8))


    for c in i_js:
      s_tile[c[1]-offset_y, c[0]-offset_x] = 0

    label_image,n = mh.label(s_tile)

    # if (n!=3):
    #   print 'ERROR',n

    # check which label was selected
    selected_label = label_image[click[1]-offset_y, click[0]-offset_x]

    # print 'selected', selected_label

    for c in i_js:
      label_image[c[1]-offset_y, c[0]-offset_x] = selected_label # the line belongs to the selected label


    # mh.imsave('/tmp/seg2.tif', 10*label_image.astype(np.uint8))


    # update the segmentation data

    self.__largest_id += 1
    new_id = self.__largest_id

    # unselected_label = selected_label==1 ? unselected_label=2 : unselected_label:1

    if selected_label == 1:
      unselected_label = 2
    else:
      unselected_label = 1

    full_coords = np.where(label_image > 0)
    full_bbox = [min(full_coords[1]), min(full_coords[0]), max(full_coords[1]), max(full_coords[0])]

    label_image[label_image == selected_label] = 0 # should be zero then
    label_image[label_image == unselected_label] = new_id - self.lookup_label(label_id)

    tile = np.add(tile, label_image).astype(np.uint32)



    # mh.imsave('/tmp/old_tile.tif', old_tile[full_bbox[]].astype(np.uint32))
    # mh.imsave('/tmp/new_tile.tif', tile[full_coords].astype(np.uint32))

    #
    # this is for undo
    #
    old_area = old_tile[full_bbox[1]:full_bbox[3],full_bbox[0]:full_bbox[2]]
    new_area = tile[full_bbox[1]:full_bbox[3],full_bbox[0]:full_bbox[2]]
    current_action = values['current_action']

    action = {}
    action['origin'] = input['origin']
    action['name'] = 'ACTION'
    action_value = {}
    action_value['type'] = 'SPLIT'
    action_value['value'] = [values["z"], full_bbox, old_area, new_area]
    action['value'] = [current_action, action_value]

    self.add_action(action)


    # mh.imsave('/tmp/newtile.tif', tile.astype(np.uint32))

    # width = self.__dojoserver.get_image()._width
    # height = self.__dojoserver.get_image()._height

    # width_ratio = width / 512
    # height_ratio = height / 512

    # output_folder = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)+'/'

    # try:
    #   os.makedirs(output_folder)
    # except OSError as exc: # Python >2.5
    #   if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
    #     pass
    #   else: raise

    # for x in x_tiles:
    #   for y in y_tiles:

    #     current_data = tile[y*512-offset_y:y*512-offset_y+512, x*512-offset_x:x*512-offset_x+512]
    #     hdf5filename = output_folder+'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.hdf5'
    #     h5f = h5py.File(hdf5filename, 'w')
    #     h5f.create_dataset('dataset_1', data=current_data)
    #     h5f.close()

    #     # print 'written', hdf5filename



    # now create all zoomlevels
    zoomed_tile = tile
    max_zoomlevel = self.__dojoserver.get_segmentation().get_max_zoomlevel()

    target_i = 512*x_tiles[0]
    target_j = 512*y_tiles[0]
    target_width = tile.shape[1]
    target_height = tile.shape[0]
  
    # print 'ORIGINAL w', 0
    # print 'x', start_x
    # print 'y', start_y
    # print 'size', tile.shape
    # print 'tiles', x_tiles, y_tiles
    # print '='*80


    # orig_startx = start_x
    # orig_starty = start_y

    # tile_width = 512


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

              # source
              # [pixel_written_y:pixel_written_y+tile_height:pixel_written_x:pixel_written_x+tile_width]
              
              # target
              # [offset_y:offset_y+tile_height,offset_x:offset_x+tile_width]
                      
              print 'pixel X,Y', tile_x, tile_y
  #             print 'offset X', offset_x
  #             print 'offset Y', offset_y
  #             print 'source i', pixel_written_x
  #             print 'source j', pixel_written_y
  #             print 'tile width', tile_width
  #             print 'tile height', tile_height
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













      # start_x /= 2
      # start_y /= 2

      # # tile_width /= 2


      # # let's see which tiles we need to write
      # x_tiles = range((start_x//512), (((start_x + zoomed_tile.shape[1] - 1)//512) + 1))
      # y_tiles = range((start_y//512), (((start_y + zoomed_tile.shape[0] - 1)//512) + 1))          

      # print '='*80
      # print '='*80
      # print 'w', w
      # print 'x', start_x
      # print 'y', start_y
      # print 'size', zoomed_tile.shape
      # print 'tiles', x_tiles, y_tiles
      # print '='*80

      # for i,x in enumerate(x_tiles):
      #   for j,y in enumerate(y_tiles):

      #     #
      #     # load old tile
      #     #

      #     s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.hdf5'

      #     # try the temporary data first
      #     ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(values["z"]).zfill(8)

      #     if not os.path.exists(os.path.join(ids_data_path,s)):
      #       ids_data_path = self.__mojo_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(values["z"]).zfill(8)

      #     # print os.path.join(ids_data_path,s)

      #     hdf5_file = h5py.File(os.path.join(ids_data_path,s))
      #     list_of_names = []
      #     hdf5_file.visit(list_of_names.append)
      #     image_data = hdf5_file[list_of_names[0]].value
      #     hdf5_file.close()


      #     # current_data = tile[y*512-offset_y:y*512-offset_y+512, x*512-offset_x:x*512-offset_x+512]
      #     # print 'w', w
      #     # print 'tile', x, y
      #     # print 'current tile width', tile_width
      #     # print 'original startx, starty', orig_startx, orig_starty
      #     # print 'current startx, starty', start_x, start_y
      #     # print 'i,j', i, j



      #     target_x = start_x - x*512
      #     target_y = start_y - y*512

      #     print 'o_x', target_x
      #     print 'o_y', target_y

      #     target_x_size = 512 - target_x#min(target_x+512, 512-i_new)2048 - 5*512 -
      #     target_y_size = 512 - target_y#min(target_y+512, 512-target_y)
          





      #     # replace image_data

      #     i_new = orig_startx / 2**w % 512#0#max(0,start_x - x*512);
      #     j_new = orig_starty / 2**w % 512#0#max(0,start_y - y*512);

      #     j_size = min(j_new+tile_width, 512-j_new)
      #     i_size = min(i_new+tile_width, 512-i_new)


      #     current_data = zoomed_tile[j*tile_width:j*tile_width+j_size, i*tile_width:i*tile_width+i_size]

      #     print 'tile', x, y
      #     print 'indices', i, j
      #     print 'ij size', i_size, j_size
      #     print 'zoomed tile area', j*tile_width,':',j*tile_width+j_size, i*tile_width,':',i*tile_width+i_size
      #     print 'area shape', current_data.shape
          



      #     print 'i,j new', i_new, j_new
      #     print 'new size', i_size, j_size

      #     # print 'i', i_new, j_new, current_data.shape[0], current_data.shape[1]
      #     image_data[j_new:j_new+current_data.shape[0], i_new:i_new+current_data.shape[1]] = current_data

      #     hdf5filename = output_folder+s
      #     h5f = h5py.File(hdf5filename, 'w')
      #     h5f.create_dataset('dataset_1', data=image_data)
      #     h5f.close()

      #     print 'written', hdf5filename



    full_bbox[0] += offset_x
    full_bbox[1] += offset_y
    full_bbox[2] += offset_x
    full_bbox[3] += offset_y

    # # split tile and save as hdf5
    # x0y0 = tile[0:512,0:512]
    # x1y0 = tile[0:512,512:1024]
    # x0y1 = tile[512:1024,0:512]
    # x1y1 = tile[512:1024,512:1024]

    # output_folder = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)+'/'

    # try:
    #   os.makedirs(output_folder)
    # except OSError as exc: # Python >2.5
    #   if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
    #     pass
    #   else: raise

    # h5f = h5py.File(output_folder+'y=00000000,x=00000000.hdf5', 'w')
    # h5f.create_dataset('dataset_1', data=x0y0)
    # h5f.close()

    # h5f = h5py.File(output_folder+'y=00000001,x=00000000.hdf5', 'w')
    # h5f.create_dataset('dataset_1', data=x0y1)
    # h5f.close()

    # h5f = h5py.File(output_folder+'y=00000000,x=00000001.hdf5', 'w')
    # h5f.create_dataset('dataset_1', data=x1y0)
    # h5f.close()

    # h5f = h5py.File(output_folder+'y=00000001,x=00000001.hdf5', 'w')
    # h5f.create_dataset('dataset_1', data=x1y1)
    # h5f.close()

    # output_folder = self.__mojo_tmp_dir + '/ids/tiles/w=00000001/z='+str(values["z"]).zfill(8)+'/'

    # try:
    #   os.makedirs(output_folder)
    # except OSError as exc: # Python >2.5
    #   if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
    #     pass
    #   else: raise

    # # zoomed_tile = tile.reshape(512,512)
    # zoomed_tile = ndimage.interpolation.zoom(tile, .5, order=0, mode='nearest')
    # h5f = h5py.File(output_folder+'y=00000000,x=00000000.hdf5', 'w')
    # h5f.create_dataset('dataset_1', data=zoomed_tile)
    # h5f.close()

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

    # # try the temporary data first
    # ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

    # if not os.path.isdir(ids_data_path):
    #   ids_data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

    # find tiles we need for this split on highest res
    bb = values['brush_bbox']

    x_tiles = range((bb[0]//512), (((bb[0] + bb[1]-bb[0]-1)//512) + 1))
    y_tiles = range((bb[2]//512), (((bb[2] + bb[3]-bb[2]-1)//512) + 1))    


    tile = {}
    segtile = {}

    for x in x_tiles:
      for y in y_tiles:

        if not x in tile:
          tile[x] = {}

        if not x in segtile:
          segtile[x] = {}        

        i = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_image().get_input_format()

        s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_segmentation().get_input_format()

        tile[x][y] = cv2.imread(os.path.join(data_path,i),0)

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

        segtile[x][y] = image_data



    # go through rows of each tile and segmentation
    row = None
    first_row = True    
    for r in tile.keys():
      column = None
      first_column = True

      for c in tile[r]:
        if first_column:
          column = tile[r][c]
          column_seg = segtile[r][c]
          first_column = False
        else:
          column = np.concatenate((column, tile[r][c]), axis=0)
          column_seg = np.concatenate((column_seg, segtile[r][c]), axis=0)

      if first_row:
        row = column
        row_seg = column_seg
        first_row = False
      else:
        row = np.concatenate((row, column), axis=1)
        row_seg = np.concatenate((row_seg, column_seg), axis=1)

    tile_dict = tile

    tile = row
    segmentation = row_seg



    # images = os.listdir(data_path)
    # tile = {}
    # for i in images:

    #   location = os.path.splitext(i)[0].split(',')
    #   for l in location:
    #     l = l.split('=')
    #     exec(l[0]+'=int("'+l[1]+'")')

    #   if not x in tile:
    #     tile[x] = {}
    #   tile[x][y] = cv2.imread(os.path.join(data_path,i),0)#tif.imread(os.path.join(data_path,i))

    # row = None
    # first_row = True

    # # go through rows of each tile
    # for r in tile.keys():
    #   column = None
    #   first_column = True

    #   for c in tile[r]:
    #     if first_column:
    #       column = tile[r][c]
    #       first_column = False
    #     else:
    #       column = np.concatenate((column, tile[r][c]), axis=0)

    #   if first_row:
    #     row = column
    #     first_row = False
    #   else:
    #     row = np.concatenate((row, column), axis=1)

    # tile = row



    # # try the temporary data first
    # data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

    # if not os.path.isdir(data_path):
    #   data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(values["z"]).zfill(8)

    # images = os.listdir(data_path)
    # segtile = {}
    # for i in images:

    #   location = os.path.splitext(i)[0].split(',')
    #   for l in location:
    #     l = l.split('=')
    #     exec(l[0]+'=int("'+l[1]+'")')

    #   if not x in segtile:
    #     segtile[x] = {}

    #   hdf5_file = h5py.File(os.path.join(data_path,i))
    #   list_of_names = []
    #   hdf5_file.visit(list_of_names.append)
    #   image_data = hdf5_file[list_of_names[0]].value
    #   hdf5_file.close()

    #   segtile[x][y] = image_data

    # row2 = None
    # first_row = True

    # # go through rows of each tile
    # for r in segtile.keys():
    #   column = None
    #   first_column = True

    #   for c in segtile[r]:
    #     if first_column:
    #       column = segtile[r][c]
    #       first_column = False
    #     else:
    #       column = np.concatenate((column, segtile[r][c]), axis=0)

    #   if first_row:
    #     row2 = column
    #     first_row = False
    #   else:
    #     row2 = np.concatenate((row2, column), axis=1)

    # segmentation = row2



    mh.imsave('/tmp/tilebef.jpg', tile)




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

      touches_left = label_id in segmentation[:,0]
      touches_right = label_id in segmentation[:,segmentation.shape[1]-1]
      touches_top = label_id in segmentation[0,:]
      touches_bottom = label_id in segmentation[segmentation.shape[0]-1, :]

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

            if not x in segtile:
              segtile[x] = {}        

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

            segtile[x][y] = image_data



        # go through rows of each tile and segmentation, AGAIN!
        row = None
        first_row = True    
        for r in tile_dict.keys():
          column = None
          first_column = True

          for c in tile_dict[r]:
            if first_column:
              column = tile_dict[r][c]
              column_seg = segtile[r][c]
              first_column = False
            else:
              column = np.concatenate((column, tile_dict[r][c]), axis=0)
              column_seg = np.concatenate((column_seg, segtile[r][c]), axis=0)

          if first_row:
            row = column
            row_seg = column_seg
            first_row = False
          else:
            row = np.concatenate((row, column), axis=1)
            row_seg = np.concatenate((row_seg, column_seg), axis=1)

        tile = row
        segmentation = row_seg


    # mh.imsave('/tmp/tileaft.jpg', tile)
    # tif.imsave('/tmp/tileaft.tif', segmentation)



    # #
    # # crop according to bounding box
    # #
    # bbox = values['brush_bbox']

    # #
    # # but take offset of tile into account
    # #
    # offset_x = x_tiles[0]*512
    # offset_y = y_tiles[0]*512

    # bbox[0] -= offset_x
    # bbox[1] -= offset_x
    # bbox[2] -= offset_y
    # bbox[3] -= offset_y

    # sub_tile = tile[bbox[2]:bbox[3],bbox[0]:bbox[1]]
    # seg_sub_tile = segmentation[bbox[2]:bbox[3],bbox[0]:bbox[1]]

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

    sub_tile = tile[bbox_relative[2]:bbox_relative[3],bbox_relative[0]:bbox_relative[1]]
    seg_sub_tile = segmentation[bbox_relative[2]:bbox_relative[3],bbox_relative[0]:bbox_relative[1]]



    # mh.imsave('/tmp/dojobox.tif', sub_tile);

    print sub_tile.shape

    sub_tile = mh.gaussian_filter(sub_tile, 1).astype(np.uint8) # gaussian filter
    sub_tile = (255 * exposure.equalize_hist(sub_tile)).astype(np.uint8) # enhance contrast


    # brush_mask = np.zeros((1024,1024),dtype=bool)
    brush_size = values['brush_size']

    i_js = values['i_js']

    # print i_js

    # for c in i_js:
    #   brush_mask[c[1],c[0]-math.floor(brush_size/2)] = True
    #   brush_mask[c[1],c[0]+math.floor(brush_size/2)] = True
        
    # brush_mask = brush_mask[bbox[2]:bbox[3],bbox[0]:bbox[1]]
        
    # for i in range(brush_size):
    #     brush_mask = mh.morph.dilate(brush_mask)

    # brush_mask = mh.morph.dilate(brush_mask, np.ones((brush_size, brush_size)))

    # make sparse points in i_js a dense line (with linear interpolation)
    dense_brush = []
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

      # dense_brush = list(set(dense_brush))

    # print dense_brush

    width = self.__dojoserver.get_image()._width
    height = self.__dojoserver.get_image()._height

    # add dense brush stroke to mask image
    brush_mask = np.zeros((height, width),dtype=bool)

#    for c in i_js:
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

    # # compute corners 
    # corners = np.zeros(brush_mask.shape,dtype=bool)

    # n = 2*brush_size 

    # # upper left 
    # corners[0:n,0:n] = True

    # # upper right
    # corners[0:n,-n:-1] = True
    # corners[0:n,-1] = True

    # # lower left
    # corners[-n:-1,0:n] = True
    # corners[-1,0:n] = True

    # # lower right
    # corners[-n:-1,-n:-1] = True
    # corners[-1,-n:-1] = True
    # corners[-n:-1,-1] = True
    # corners[-1,-1] = True

    # dilate non-brush segments
    outside_brush_mask = np.copy(~brush_mask)
    outside_brush_mask = mh.morph.dilate(outside_brush_mask, np.ones((brush_size, brush_size)))

    # # compute brush boundary

    # for y in range(outside_brush_mask.shape[0]-1):
    #   for x in range(outside_brush_mask.shape[1]-1):

    #     if brush_mask[y,x] != brush_mask[y,x+1]: #and seg_sub_tile[y,x] == label_id:  
    #       outside_brush_mask[y,x] = 1
    #       outside_brush_mask[y,x+1] = 1

    #     if brush_mask[y,x] != brush_mask[y+1,x]: #and seg_sub_tile[y,x] == label_id:
    #       outside_brush_mask[y,x] = 1
    #       outside_brush_mask[y+1,x] = 1

    # for y in range(1,outside_brush_mask.shape[0]):
    #   for x in range(1,outside_brush_mask.shape[1]):

    #     if brush_mask[y,x] != brush_mask[y,x-1]: #and seg_sub_tile[y,x] == label_id:  
    #       outside_brush_mask[y,x] = 1
    #       outside_brush_mask[y,x-1] = 1
        
    #     if brush_mask[y,x] != brush_mask[y-1,x]:# and seg_sub_tile[y,x] == label_id:
    #       outside_brush_mask[y,x] = 1
    #       outside_brush_mask[y-1,x] = 1


    # compute end points of line
    end_points = np.zeros(brush_mask.shape,dtype=bool)

    first_point = i_js[0]
    last_point = i_js[-1]

    first_point_x = min(first_point[0] - bbox[0],brush_mask.shape[1]-1)
    first_point_y = min(first_point[1] - bbox[2], brush_mask.shape[0]-1)
    last_point_x = min(last_point[0] - bbox[0], brush_mask.shape[1]-1)
    last_point_y = min(last_point[1] - bbox[2], brush_mask.shape[0]-1)

    # print first_point_x, first_point_y
    # print last_point_x, last_point_y

    # p0 = (i_js[0][0] - bbox[0], i_js[0][1] - bbox[2])
    # p1 = (i_js[-1][0] - bbox[0], i_js[-1][1] - bbox[2])
    # p0 = 
    # print i_js[0], i_js[-1], bbox, p0, p1, brush_mask.shape
    # end_points[p0[1], p0[0]] = True
    # end_points[p1[1], p1[0]] = True
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




















    # outside_brush_mask = np.copy(~brush_mask)
    # for i in range(brush_size / 2):
    #     outside_brush_mask = mh.morph.dilate(outside_brush_mask)

    # outside_brush_mask = mh.morph.dilate(outside_brush_mask, np.ones((brush_size, brush_size)))


    # brush_boundary_mask = brush_mask & outside_brush_mask

    # crop image and boundary mask
    # brush_image = mh.croptobbox(brush_image)
    # brush_boundary_mask = mh.croptobbox(brush_boundary_mask)

    # x0 = brush_size/2
    # x1 = brush_boundary_mask.shape[0] - x0
    # y0 = x0
    # y1 = brush_boundary_mask.shape[1] - y0

    # brush_boundary_mask = brush_boundary_mask[x0:x1,y0:y1]
    # brush_image = brush_image[x0:x1,y0:y1]






    # seeds,n = mh.label(brush_boundary_mask)
    seeds,n = mh.label(seed_mask)

    # print n

    # remove small regions
    sizes = mh.labeled.labeled_size(seeds)
    min_seed_size = 5
    too_small = np.where(sizes < min_seed_size)
    seeds = mh.labeled.remove_regions(seeds, too_small).astype(np.uint8)


    #
    # run watershed
    #
    ws = mh.cwatershed(brush_image.max() - brush_image, seeds)

    # mh.imsave('/tmp/end_points.tif', 50*end_points.astype(np.uint8))
    # mh.imsave('/tmp/seeds_mask.tif', 50*seed_mask.astype(np.uint8))
    # mh.imsave('/tmp/seeds.tif', 50*seeds.astype(np.uint8))
    # mh.imsave('/tmp/ws.tif', 50*ws.astype(np.uint8))

    lines_array = np.zeros(ws.shape,dtype=np.uint8)
    lines = []

    # print label_id

    # valid_labels = [label_id]

    # while label_id in self.__merge_table.values():
    #   label_id = self.__merge_table.values()[]
    #   valid_labels.append(label_id)

    for y in range(ws.shape[0]-1):
      for x in range(ws.shape[1]-1):

        if ws[y,x] != ws[y,x+1] and self.lookup_label(seg_sub_tile[y,x]) == label_id:  
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])
        if ws[y,x] != ws[y+1,x] and self.lookup_label(seg_sub_tile[y,x]) == label_id:
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])

    for y in range(1,ws.shape[0]):
      for x in range(1,ws.shape[1]):
        if ws[y,x] != ws[y,x-1] and self.lookup_label(seg_sub_tile[y,x]) == label_id:  
          lines_array[y,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])
        if ws[y,x] != ws[y-1,x] and self.lookup_label(seg_sub_tile[y,x]) == label_id:
          lines_array[y,x] = 1
          #lines_array[y-1,x] = 1
          lines.append([bbox[0]+x,bbox[2]+y])          
                
    # mh.imsave('/tmp/lines.tif', 50*lines_array.astype(np.uint8))

    output = {}
    output['name'] = 'SPLITRESULT'
    output['origin'] = input['origin']
    output['value'] = lines
    # print output
    self.__websocket.send(json.dumps(output))

  def lookup_label(self, label_id):
    '''
    '''
    # print self.__merge_table, label_id
    # print self.__merge_table.keys()
    while str(label_id) in self.__merge_table.keys():
      # print 'label id', label_id
      # print 'merge[label id]', self.__merge_table[str(label_id)]
      label_id = self.__merge_table[str(label_id)]

    # print 'new label', label_id

    return label_id

  def lookup_merge_label(self,label_id):
    '''
    '''

    labels = [str(label_id)]

    for (k,v) in self.__merge_table.items():

      if v == int(label_id):
        labels = labels + self.lookup_merge_label(k)

    return labels


