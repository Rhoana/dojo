#!/usr/bin/env python

#
# This script takes a sample segmentation TIF file (32 bit supported) and colorizes it.
#
import os
import re
import sys
#import h5py
import numpy as np
import scipy.ndimage

import matplotlib.pyplot as plt

import tifffile as tif

from skimage import data
from skimage.transform import pyramid_gaussian


class PyramidLogic():
  '''
  '''
  def __init__( self ):
    '''
    '''

  def run( self, input, output ):
    '''
    '''


    image = tif.imread(input)
    print image.dtype
    rows, cols = image.shape
    dim = 1

    pyramid = []

    #pyramid = tuple(pyramid_gaussian(image, downscale=2, mode='nearest'))

    res_image = scipy.ndimage.zoom(image, 0.5, order=0)

    # while res_image.shape[0] >= 256:

    #   pyramid.append(res_image)

    #   res_image = scipy.ndimage.zoom(image, 0.5, order=0)

      

    #composite_image = np.zeros((rows, cols + cols / 2), dtype=np.uint32)

    #composite_image[:rows, :cols] = pyramid[0].astype(np.uint32)

    # i_row = 0
    # for p in pyramid[1:]:
    #     n_rows, n_cols = p.shape[:2]
    #     composite_image[i_row:i_row + n_rows, cols:cols + n_cols] = p.astype(np.uint32)
    #     i_row += n_rows

    # plt.imshow(res_image)
    # plt.show()


    tif.imsave(output, res_image)







def print_help( scriptName ):
  '''
  '''
  description = 'Create a pyramid version of an image.'
  print description
  print
  print 'Usage: ' + scriptName + ' INPUT_FILE OUTPUT_FILE'
  print

#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len( sys.argv ) < 3:
    print_help( sys.argv[0] )
    sys.exit( 1 )

  logic = PyramidLogic()
  logic.run( sys.argv[1], sys.argv[2] )
