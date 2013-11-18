import os
import re
from datasource import Datasource

class Image(Datasource):

  def __init__(self, mojo_dir):
    '''
    @override
    '''
    query = 'image'
    input_format = 'tif'
    output_format = 'jpg'
    sub_dir = 'tiles'

    super(Image, self).__init__(mojo_dir, query, input_format, output_format, sub_dir)

  def handle(self, request):
    '''
    @override
    '''
    content_type = 'text/html'
    content = 'Error 404'

    super(Image, self).handle(request, content, content_type)

