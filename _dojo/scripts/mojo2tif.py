import tifffile as tif
import mahotas as mh
import numpy as np
import h5py
import sys
import os

class Logic():

  def __init__(self):
    '''
    '''
    pass
    
    
  def run(self, mojodir, outdir):

    print 'Convert MOJO dir', mojodir

    self.__mojo_dir = mojodir

    # load largest image, combine to tile, store as tif
    
    data_path = self.__mojo_dir + '/ids/w=00000000/'

    for z in os.listdir(data_path):

      data_path2 = os.path.join(data_path, z)

      print data_path2

      images = os.listdir(data_path2)
      tile = {}
      for i in images:


        location = os.path.splitext(i)[0].split(',')
        for l in location:
          l = l.split('=')
          exec(l[0]+'=int("'+l[1]+'")')

        if not x in tile:
          tile[x] = {}
        # tile[x][y] = tif.imread(os.path.join(data_path,i))


        hdf5_file = h5py.File(os.path.join(data_path2,i))
        list_of_names = []
        hdf5_file.visit(list_of_names.append)
        tile[x][y] = hdf5_file[list_of_names[0]].value
        hdf5_file.close()        



      row = None
      first_row = True



      # go through rows of each tile
      for r in tile.keys():
        column = None
        first_column = True

        print len(tile[r])

        for c in tile[r]:

          if first_column:
            column = tile[r][c]
            first_column = False
          else:

            column = np.concatenate((column, tile[r][c]), axis=0)

        if first_row:
          row = column
          first_row = False
        else:
          row = np.concatenate((row, column), axis=1)

      tile = row


      
      outfile = os.path.join(outdir, z+'.tif')

      tif.imsave( outfile,tile)
      print 'stored', outfile


#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len( sys.argv ) < 3:
    print 'need dir and outdir'
    sys.exit( 1 )

  logic = Logic()
  logic.run( sys.argv[1], sys.argv[2] )

