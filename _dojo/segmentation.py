import h5py
import numpy as np
import os
import re
import zlib
import StringIO
from datasource import Datasource

class Segmentation(Datasource):

  def __init__(self, mojo_dir, tmp_dir):
    '''
    @override
    '''
    query = 'segmentation'
    input_format = 'hdf5'
    output_format = 'raw'
    sub_dir = 'ids'

    super(Segmentation, self).__init__(mojo_dir, tmp_dir, query, input_format, output_format, sub_dir)


  def get_volume_data(self):
    '''
    '''
    files = super(Segmentation, self).get_volume(1)


    out = None
    out_is_there = False

    for f in files:
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

    return out


  def get_volume(self, zoomlevel):
    '''
    @override
    '''
    files = super(Segmentation, self).get_volume(zoomlevel)

    out = None
    out_is_there = False

    for f in files:
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

    potential_orphans = [k for k in touch_counter if touch_counter[k] == 1]
    print '   Found', len(potential_orphans), 'potential orphans'

    valid_labels = [k for k in touch_counter if touch_counter[k] > 1]
    print '   Found', len(valid_labels), 'valid labels'


    # run through slices from 0..MAX and sort orphans and potential orphans
    sorted_orphans = np.empty_like(orphans)
    for s in range(volume.shape[2]):
      mask_for_slice = np.in1d(orphans, volume[:,:,s])
      orphans_in_slice = orphans[mask_for_slice]
      orphans = np.setdiff1d(orphans, orphans_in_slice)
      print orphans_in_slice
      

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

    c_image_data = zlib.compress(image_data)

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
