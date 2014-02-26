import os
import re
import StringIO
from datasource import Datasource
from PIL import Image as PILImage
import zlib

import numpy as np
from nipy.core.api import Image as NImage, AffineTransform
from nipy.io.api import save_image

import tifffile as tif

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

  def get_volume(self, zoomlevel):
    '''
    @override
    '''
    files = super(Image, self).get_volume(zoomlevel)

    out = None
    out_is_there = False

    for f in files:
      input_image = tif.imread(f)

      if out_is_there:
        out = np.dstack([out, input_image])
      else:
        out = input_image
        out_is_there = True

    cmap = AffineTransform('kji','zxy', np.eye(4))
    img = NImage(out, cmap)

    # c_image_data = zlib.compress(img.get_data())

    from tempfile import mkstemp
    fd, name = mkstemp(suffix='.nii.gz')
    tmpfile = open(name)
    save_image(img, tmpfile.name)
    tmpfile.close()
    tmpfile = open(name)

    # output = StringIO.StringIO()
    # save_image(img, output)
    # output.write(c_image_data)

    content = tmpfile.read()
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

