import h5py
import mahotas as mh
import numpy as np
import os
import re
import zlib
import StringIO

from collections import OrderedDict
from datasource import Datasource

class Segmentation(Datasource):

  def __init__(self, mojo_dir, tmp_dir, out_dir, dojoserver):
    '''
    @override
    '''
    query = 'segmentation'
    input_format = 'hdf5'
    output_format = 'raw'
    sub_dir = 'ids'

    super(Segmentation, self).__init__(mojo_dir, tmp_dir, query, input_format, output_format, sub_dir, out_dir)

    self._orphans = None
    self._potential_orphans = None

    self.__dojoserver = dojoserver


  def get_volume_data(self):
    '''
    '''
    files = super(Segmentation, self).get_volume(1)

    out = None
    out_is_there = False

    for i,f in enumerate(files):

      # if i % 4 != 0:
      #   continue

      hdf5_file = h5py.File(f)
      list_of_names = []
      hdf5_file.visit(list_of_names.append)
      image_data = hdf5_file[list_of_names[0]].value
      hdf5_file.close()

      if out_is_there:
        out = np.dstack([out, image_data])
        # out = np.concatenate([out, image_data])
      else:
        #out = input_image
        out = image_data
        out_is_there = True

    print 'Loaded volume data', out.shape

    return out


  def get_volume(self, zoomlevel):
    '''
    @override
    '''
    files = super(Segmentation, self).get_volume(zoomlevel)

    out = None
    out_is_there = False

    for i,f in enumerate(files):

      if i % 4 != 0:
        continue
      hdf5_file = h5py.File(f)
      list_of_names = []
      hdf5_file.visit(list_of_names.append)
      image_data = hdf5_file[list_of_names[0]].value
      hdf5_file.close()

      if out_is_there:
        #out = np.dstack([out, input_image])
        out = np.concatenate([out, image_data.flatten()])
      else:
        #out = input_image
        out = image_data.flatten()
        out_is_there = True

    c_image_data = zlib.compress(out)

    print 'Loaded volume', out.shape

    output = StringIO.StringIO()
    output.write(c_image_data)

    content = output.getvalue()
    content_type = 'application/octstream'

    return content, content_type

  def detect_orphans(self):
    '''
    '''
    print 'Detecting orphans..'
    
    volume = self.get_volume_data()
    
    #
    # get all unique labels
    #
    unique_labels = np.unique(volume)
    print '   Found in total', len(unique_labels), 'labels'

    #
    # count how often each label is in the outside planes of the volume
    #
    mask_top = np.in1d(unique_labels, volume[:,:,0])
    mask_bottom = np.in1d(unique_labels, volume[:,:,volume.shape[2]-1])
    mask_left = np.in1d(unique_labels, volume[:,0,:])
    mask_right = np.in1d(unique_labels, volume[:,volume.shape[1]-1,:])
    mask_front = np.in1d(unique_labels, volume[0,:,:])
    mask_back = np.in1d(unique_labels, volume[volume.shape[0]-1,:,:])


    labels_touch_top = unique_labels[mask_top]
    labels_touch_bottom = unique_labels[mask_bottom]
    labels_touch_left = unique_labels[mask_left]
    labels_touch_right = unique_labels[mask_right]
    labels_touch_front = unique_labels[mask_front]
    labels_touch_back = unique_labels[mask_back]

    touch_counter = {}

    for l in labels_touch_top:
      if l in touch_counter:
        touch_counter[l] += 1
      else:
        touch_counter[l] = 1

    for l in labels_touch_bottom:
      if l in touch_counter:
        touch_counter[l] += 1
      else:
        touch_counter[l] = 1

    for l in labels_touch_left:
      if l in touch_counter:
        touch_counter[l] += 1
      else:
        touch_counter[l] = 1

    for l in labels_touch_right:
      if l in touch_counter:
        touch_counter[l] += 1
      else:
        touch_counter[l] = 1

    for l in labels_touch_front:
      if l in touch_counter:
        touch_counter[l] += 1
      else:
        touch_counter[l] = 1

    for l in labels_touch_back:
      if l in touch_counter:
        touch_counter[l] += 1
      else:
        touch_counter[l] = 1


    #
    # now we know:
    #  labels which are not in touch_counter are orphans
    #  labels which have value 1 in touch_counter are potential orphans
    #          

    orphans = np.setdiff1d(unique_labels, touch_counter.keys())
    print '   Found', len(orphans), 'orphans'

    potential_orphans = np.array([k for k in touch_counter if touch_counter[k] == 1])
    print '   Found', len(potential_orphans), 'potential orphans'

    valid_labels = np.array([k for k in touch_counter if touch_counter[k] > 1])
    print '   Found', len(valid_labels), 'valid labels'

    sizes = mh.labeled.labeled_size(volume)

    orphans_sizes = sizes[orphans]

    potential_orphans_sizes = sizes[potential_orphans]

    bbox = mh.labeled.bbox(volume)


    #
    # orphan handling by eagon
    #

    #Grab orphans' statistics using their indices in the set of unique_labels
    orphans_indices = np.nonzero(np.in1d(unique_labels, orphans, assume_unique = True))[0] + 1
    orphans_bbox = bbox[orphans_indices]
    sizes = mh.labeled.labeled_size(volume)
    orphans_sizes = sizes[orphans_indices]

    #Find single slice orphans
    #Presume that both orphans and orphan_bbox are sorted and have the same indices
    ss_orphans_indices = [x for x in range(len(orphans)) if orphans_bbox[x, 5] - orphans_bbox[x, 4] == 1]
    ss_orphans = orphans[ss_orphans_indices]

    #Find completely engulfed orphans (by a single object)
    engulfed_orphans = []
    engulfed_orphans_indices = []
    for i in range(len(orphans)):
        current_block = volume[orphans_bbox[i,0] - 1:orphans_bbox[i,1] + 1, orphans_bbox[i,2] - 1:orphans_bbox[i,3] + 1, orphans_bbox[i,4] - 1:orphans_bbox[i,5] + (orphans_bbox[i,5] != volume.shape[2])]
        border_mask = mh.labeled.borders(current_block == orphans[i])
        neighbor_ids = np.unique(current_block[border_mask])
        if len(neighbor_ids) == 2:
            engulfed_orphans.append(orphans[i])
            engulfed_orphans_indices.append(i)

    #Sort according to size
    sorted_orphans = zip(orphans, orphans_sizes)
    sorted_orphans.sort(key = lambda t: t[1], reverse=True)
    sorted_orphans = list(x[0] for x in sorted_orphans)
    other_orphans = [x for x in sorted_orphans if x not in engulfed_orphans and x not in ss_orphans]
    other_orphans_bbox = [[(orphans_bbox[np.nonzero(orphans == x)[0][0]][i]) for i in range(6)] for x in other_orphans]

    sorted_engulfed_orphans = zip(engulfed_orphans, engulfed_orphans_indices, orphans_sizes[engulfed_orphans_indices])
    sorted_engulfed_orphans.sort(key = lambda t: t[2], reverse=True)
    engulfed_orphans_indices = list(x[1] for x in sorted_engulfed_orphans)
    sorted_ss_orphans = zip(ss_orphans, ss_orphans_indices, orphans_sizes[ss_orphans_indices])
    sorted_ss_orphans.sort(key = lambda t: t[2], reverse=True)
    ss_orphans_indices = list(x[1] for x in sorted_ss_orphans)
    ss_orphans_indices = [x for x in ss_orphans_indices if x not in engulfed_orphans_indices]

    #Output to strings for json.dumps
    # sorted_engulfed_orphans = list(str(x[0]) for x in sorted_engulfed_orphans)
    # engulfed_orphans_bbox = [[str(orphans_bbox[x][i]) for i in range(6)] for x in engulfed_orphans_indices]
    # sorted_ss_orphans = list(str(x[0]) for x in sorted_ss_orphans)
    # ss_orphans_bbox = [[str(orphans_bbox[x][i]) for i in range(6)] for x in ss_orphans_indices]
    # other_orphans = [str(x) for x in other_orphans]
    sorted_engulfed_orphans = list((x[0]) for x in sorted_engulfed_orphans)
    engulfed_orphans_bbox = [[(orphans_bbox[x][i]) for i in range(6)] for x in engulfed_orphans_indices]
    sorted_ss_orphans = list((x[0]) for x in sorted_ss_orphans)
    ss_orphans_bbox = [[(orphans_bbox[x][i]) for i in range(6)] for x in ss_orphans_indices]
    other_orphans = [(x) for x in other_orphans]


    #Output in JSON
    engulfed_orphans = [list(a) for a in zip(sorted_engulfed_orphans, engulfed_orphans_bbox, [0]*len(sorted_engulfed_orphans))]
    ss_orphans = [list(a) for a in zip(sorted_ss_orphans, ss_orphans_bbox, [0]*len(sorted_ss_orphans))]
    other_orphans = [list(a) for a in zip(other_orphans, other_orphans_bbox, [0]*len(other_orphans))]





    # # now sort the orphans by size
    # sorted_orphans = zip(orphans, orphans_sizes)
    # sorted_orphans.sort(key = lambda t: t[1], reverse=True)
    # sorted_orphans = list(x[0] for x in sorted_orphans)
    sorted_potential_orphans = zip(potential_orphans, potential_orphans_sizes)
    sorted_potential_orphans.sort(key = lambda t: t[1], reverse=True)
    sorted_potential_orphans = list(x[0] for x in sorted_potential_orphans)

    # # print sorted_orphans



    self.get_database()._orphans = engulfed_orphans + ss_orphans + other_orphans
    self.get_database()._potential_orphans = sorted_potential_orphans

    return volume, orphans, orphans_sizes


  def get_tile(self, file):
    '''
    '''
    super(Segmentation, self).get_tile(file)

    hdf5_file = h5py.File(file)
    list_of_names = []
    hdf5_file.visit(list_of_names.append)
    image_data = hdf5_file[list_of_names[0]].value
    hdf5_file.close()

    #print file, image_data[0][0], image_data.shape
    # print image_data.dtype

    #
    # NEW: WE NOW APPLY THE MERGE TABLE FROM THE DATABASE HERE
    #
    lut = self.__dojoserver.get_controller().get_hardened_merge_table()
    # print lut
    hardened_image_data = lut[image_data]
    # print 'hardened', hardened_image_data.shape

    # mh.imsave('/tmp/hardened.tif', hardened_image_data.astype(np.uint32))

    c_image_data = zlib.compress(hardened_image_data.astype(np.uint32))

    output = StringIO.StringIO()
    output.write(c_image_data)

    content = output.getvalue()
    content_type = 'application/octstream'

    return content, content_type

  def handle(self, request):
    '''
    @override
    '''
    content_type = 'text/html'
    content = None

    # any possible other request like persist can go here

    return super(Segmentation, self).handle(request, content, content_type)
