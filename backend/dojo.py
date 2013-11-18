#!/usr/bin/env python

#
# DOJO Image Server
#
import itertools
import json
import os
# import png
import re
import sys
import h5py
import numpy as np
import xml.etree.ElementTree as ET
import zlib
import StringIO
from PIL import Image
import ImageFile
ImageFile.MAXBLOCK = 10000000000 # default is 64k


from gevent import http

class ServerLogic:

  def __init__( self ):
    '''
    '''
    self.__mojo_dir = None

    # {'numBytesPerVoxel': '4', 'numVoxelsPerTileZ': '1', 'numVoxelsX': '1024', 'numVoxelsPerTileY': '512', 'numVoxelsPerTileX': '512', 'dxgiFormat': 'R32_UInt', 'numTilesX': '2', 'numTilesY': '2', 'numTilesZ': '20', 'fileExtension': 'hdf5', 'numTilesW': '2', 'numVoxelsZ': '20', 'numVoxelsY': '1024', 'isSigned': 'false'}
    self.__image_info = None
    self.__segmentation_info = None
    self.__colormap = []

    self.__image_output_format = 'jpg'
    self.__segmentation_output_format = 'png'


    # file system regex
    self.__colormap_file_regex = re.compile('colorMap.hdf5$')
    self.__info_regex = re.compile('/tiledVolumeDescription.xml$')

    # handler regex
    self.__image_regex = re.compile('/image/\d+/$')
    self.__segmentation_regex = re.compile('/segmentation/\d+/$')
    self.__image_tile_regex = re.compile('/image/\d+/\d+/\d+_\d+.'+self.__image_output_format+'$')
    self.__segmentation_tile_regex = re.compile('/segmentation/\d+/\d+/\d+_\d+.'+self.__segmentation_output_format+'$')
    self.__colormap_regex = re.compile('/colormap$')


  def run( self, mojo_dir ):
    '''
    '''

    # parse the mojo directory
    for root, dirs, files in os.walk(mojo_dir):

      for f in files:

        # info file
        if self.__info_regex.match(f):
          tree = ET.parse(os.path.join(root,f))
          xml_root = tree.getroot()
          self.__info = xml_root.attrib


        # colormap
        elif self.__colormap_file_regex.match(f):
          hdf5_file = h5py.File(os.path.join(root,f), 'r')
          list_of_names = []
          hdf5_file.visit(list_of_names.append) 
          self.__colormap = hdf5_file[list_of_names[0]].value


    self.__mojo_dir = mojo_dir

    print 'Serving on 1337'
    http.HTTPServer(('0.0.0.0', 1337), self.handle).serve_forever()

  def handle( self, request ):
    '''
    '''

    content_type = 'text/html'
    content = 'Error 404'    

    #
    # an image tile source
    #
    if self.__image_regex.match(request.uri):
      # an image was requested, grab the number
      slice_number = request.uri.split('/')[-1]

      # return xml info for the tile
      xml_info = '<?xml version="1.0" encoding="UTF-8"?>\n'
      xml_info += '<Image xmlns="http://schemas.microsoft.com/deepzoom/2008" TileSize="'+self.__info['numVoxelsPerTileX']+'" Overlap="0" Format="'+self.__image_output_format+'"><Size Width="'+self.__info['numVoxelsX']+'" Height="'+self.__info['numVoxelsY']+'"/></Image>'
      content = xml_info

    #
    # a segmentation tile source
    #
    elif self.__segmentation_regex.match(request.uri):
      # a segmentation was requested, grab the number
      slice_number = request.uri.split('/')[-1]

      # return xml info for the tile
      xml_info = '<?xml version="1.0" encoding="UTF-8"?>\n'
      xml_info += '<Image xmlns="http://schemas.microsoft.com/deepzoom/2008" TileSize="'+self.__info['numVoxelsPerTileX']+'" Overlap="0" Format="'+self.__segmentation_output_format+'"><Size Width="'+self.__info['numVoxelsX']+'" Height="'+self.__info['numVoxelsY']+'"/></Image>'
      content = xml_info

    #
    # a color map
    #
    elif self.__colormap_regex.match(request.uri) and len(self.__colormap) > 0:
      content = json.dumps(self.__colormap.tolist())

    #
    # a segmentation tile
    #
    elif self.__segmentation_tile_regex.match(request.uri):

      request_splitted = request.uri.split('/')
      tile_x_y = request_splitted[-1].split('.')[0]
      tile_x = tile_x_y.split('_')[0]
      tile_y = tile_x_y.split('_')[1]

      zoomlevel = request_splitted[-2]
      slice_number = request_splitted[-3]
      hdf5_file = os.path.join(self.__mojo_dir, 'tiles', 'w='+zoomlevel.zfill(8), 'z='+slice_number, 'y='+tile_x.zfill(8)+','+'x='+tile_y.zfill(8)+'.hdf5')

      if os.path.exists(hdf5_file):

        hdf5_file = h5py.File(hdf5_file)
        list_of_names = []
        hdf5_file.visit(list_of_names.append)
        image_data = hdf5_file[list_of_names[0]].value
        c_image_data = zlib.compress(image_data)

        output = StringIO.StringIO()
        output.write(c_image_data)

        content_type = 'application/octstream'
        content = output.getvalue()

    #
    # an image tile
    #
    elif self.__image_tile_regex.match(request.uri):
      request_splitted = request.uri.split('/')
      tile_x_y = request_splitted[-1].split('.')[0]
      tile_x = tile_x_y.split('_')[0]
      tile_y = tile_x_y.split('_')[1]

      zoomlevel = request_splitted[-2]
      slice_number = request_splitted[-3]
      tif_file = os.path.join(self.__mojo_dir, 'tiles', 'w='+zoomlevel.zfill(8), 'z='+slice_number, 'y='+tile_x.zfill(8)+','+'x='+tile_y.zfill(8)+'.tif')

      if os.path.exists(tif_file):

        image_data = Image.open(tif_file)
        output = StringIO.StringIO()
        image_data.save(output, 'JPEG')

        content_type = 'image/jpeg'
        content = output.getvalue()



        
    request.add_output_header('Access-Control-Allow-Origin', '*')
    request.add_output_header('Content-Type', content_type)

    request.send_reply(200, "OK", content)

def print_help( scriptName ):
  '''
  '''
  description = ''
  print description
  print
  print 'Usage: ' + scriptName + ' MOJO_DIRECTORY'
  print

#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len( sys.argv ) < 2:
    print_help( sys.argv[0] )
    sys.exit( 1 )

  logic = ServerLogic()
  logic.run( sys.argv[1] )
