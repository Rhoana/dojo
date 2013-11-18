import os
import re
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

  def handle(self, request):
    '''
    @override
    '''
    content_type = 'text/html'
    content = 'Error 404'

    super(Segmentation, self).handle(request, content, content_type)
