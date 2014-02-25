import os
import shutil

from nipy.io.files import load as nipLoad
from nipy.io.files import save as nipSave

from PIL import Image as PILImage

import tifffile as tif

import numpy as np

def create(rootdir):

  out = None
  prev = None

  out_is_there = False

  i = 0
  for root, dirs, files in os.walk(rootdir):
    for f in files:

      input_image = tif.imread(os.path.join(root, f))

      if out_is_there:
        out = np.concatenate([out, input_image.flatten()])
      else:
        out = input_image.flatten()
        out_is_there = True

        from nipy.core.api import Image, AffineTransform
>>> from nipy.io.api import save_image
>>> data = np.zeros((91,109,91), dtype=np.uint8)
>>> cmap = AffineTransform('kji', 'zxy', np.eye(4))
>>> img = Image(data, cmap)
>>> fname1 = os.path.join(tmpdir, 'img1.nii.gz')
>>> saved_img1 = save_image(img, fname1)
    

      # image_data = PILImage.open(os.path.join(subdir,file))
      # if image_data.mode != "RGB":
      #   image_data = image_data.convert("RGB")

      # print image_data.toString()
      # break

      # shutil.copy(os.path.join(subdir, file), '/tmp/'+str(i)+'.tif')
      # i+=1

  print out.shape

create('/home/d/TMP/MOJO/ac3x75/mojo/images/tiles/w=00000001')

