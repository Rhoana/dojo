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

  def scanWithoutMoving(self, where, type, chunks=1):
    '''
    '''
    old_pointer = self._pointer
    self._pointer = where
    result = self.scan(type, chunks)
    self._pointer = old_pointer
    return result

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

    bytes = struct.unpack(symbol*chunks, self._f.read(chunks*chunk_size))

    if chunks == 1:
      return bytes[0]
    else:
      return bytes

class TIFFile(object):

  def __init__(self):
    '''
    '''
    self._little_endian = False
    self._tags = {}



_TIFF_TAGS = {
  254: 'NEW_SUBFILE_TYPE',
  256: 'IMAGE_WIDTH',
  257: 'IMAGE_LENGTH',
  258: 'BITS_PER_SAMPLE',
  259: 'COMPRESSION',
  262: 'PHOTO_INTERP',
  266: 'FILL_ORDER',
  269: 'DOCUMENT_NAME',
  270: 'IMAGE_DESCRIPTION',
  273: 'STRIP_OFFSETS',
  274: 'ORIENTATION',
  277: 'SAMPLES_PER_PIXEL',
  278: 'ROWS_PER_STRIP',
  279: 'STRIP_BYTE_COUNT',
  282: 'X_RESOLUTION',
  283: 'Y_RESOLUTION',
  284: 'PLANAR_CONFIGURATION',
  296: 'RESOLUTION_UNIT',
  305: 'SOFTWARE',
  306: 'DATE_TIME',
  315: 'ARTIST',
  316: 'HOST_COMPUTER',
  317: 'PREDICTOR',
  320: 'COLOR_MAP',
  322: 'TILE_WIDTH',
  339: 'SAMPLE_FORMAT',
  347: 'JPEG_TABLES',
  33628: 'METAMORPH1',
  33629: 'METAMORPH2',
  34122: 'IPLAB',
  43314: 'NIH_IMAGE_HDR',
  50838: 'META_DATA_BYTE_COUNTS',
  50839: 'META_DATA'

};

with open(sys.argv[1]) as f:

  s = Scanner(f)
  t = TIFFile()
  t._little_endian = (s.scan('ushort') == 0x4949)
  if (s.scan('ushort') != 42):
    raise Exception("Invalid magic number")

  ifd_offset = s.scan('uint')
  s.jumpTo(ifd_offset)
  ifd_count = s.scan('ushort')

  for i in range(ifd_count):

    identifier = s.scan('ushort')
    field = s.scan('ushort')
    count = s.scan('uint')

    if (field == 0):
      # byte
      value_type = 'uchar'
      byte_size = 1
    elif (field == 2):
      # ascii
      value_type = 'uchar'
    elif (field == 3):
      # short
      value_type = 'ushort'
      byte_size = 2
    elif (field == 4):
      # long
      value_type = 'uint'
      byte_size = 4
    elif (field == 5):
      # long fraction TODO
      pass

    if count * byte_size > 4:
      value = s.scan('uint')
      # value is an offset
      value = s.scanWithoutMoving(value, value_type, count)
    else:
      value = s.scan(value_type, count)
      s.jump(4-(count*byte_size))

    # if identifier in _TIFF_TAGS:
    #   print _TIFF_TAGS[identifier], field, count, value, value_type

    if identifier in _TIFF_TAGS:
      t._tags[_TIFF_TAGS[identifier]] = value

  

  if sys.argv[2] == 'sub':

    factor = int(sys.argv[3])

    out = np.zeros((16384/factor,16384/factor), dtype=np.uint8)

    # now move to the data
    k = 0
    l = 0
    for i,o in enumerate(t._tags['STRIP_OFFSETS']):
      if i % factor == 0:
        # take only every 32th row
        # s.jumpTo(o)
        # grab the number of bytes for this strip
        n = t._tags['STRIP_BYTE_COUNT'][i]

        for j in range(n):
          if j % factor == 0:
            s.jumpTo(o+j)
          
            out[k,l] = s.scan('uchar')
        
            l += 1

        l = 0
        k += 1


    cv2.imwrite('/tmp/sub.jpg', out)

  else:

    width = int(sys.argv[2])
    height = int(sys.argv[3])
    row = int(sys.argv[4])
    col = int(sys.argv[5])    

    out = np.zeros((height, width), dtype=np.uint8)



    
    k = 0
    # grab the right row
    for i in range(row,row+height):
      row_byte_offset = t._tags['STRIP_OFFSETS'][i]

      s.jumpTo(row_byte_offset+col)
      row_data = s.scan('uchar', col+width)

      out[k,:] = row_data

      k += 1

    cv2.imwrite('/tmp/grr.jpg', out)
