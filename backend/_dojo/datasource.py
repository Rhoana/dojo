import os
import re

import h5py
import json
import xml.etree.ElementTree as ET

class Datasource(object):

  def __init__(self, mojo_dir, query, input_format, output_format, sub_dir):
    '''
    '''

    self.__mojo_dir = mojo_dir

    self.__query = query
    self.__input_format = input_format
    self.__output_format = output_format
    self.__sub_dir = sub_dir

    # {'numBytesPerVoxel': '4', 'numVoxelsPerTileZ': '1', 'numVoxelsX': '1024', 'numVoxelsPerTileY': '512', 'numVoxelsPerTileX': '512', 'dxgiFormat': 'R32_UInt', 'numTilesX': '2', 'numTilesY': '2', 'numTilesZ': '20', 'fileExtension': 'hdf5', 'numTilesW': '2', 'numVoxelsZ': '20', 'numVoxelsY': '1024', 'isSigned': 'false'}
    self.__info = None
    
    self.__has_colormap = False
    self.__colormap = None

    # file system regex
    self.__info_regex = re.compile('.*' + self.__sub_dir + '/tiledVolumeDescription.xml$')
    self.__colormap_file_regex = re.compile('.*' + self.__sub_dir + '/colorMap.hdf5$')

    # handler regex
    self.__query_toc_regex = re.compile('/' + self.__query + '/contents$')
    self.__query_tilesource_regex = re.compile('/' + self.__query + '/\d+/$')
    self.__query_tile_regex = re.compile('/' + self.__query + '/\d+/\d+/\d+_\d+.' + self.__output_format + '$')
    self.__query_colormap_regex = re.compile('/' + self.__query + '/colormap$')

    self.__setup()


  def __setup(self):
    '''
    '''

    # parse the mojo directory
    for root, dirs, files in os.walk(self.__mojo_dir):

      for f in files:

        # info file
        if self.__info_regex.match(os.path.join(root,f)):
          tree = ET.parse(os.path.join(root,f))
          xml_root = tree.getroot()
          self.__info = xml_root.attrib

        # colormap
        elif self.__colormap_file_regex.match(os.path.join(root,f)):
          hdf5_file = h5py.File(os.path.join(root,f), 'r')
          list_of_names = []
          hdf5_file.visit(list_of_names.append) 
          self.__has_colormap = True
          self.__colormap = hdf5_file[list_of_names[0]].value


  def get_info_xml(self):
    '''
    '''
    xml_info = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_info += '<Image xmlns="http://schemas.microsoft.com/deepzoom/2008" TileSize="'+self.__info['numVoxelsPerTileX']+'" Overlap="0" Format="'+self.__output_format+'"><Size Width="'+self.__info['numVoxelsX']+'" Height="'+self.__info['numVoxelsY']+'"/></Image>'

    return xml_info

  def handle(self, request, content, content_type):
    '''
    React to a HTTP request.
    '''
    
    if self.__query_tilesource_regex.match(request.uri):
      content_type = 'text/html'
      content = self.get_info_xml()
    elif self.__query_colormap_regex.match(request.uri) and self.__has_colormap:
      content_type = 'text/html'
      content = json.dumps(self.__colormap.tolist())

    request.add_output_header('Access-Control-Allow-Origin', '*')
    request.add_output_header('Content-Type', content_type)

    request.send_reply(200, "OK", content)

    pass

