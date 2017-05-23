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
from PIL import Image as PILImage

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

    # Attributes for the split operation
    [self.data_path,self.label_id,self.x_tiles,self.y_tiles,self.z] = [0,0,0,0,0]

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

  def add_action(self, input):

    values = list(input['value'])
    current_action = values[0]
    value = values[1]
    username = input['origin']

    # check if we have an action stack for this user
    if not username in self.__actions:
      self.__actions[username] = []

    if current_action < len(self.__actions[username]):
      # remove all actions from the last undo'ed one to the current
      self.__actions[username] = self.__actions[username][0:current_action]

    self.__actions[username].append(value)

    #
    # send the action index
    #
    output = {}
    output['name'] = 'CURRENT_ACTION'
    output['origin'] = username
    output['value'] = [len(self.__actions[username])]*2
    self.__websocket.send(json.dumps(output))

  def undo_action(self, input):

    value = input['value']
    username = input['origin']

    if username in self.__actions:
      # actions available
      action = self.__actions[username][value-1]

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

        self.z = action['value'][0]
        bb = action['value'][1]
        old_area = action['value'][2]

        self.x_tiles = range((bb[0]//512), (((bb[2]-1)//512) + 1))
        self.y_tiles = range((bb[1]//512), (((bb[3]-1)//512) + 1))

        tile_dict = {} # here this is the segmentation

        # Load segmentation data
        tile_dict = self.file_iter(tile_dict)[0]
        # go through rows of each segmentation
        row_val = self.tile_iter(tile_dict)[0]

        # Temporarily harden new merges
        new_merges = self.__new_merge_table
        for k,v in new_merges.iteritems():
          while str(v) in new_merges: v = new_merges[str(v)]
          row_val[np.where(row_val==float(k))] = v

        #
        # NOW REPLACE THE PIXEL DATA
        # but take offset of tile into account
        #
        offset_x = self.x_tiles[0]*512
        offset_y = self.y_tiles[0]*512

        bb_relative =  np.array(bb) - [offset_x, offset_y, offset_x , offset_y]

        row_val[bb_relative[1]:bb_relative[3],bb_relative[0]:bb_relative[2]] = old_area

        # Save all the splits
        self.save_iter(row_val)

        # send reload event
        output = {}
        output['name'] = 'HARD_RELOAD'
        output['origin'] = 'SERVER'
        output['value'] = {'z':self.z, 'full_bbox':str(bb)}
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
    output['value'] = [value, len(self.__actions[username])]
    self.__websocket.send(json.dumps(output))

  def redo_action(self, input):

    value = input['value']
    username = input['origin']
    # increase value
    value = min(len(self.__actions[username]), value+1)

    if username in self.__actions:

      # actions available
      action = self.__actions[username][value-1]

      #
      # redo merge
      #
      if action['type'] == 'MERGE_GROUP':

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

        self.z = action['value'][0]
        bb = action['value'][1]
        new_area = action['value'][3]

        self.x_tiles = range((bb[0]//512), (((bb[2]-1)//512) + 1))
        self.y_tiles = range((bb[1]//512), (((bb[3]-1)//512) + 1))

        tile_dict = {} # here this is the segmentation

        # Load segmentation data
        tile_dict = self.file_iter(tile_dict)[0]
        # go through rows of each tile and segmentation
        row_val = self.tile_iter(tile_dict)[0]

        # Temporarily harden new merges
        new_merges = self.__new_merge_table
        for k,v in new_merges.iteritems():
          while str(v) in new_merges: v = new_merges[str(v)]
          row_val[np.where(row_val==float(k))] = v

        #
        # NOW REPLACE THE PIXEL DATA
        # but take offset of tile into account
        #
        offset_x = self.x_tiles[0]*512
        offset_y = self.y_tiles[0]*512

        bb_relative = np.array(bb) - [offset_x, offset_y, offset_x , offset_y]

        row_val[bb_relative[1]:bb_relative[3],bb_relative[0]:bb_relative[2]] = new_area

        # Save all the splits
        self.save_iter(row_val)

        # send reload event
        output = {}
        output['name'] = 'HARD_RELOAD'
        output['origin'] = 'SERVER'
        output['value'] = {'z':self.z, 'full_bbox':str(bb)}
        # print output
        self.__websocket.send(json.dumps(output))

    #
    # send the action index
    #
    output = {}
    output['name'] = 'CURRENT_ACTION'
    output['origin'] = username
    output['value'] = [value, len(self.__actions[username])]
    self.__websocket.send(json.dumps(output))

  def save(self, input):

    print 'SAVING..'
    self.__actions = {}
    for username in self.__actions:
      # empty user actions
      output = {}
      output['value'] = [0,0]
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
    bb = values['bbox']
    image = self.__dojoserver.get_image()
    self.label_id = values['id']
    self.z = values['z']

    # find tiles we need for this split on highest res and make sure the bb is valid
    bb = np.clip(np.array(bb),0,[image._width]*2 + [image._height]*2)

    self.x_tiles = range((bb[0]//512), (((bb[1]-1)//512) + 1))
    self.y_tiles = range((bb[2]//512), (((bb[3]-1)//512) + 1))

    tile_dict = {} # here this is the segmentation

    # Load segmentation data
    tile_dict = self.file_iter(tile_dict)[0]
    # go through rows of each segmentation
    row_val = self.tile_iter(tile_dict)[0]

    self.use_new_merge()

    ##
    #
    # important: we need to detect if the label_id touches one of the borders of our segmentation
    # we need to load additional tiles until this is not the case anymore
    #
    [row_val, old_tile] = self.edge_iter(tile_dict, row_val)

    # temporarily flatten
    for seg in self.ids: row_val[np.where(row_val == seg)] = self.label_id

    # Apply saved hardened merges
    lut = self.get_hard_merge_table()
    row_val = lut[row_val]

    i_js = values['line']
    click = values['click']

    #
    # Take offset of tile into account
    #
    offset_x = self.x_tiles[0]*512
    offset_y = self.y_tiles[0]*512

    s_tile = np.zeros(row_val.shape)
    s_tile[row_val == self.label_id] = 1

    # mh.imsave('../t_val.jpg', row_val.astype(np.uint8))

    for c in i_js:
      s_tile[c[1]-offset_y, c[0]-offset_x] = 0

    label_image,n = mh.label(s_tile)

    # check which label was selected
    selected_label = label_image[click[1]-offset_y, click[0]-offset_x]

    for c in i_js:
      label_image[c[1]-offset_y, c[0]-offset_x] = selected_label # the line belongs to the selected label

    # update the segmentation data

    self.__largest_id += 1
    new_id = self.__largest_id

    # unselected_label = selected_label==1 ? unselected_label=2 : unselected_label:1

    if selected_label == 1:
      unselected_label = 2
    else:
      unselected_label = 1

    full_coords = np.where(label_image > 0)
    full_bb = [min(full_coords[1]), min(full_coords[0]), max(full_coords[1]), max(full_coords[0])]

    label_image[label_image == selected_label] = 0 # should be zero then
    label_image[label_image == unselected_label] = new_id - self.lookup_label(self.label_id)

    tile = np.add(row_val, label_image).astype(np.uint32)

    #
    # this is for undo
    #
    old_area = old_tile[full_bb[1]:full_bb[3],full_bb[0]:full_bb[2]]
    new_area = tile[full_bb[1]:full_bb[3],full_bb[0]:full_bb[2]]
    current_action = values['current_action']

    upd_full_bb = [full_bb[i] + [offset_x, offset_y][i%2] for i in range(4)]

    action = {}
    action['origin'] = input['origin']
    action['name'] = 'ACTION'
    action_value = {}
    action_value['type'] = 'SPLIT'
    action_value['value'] = [values["z"], upd_full_bb, old_area, new_area]
    action['value'] = [current_action, action_value]

    self.add_action(action)
    print 'split done\n'

    # Save all the splits, yielding offsets
    offsets = self.save_iter(tile)

    full_bb[0] += offsets[0]
    full_bb[1] += offsets[1]
    full_bb[2] += offsets[0]
    full_bb[3] += offsets[1]

    output = {}
    output['name'] = 'RELOAD'
    output['origin'] = input['origin']
    output['value'] = {'z':values["z"], 'full_bbox':str(full_bb)}
    # print output
    self.__websocket.send(json.dumps(output))

    output = {}
    output['name'] = 'SPLITDONE'
    output['origin'] = input['origin']
    output['value'] = {'z':values["z"], 'full_bbox':str(full_bb)}
    self.__websocket.send(json.dumps(output))

    self.__split_count += 1

  def split(self, input):

    print 'split go...'

    values = input['value']
    self.z = values['z']
    bb = values['brush_bbox']
    self.label_id = values['id']
    image = self.__dojoserver.get_image()
    self.data_path = self.__mojo_dir + '/images/tiles/w=00000000/z='+str(self.z).zfill(8)

    # find tiles we need for this split on highest res and make sure the bb is valid
    bb = np.clip(np.array(bb),0,[image._width]*2 + [image._height]*2)

    self.x_tiles = range((bb[0]//512), (((bb[1]-1)//512) + 1))
    self.y_tiles = range((bb[2]//512), (((bb[3]-1)//512) + 1))

    img_dict = {}
    seg_dict = {}

    # Load segmentation and image data through file
    [seg_dict,img_dict] = self.file_iter(seg_dict,img_dict)
    # go through rows of each tile and segmentation, AGAIN!
    [row_seg,row_img] = self.tile_iter(seg_dict,img_dict)

    self.use_new_merge()

    ##
    #
    # important: we need to detect if the label_id touches one of the borders of our segmentation
    # we need to load additional tiles until this is not the case anymore
    #
    [row_seg,row_img] = self.edge_iter(seg_dict,img_dict,row_seg,row_img)

    # temporarily flatten
    for seg in self.ids: row_seg[np.where(row_seg == seg)] = self.label_id

    #
    # but take offset of tile into account
    #
    offset_x = self.x_tiles[0]*512
    offset_y = self.y_tiles[0]*512

    bb_relative = bb - np.array([offset_x]*2 + [offset_y]*2)
    sub_tile = row_img[bb_relative[2]:bb_relative[3],bb_relative[0]:bb_relative[1]]
    seg_sub_tile = row_seg[bb_relative[2]:bb_relative[3],bb_relative[0]:bb_relative[1]]

    sub_tile = mh.gaussian_filter(sub_tile, 1).astype(np.uint8) # gaussian filter
    sub_tile = (255 * exposure.equalize_hist(sub_tile)).astype(np.uint8) # enhance contrast

    brush_size = values['brush_size']

    i_js = values['i_js']

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
    brush_mask = brush_mask[bb[2]:bb[3],bb[0]:bb[1]]
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
    first_point,last_point = (i_js[0],i_js[-1])

    bind = lambda x: tuple(min(x[i] - bb[2*i], brush_mask.shape[1-i]-1) for i in range(1,-1,-1))
    first_points, last_points = (bind(x) for x in [first_point, last_point])

    end_points[first_points],end_points[last_points] = (True, True)
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

    lines_array = np.zeros(ws.shape,dtype=np.uint8)
    lines = []

    for y in range(ws.shape[0]-1):
      for x in range(ws.shape[1]-1):

        # print 'looking for', seg_sub_tile[y,x]

        if self.lookup_label(seg_sub_tile[y,x]) != self.label_id:
          continue

        if ws[y,x] != ws[y,x+1]:
          lines_array[y,x] = 1
          lines.append([bb[0]+x,bb[2]+y])
        if ws[y,x] != ws[y+1,x]:
          lines_array[y,x] = 1
          lines.append([bb[0]+x,bb[2]+y])

    for y in range(1,ws.shape[0]):
      for x in range(1,ws.shape[1]):

        if self.lookup_label(seg_sub_tile[y,x]) != self.label_id:
          continue

        if ws[y,x] != ws[y,x-1]:
          lines_array[y,x] = 1
          lines.append([bb[0]+x,bb[2]+y])
        if ws[y,x] != ws[y-1,x]:
          lines_array[y,x] = 1
          lines.append([bb[0]+x,bb[2]+y])

    output = {}
    output['name'] = 'SPLITRESULT'
    output['origin'] = input['origin']
    output['value'] = lines
    # print output
    self.__websocket.send(json.dumps(output))

  def file_iter(self,*dicts,**kwargs):
    lend = range(len(dicts))
    for x in self.x_tiles:
      for y in self.y_tiles:
        for i in lend:
          if not x in dicts[i]:
            dicts[i][x] = {}
          # If updating data for last dictionary
          elif 'up' in kwargs and i is len(dicts)-1:
            # check for old data
            if y in dicts[i][x]:
              continue

        # If extra dictionary for image data
        if len(dicts) > 1:
          img = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_image().get_input_format()
          dicts[-1][x][y] = np.array(PILImage.open(os.path.join(self.data_path,img)))
        # Always get segmentation data
        seg = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.'+self.__dojoserver.get_segmentation().get_input_format()

        # try the temporary data first
        ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w=00000000/z='+str(self.z).zfill(8)
        if not os.path.exists(os.path.join(ids_data_path,seg)):
          ids_data_path = self.__mojo_dir + '/ids/tiles/w=00000000/z='+str(self.z).zfill(8)

        hdf5_file = h5py.File(os.path.join(ids_data_path,seg))
        list_of_names = []
        hdf5_file.visit(list_of_names.append)
        dicts[0][x][y] = hdf5_file[list_of_names[0]].value
        hdf5_file.close()

    # Return the only dictionary or all dictionaries
    return dicts

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
    return rows

  def edge_iter(self,*dicts_rows):
    # Takes 2 or 4 arguments
    lend = len(dicts_rows)//2
    rows = dicts_rows[-lend:]
    dicts = dicts_rows[:-lend]

    label_touches_border = True
    max_x_tiles = self.__dojoserver.get_image()._xtiles
    max_y_tiles = self.__dojoserver.get_image()._ytiles

    while label_touches_border:
      img = np.dstack(tuple([255*(rows[0]-rows[0].min())/(rows[0].max())])*3)
      if self.label_id not in rows[0]: print 'No match in tile ' + str(self.x_tiles) + ', ' + str(self.y_tiles)

      img[np.where(rows[0] == self.label_id)] = [50,160,80]

      touches_top = any([ seg in rows[0][0,:] for seg in self.ids ])
      touches_left = any([ seg in rows[0][:,0] for seg in self.ids ])
      touches_right = any([ seg in rows[0][:,-1] for seg in self.ids ])
      touches_bottom = any([ seg in rows[0][-1,:] for seg in self.ids ])

      label_touches_border = touches_left or touches_right or touches_bottom or touches_top

      if not label_touches_border:
        break

      new_data = False

      if touches_left and self.x_tiles[0] > 0:

        # alright, we need to include more tiles in left x direction
        self.x_tiles = [self.x_tiles[0]-1] + self.x_tiles
        new_data = True

      if touches_top and self.y_tiles[0] > 0:

        self.y_tiles = [self.y_tiles[0]-1] + self.y_tiles
        new_data = True

      if touches_right and self.x_tiles[-1] < max_x_tiles-1:

        self.x_tiles = self.x_tiles + [self.x_tiles[-1] + 1]
        new_data = True

      if touches_bottom and self.y_tiles[-1] < max_y_tiles-1:

        self.y_tiles = self.y_tiles + [self.y_tiles[-1] + 1]
        new_data = True

      if new_data:

        # go through rows of each tile and segmentation
        rows = self.tile_iter(*self.file_iter(*dicts, up='date'))

      else:

        label_touches_border = False

    # if only one dict, copy first row to second row
    return rows*2 if lend == 1 else rows

  def save_iter(self,tile):
    # now create all zoomlevels
    max_zoomlevel = self.__dojoserver.get_segmentation().get_max_zoomlevel()

    target_i = 512*self.x_tiles[0]
    target_j = 512*self.y_tiles[0]
    target_width = tile.shape[1]
    target_height = tile.shape[0]

    for w in range(0, max_zoomlevel+1):

      output_folder = self.__mojo_tmp_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(self.z).zfill(8)+'/'

      try:
        os.makedirs(output_folder)
      except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(output_folder):
          pass
        else: raise

      if w!=0:
        tile = ndimage.interpolation.zoom(tile, .5, order=0, mode='nearest')

      # find tiles
      self.x_tiles = range((target_i//512), (((target_i + target_width-1)//512) + 1))
      self.y_tiles = range((target_j//512), (((target_j + target_height-1)//512) + 1))

      tile_width = 0
      pixel_written_x = 0


      for i,x in enumerate(self.x_tiles):

          # let's grab the pixel coordinate of all tiles of this column
          tile_x = x*512

          # now the offset in x for this column
          if (i==0):
              offset_x = target_i - tile_x + i*512
          else:
              offset_x = 0

          pixel_written_y = 0

          for j,y in enumerate(self.y_tiles):

              #
              # load old tile
              #

              s = 'y='+str(y).zfill(8)+',x='+str(x).zfill(8)+'.hdf5'

              # try the temporary data first
              ids_data_path = self.__mojo_tmp_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(self.z).zfill(8)

              if not os.path.exists(os.path.join(ids_data_path,s)):
                ids_data_path = self.__mojo_dir + '/ids/tiles/w='+str(w).zfill(8)+'/z='+str(self.z).zfill(8)

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

              image_data[offset_y:offset_y+tile_height,offset_x:offset_x+tile_width] = tile[pixel_written_y:pixel_written_y+tile_height,pixel_written_x:pixel_written_x+tile_width]

              hdf5filename = output_folder+s
              h5f = h5py.File(hdf5filename, 'w')
              h5f.create_dataset('dataset_1', data=image_data)
              h5f.close()

              pixel_written_y += tile_height

          pixel_written_x += tile_width

      # update target values
      target_i /= 2
      target_j /= 2
      target_width /= 2
      target_height /= 2

    # Return offsets
    return [offset_x,offset_y]

  def use_new_merge(self):

    self.ids = [self.label_id]
    # Temporarily harden new merges
    new_merges = self.__new_merge_table
    for k,v in new_merges.iteritems():
      chain = [int(k)]
      while str(v) in new_merges:
        v = new_merges[str(v)]
        if v not in self.ids and v not in chain: chain.append(v)
      if self.label_id == v:
        self.ids += chain

  def lookup_label(self, label_id):

    label_id = self.__hard_merge_table[label_id]

    while str(label_id) in self.__new_merge_table:

      label_id = self.__new_merge_table[str(label_id)]

    return label_id
