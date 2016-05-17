import os
import re
import StringIO
from datasource import Datasource
from PIL import Image as PILImage
import cv2
import zlib

import numpy as np


class Image(Datasource):

  def __init__(self, mojo_dir, tmp_dir):
    '''
    @override
    '''
    query = 'image'
    input_format = None
    output_format = 'jpg'
    sub_dir = 'images'

    super(Image, self).__init__(mojo_dir, tmp_dir, query, input_format, output_format, sub_dir)

  def get_volume(self, zoomlevel):
    '''
    @override
    '''
    files = super(Image, self).get_volume(zoomlevel)

    out = None
    out_is_there = False

    zSample_max = 50

    # Sample all slices or a maximum number of z slices from all files
    for i in np.linspace(0,len(files)-1,min(len(files),zSample_max), dtype=int):

      input_image = cv2.imread(files[i],0)

      if out_is_there:
        #out = np.dstack([out, input_image])
        out = np.concatenate([out, input_image.flatten()])
      else:
        #out = input_image
        out = input_image.flatten()
        out_is_there = True

    c_image_data = zlib.compress(out)

    output = StringIO.StringIO()
    output.write(c_image_data)

    content = output.getvalue()
    content_type = 'application/octstream'

    return content, content_type

  def get_tile(self, file):
    '''
    @override
    '''
    super(Image, self).get_tile(file)

    image_data = PILImage.open(file)
    if image_data.mode != "RGB":
      image_data = image_data.convert("RGB")
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
    content = None

    return super(Image, self).handle(request, content, content_type)

