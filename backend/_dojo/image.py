import os
import re
import StringIO
from datasource import Datasource
from PIL import Image

class Image(Datasource):

  def __init__(self, mojo_dir):
    '''
    @override
    '''
    query = 'image'
    input_format = 'tif'
    output_format = 'jpg'
    sub_dir = 'images'

    super(Image, self).__init__(mojo_dir, query, input_format, output_format, sub_dir)

  def get_tile(self, file):
    '''
    '''
    super(Segmentation, self).get_tile(file)

    image_data = Image.open(tif_file)
    output = StringIO.StringIO()
    image_data.save(output, 'JPEG')

    content_type = 'image/jpeg'
    content = output.getvalue()

    return content, content_type

  def handle(self, request):
    '''
    @override
    '''
    content_type = 'text/html'
    content = 'Error 404'

    super(Image, self).handle(request, content, content_type)

