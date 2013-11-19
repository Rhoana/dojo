#!/usr/bin/env python

#
# this script imports a mojo filesystem tree, takes the lowest zoom level
# and creates one .TIF per slice in a folder
#
import os
import re
import sys
import h5py
import numpy as np

import tifffile as tif


class ImportLogic():
  '''
  '''
  def __init__( self ):
    '''
    '''

  def run( self, directory, output_directory ):
    '''
    '''

    # zoomlevels are directories w=00000000, w=00000001 etc.
    zoomlevel_regex = re.compile('w=\d+')

    zstack_regex = re.compile('z=\d+')

    colormap_regex = re.compile('colorMap.hdf5')

    zoomlevels = []
    colormap = None
    found_colormap = False
    colors = 0

    for root, dirs, files in os.walk(directory):

      for d in dirs:
        if zoomlevel_regex.match(d):
          zoomlevels.append(os.path.join(root, d))

      # for f in files:
        # if colormap_regex.match(f):
        #   print 'Found color map', f
        #   found_colormap = True
        #   hdf5_file = h5py.File(os.path.join(root,f), 'r')
        #   list_of_names = []
        #   hdf5_file.visit(list_of_names.append) 
        #   colormap = hdf5_file[list_of_names[0]].value
        #   colors = len(colormap)

    # sort all zoomlevels
    zoomlevels.sort()

    print 'Found lowest zoomlevel', zoomlevels[0]

    # loop through all z-stacks for the lowest zoom level

    stack = {}

    for d in os.listdir(zoomlevels[0]):

      if zstack_regex.match(d):
        images = os.listdir(os.path.join(zoomlevels[0],d))

        seq_no = int(d.split('=')[1])

        tile = {}

        # now stitch the images together
        for i in images:

          location = os.path.splitext(i)[0].split(',')
          for l in location:
            l = l.split('=')
            exec(l[0]+'=int("'+l[1]+'")')
          # we now have x and y defined

          # load the image
          if not x in tile:
            tile[x] = {}
          if os.path.splitext(i)[1] == '.tif':
            # print 'Found TIFF format'
            tile[x][y] = tif.imread(os.path.join(zoomlevels[0],d,i))
          elif os.path.splitext(i)[1] == '.hdf5':
            # print 'Found HDF5 format'
            hdf5_file = h5py.File(os.path.join(zoomlevels[0],d,i))
            list_of_names = []
            hdf5_file.visit(list_of_names.append)
            tile[x][y] = hdf5_file[list_of_names[0]].value # always grab the first

            # if found_colormap:
            #   # run through array and replace values with the color
            #   for (u,v), value in np.ndenumerate(tile[x][y]):
            #     #print u,v,value
            #     rgb = colormap[value % colors]
            #     tile[x][y][u][v] = rgb[0] # replace with red channel for now

          if tile[x][y].ndim > 2:
            # hack: if rgb dataset, only take 1 channel
            tile[x][y] = tile[x][y][0]

        # print 'stored seq', seq_no
        stack[seq_no] = tile

    for tile in stack.keys():

      row = None
      first_row = True

      # go through rows of each tile
      for r in stack[tile].keys():
        column = None
        first_column = True

        for c in stack[tile][r]:
          if first_column:
            column = stack[tile][r][c]
            first_column = False
          else:
            column = np.concatenate((column, stack[tile][r][c]))

        if first_row:
          row = column
          first_row = False
        else:
          row = np.concatenate((row, column), axis=1)

      # save the merged image
      print 'stored', os.path.join(output_directory,str(tile)+'.tif')
      tif.imsave(os.path.join(output_directory,str(tile)+'.tif'), row)


def print_help( scriptName ):
  '''
  '''
  description = 'Import a mojo filesystem tree and convert all images of the lowest zoom level to one .TIF per slice'
  print description
  print
  print 'Usage: ' + scriptName + ' DIR OUTPUT_DIR'
  print


#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len( sys.argv ) < 3:
    print_help( sys.argv[0] )
    sys.exit( 1 )

  logic = ImportLogic()
  logic.run( sys.argv[1], sys.argv[2] )