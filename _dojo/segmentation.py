import h5py
import numpy
import os
import re
import zlib
import StringIO
from datasource import Datasource

class Segmentation(Datasource):

  def __init__(self, mojo_dir):
    '''
    @override
    '''
    query = 'segmentation'
    input_format = 'hdf5'
    output_format = 'raw'
    sub_dir = 'ids'

    super(Segmentation, self).__init__(mojo_dir, query, input_format, output_format, sub_dir)

  def get_tile(self, file):
    '''
    '''
    super(Segmentation, self).get_tile(file)

    hdf5_file = h5py.File(file)
    list_of_names = []
    hdf5_file.visit(list_of_names.append)
    image_data = hdf5_file[list_of_names[0]].value

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
