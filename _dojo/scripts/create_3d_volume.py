import os
import shutil

from nipy.core.api import Image, AffineTransform

from nipy.io.api import save_image

from PIL import Image as PILImage

import tifffile as tif

import numpy as np

def create(rootdir):

  out = None
  prev = None

  out_is_there = False

  dirs = sorted(os.listdir(rootdir))

  for d in dirs:

    files = os.listdir(os.path.join(rootdir,d))

    for f in files:
      input_image = tif.imread(os.path.join(rootdir,d,f))
      # print input_image
      # print type(input_image)
      # print 'ccc',input_image.flatten()
      if out_is_there:
        #out = np.concatenate([out, input_image.flatten()])
        out = np.dstack([out, input_image])
      else:
        # out = input_image.flatten()
        out = input_image
        out_is_there = True

  # return

  # i = 0
  # for root, dirs, files in os.walk(rootdir):

  #     fullpaths = [(os.path.join(root, name)) for name in files]

  #     for f in fullpaths:
  #       print f
  #       input_image = tif.imread(f)
  #       # print input_image
  #       # print type(input_image)
  #       # print 'ccc',input_image.flatten()
  #       if out_is_there:
  #         #out = np.concatenate([out, input_image.flatten()])
  #         out = np.dstack([out, input_image])
  #       else:
  #         # out = input_image.flatten()
  #         out = input_image
  #         out_is_there = True

#>>> from nipy.io.api import save_image
#>>> data = np.zeros((91,109,91), dtype=np.uint8)
#>>> cmap = AffineTransform('kji', 'zxy', np.eye(4))
#>>> img = Image(data, cmap)
#>>> fname1 = os.path.join(tmpdir, 'img1.nii.gz')
#>>> saved_img1 = save_image(img, fname1)
    

      # image_data = PILImage.open(os.path.join(subdir,file))
      # if image_data.mode != "RGB":
      #   image_data = image_data.convert("RGB")

      # print image_data.toString()
      # break

      # shutil.copy(os.path.join(subdir, file), '/tmp/'+str(i)+'.tif')
      # i+=1
  length = out.shape[0]
  print 'aaa'
  print out
  # out = out.reshape((512, 512, length/512/512))
  print out
  cmap = AffineTransform('kji','zxy', np.eye(4))
  img = Image(out, cmap)
  save_image(img, '/tmp/out.nii.gz')

create('/home/d/TMP/MOJO/ac3x75/mojo/images/tiles/w=00000001')

