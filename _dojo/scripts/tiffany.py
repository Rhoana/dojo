# import tifffile as tif
import numpy as np
import cv2
import sys

import struct

class Scanner(object):

  def __init__(self, f):
    '''
    '''
    self._pointer = 0
    self._f = f

  def jumpTo(self, where):
    '''
    '''
    self._pointer = where

  def jump(self, howmuch):
    '''
    '''
    self._pointer += howmuch

  def scan(self, type, chunks=1):
    '''
    '''
    chunk_size = 1
    if type == 'uchar':
      chunk_size = 1
      symbol = 'B'
    elif type == 'ushort':
      chunk_size = 2
      symbol = 'H'
    elif type == 'uint':
      chunk_size = 4
      symbol = 'I'

    f.seek(self._pointer)
    self._pointer += chunk_size

    return struct.unpack(symbol, self._f.read(chunk_size))[0]

class TIFFile(object):

  def __init__(self):
    '''
    '''
    self._little_endian = False
    self._tags = {}



_TIFF_TAGS = {
  'NEW_SUBFILE_TYPE': 254,
  'IMAGE_WIDTH': 256,
  'IMAGE_LENGTH': 257,
  'BITS_PER_SAMPLE': 258,
  'COMPRESSION': 259,
  'PHOTO_INTERP': 262,
  'IMAGE_DESCRIPTION': 270,
  'STRIP_OFFSETS': 273,
  'ORIENTATION': 274,
  'SAMPLES_PER_PIXEL': 277,
  'ROWS_PER_STRIP': 278,
  'STRIP_BYTE_COUNT': 279,
  'X_RESOLUTION': 282,
  'Y_RESOLUTION': 283,
  'PLANAR_CONFIGURATION': 284,
  'RESOLUTION_UNIT': 296,
  'SOFTWARE': 305,
  'DATE_TIME': 306,
  'ARTEST': 315,
  'HOST_COMPUTER': 316,
  'PREDICTOR': 317,
  'COLOR_MAP': 320,
  'TILE_WIDTH': 322,
  'SAMPLE_FORMAT': 339,
  'JPEG_TABLES': 347,
  'METAMORPH1': 33628,
  'METAMORPH2': 33629,
  'IPLAB': 34122,
  'NIH_IMAGE_HDR': 43314,
  'META_DATA_BYTE_COUNTS': 50838,
  'META_DATA': 50839

};

with open(sys.argv[1]) as f:

  s = Scanner(f)
  t = TIFFile()
  t._little_endian = (s.scan('ushort') == 0x4949)
  if (s.scan('ushort') != 42):
    raise Error("Invalid magic number")

  ifd_offset = s.scan('uint')
  s.jumpTo(ifd_offset)
  ifd_count = s.scan('ushort')

  for i in range(ifd_count):

    identifier = s.scan('ushort')
    field = s.scan('ushort')
    count = s.scan('uint')

    print field, count

    if (field == 0):
      # byte
      value_type = 'uchar'
      byte_size = 1
    elif (field == 3):
      # short
      value_type = 'ushort'
      byte_size = 2

    if count * byte_size > 4:
      value = s.scan('uint')
      # s.jump(4)
    else:
      value = s.scan(value_type, count)
      s.jump(4-(count*byte_size))

    for tag in _TIFF_TAGS:
      if _TIFF_TAGS[tag] == identifier:
        t._tags[tag] = value

  
  # now move to the data
  s.jumpTo(t._tags['STRIP_OFFSETS'])
  
