#!/usr/bin/env python

#
# This script takes a sample segmentation TIF file (32 bit supported) and colorizes it.
#
import os
import re
import sys
import h5py
import numpy as np

import tifffile as tif



class ColorizeLogic():
  '''
  '''
  def __init__( self ):
    '''
    '''

  def run( self, input, colormap, output ):
    '''
    '''

    # load colormap
    hdf5_file = h5py.File(colormap, 'r')
    list_of_names = []
    hdf5_file.visit(list_of_names.append) 
    colormap = hdf5_file[list_of_names[0]].value
    no_colors = len(colormap)    
    
    for root, dirs, files in os.walk(input):

      for f in files:

        if f.startswith('c_') or f.startswith('p_'):
          continue

        # load input tif
        input_image = tif.imread(os.path.join(root,f))
        #print input_image.shape
        # create 3 channel output container
        output_image = np.empty([input_image.shape[0], input_image.shape[1], 3],dtype=np.int8)

        # loop through image
        for (u,v), value in np.ndenumerate(input_image):

          rgb = colormap[value % no_colors]
          #print u,v, value, rgb
          output_image[u][v][0] = rgb[0]
          output_image[u][v][1] = rgb[1]
          output_image[u][v][2] = rgb[2]

        # save output tif
        tif.imsave(os.path.join(output,'c_'+f), output_image)

        print os.path.join(output,'c_'+f), 'stored.'


def print_help( scriptName ):
  '''
  '''
  description = 'Colorize segmentation TIFs file using a colormap'
  print description
  print
  print 'Usage: ' + scriptName + ' INPUT_DIR COLOR_MAP OUTPUT_DIR'
  print

#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len( sys.argv ) < 3:
    print_help( sys.argv[0] )
    sys.exit( 1 )

  logic = ColorizeLogic()
  logic.run( sys.argv[1], sys.argv[2], sys.argv[3] )
