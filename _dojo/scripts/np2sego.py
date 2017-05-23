import os
import math
import numpy as np
import h5py
import lxml
import lxml.etree
import sqlite3

class Sego:
    def __init__(self, output_dir):

        self.tile_num_pixels_y             = 512
        self.tile_num_pixels_x             = 512

        output_path                   = output_dir
        output_ids_path                = output_path + os.sep + 'ids'
        ncolors                       = 1000
        
        
        self.output_tile_ids_path      = output_ids_path + os.sep + 'tiles'
        self.output_tile_volume_file       = output_ids_path + os.sep + 'tiledVolumeDescription.xml'
        self.output_color_map_file         = output_ids_path + os.sep + 'colorMap.hdf5'
        self.output_segment_info_db_file   = output_ids_path + os.sep + 'segmentInfo.db'

        self.id_max               = 0
        self.id_counts            = np.zeros( 0, dtype=np.int64 )
        self.id_tile_list         = []

        # Make a color map
        self.color_map = np.zeros( (ncolors + 1, 3), dtype=np.uint8 )
        for color_i in xrange( 1, ncolors + 1 ):
            rand_vals = np.random.rand(3)
            self.color_map[ color_i ] = [ rand_vals[0]*255, rand_vals[1]*255, rand_vals[2]*255 ]



    def run(self,original_ids,tile_index_z):

        ## Grow regions until there are no boundaries

        current_image_counts = np.bincount( original_ids.ravel() )
        current_image_counts_ids = np.nonzero( current_image_counts )[0]
        current_max = np.max( current_image_counts_ids )
        self.tile_index_z = tile_index_z

        if self.id_max  < current_max:
            self.id_max  = current_max
            self.id_counts.resize( self.id_max  + 1 )

        self.id_counts[ current_image_counts_ids ] = self.id_counts[ current_image_counts_ids ] + np.int64( current_image_counts [ current_image_counts_ids ] )

        ( original_image_num_pixels_x, original_image_num_pixels_y ) = original_ids.shape

        current_image_num_pixels_y = original_image_num_pixels_y
        current_image_num_pixels_x = original_image_num_pixels_x
        current_tile_data_space_y  = self.tile_num_pixels_y
        current_tile_data_space_x  = self.tile_num_pixels_x
        self.tile_index_w          = 0
        ids_stride                 = 1

        while current_image_num_pixels_y > self.tile_num_pixels_y / 2 or current_image_num_pixels_x > self.tile_num_pixels_x / 2:

            current_tile_ids_path    = self.output_tile_ids_path     + os.sep + 'w=' + '%08d' % ( self.tile_index_w ) + os.sep + 'z=' + '%08d' % ( self.tile_index_z )

            self.mkdir_safe( current_tile_ids_path )

            current_ids = original_ids[ ::ids_stride, ::ids_stride ]

            num_tiles_y = int( math.ceil( float( current_image_num_pixels_y ) / self.tile_num_pixels_y ) )
            num_tiles_x = int( math.ceil( float( current_image_num_pixels_x ) / self.tile_num_pixels_x ) )

            for tile_index_y in range( num_tiles_y ):
                for tile_index_x in range( num_tiles_x ):

                    y = tile_index_y * self.tile_num_pixels_y
                    x = tile_index_x * self.tile_num_pixels_x

                    current_tile_ids_name    = current_tile_ids_path    + os.sep + 'y=' + '%08d' % ( tile_index_y ) + ','  + 'x=' + '%08d' % ( tile_index_x ) + '.hdf5'

                    tile_ids                                                                   = np.zeros( ( self.tile_num_pixels_y, self.tile_num_pixels_x ), np.uint32 )
                    tile_ids_non_padded                                                        = current_ids[ y : y + self.tile_num_pixels_y, x : x + self.tile_num_pixels_x ]
                    tile_ids[ 0:tile_ids_non_padded.shape[0], 0:tile_ids_non_padded.shape[1] ] = tile_ids_non_padded[:,:]
                    self.save_hdf5( current_tile_ids_name, 'IdMap', tile_ids )

                    for unique_tile_id in np.unique( tile_ids ):

                        self.id_tile_list.append( (unique_tile_id, self.tile_index_w, self.tile_index_z, tile_index_y, tile_index_x ) )

            current_image_num_pixels_y = current_image_num_pixels_y / 2
            current_image_num_pixels_x = current_image_num_pixels_x / 2
            current_tile_data_space_y  = current_tile_data_space_y  * 2
            current_tile_data_space_x  = current_tile_data_space_x  * 2
            self.tile_index_w          = self.tile_index_w          + 1
            ids_stride                 = ids_stride                 * 2


    def save(self,all_shape):
        ## Sort the tile list so that the same id appears together
        self.id_tile_list = np.array( sorted( self.id_tile_list ), np.uint32 )

        ## Write all segment info to a single file

        print 'Writing colorMap file (hdf5)'

        hdf5             = h5py.File( self.output_color_map_file, 'w' )

        hdf5['idColorMap'] = self.color_map

        hdf5.close()

        print 'Writing segmentInfo file (sqlite)'


        if os.path.exists(self.output_segment_info_db_file):
            os.remove(self.output_segment_info_db_file)
            print "Deleted existing database file."

        con = sqlite3.connect(self.output_segment_info_db_file)

        cur = con.cursor()

        cur.execute('PRAGMA main.cache_size=10000;')
        cur.execute('PRAGMA main.locking_mode=EXCLUSIVE;')
        cur.execute('PRAGMA main.synchronous=OFF;')
        cur.execute('PRAGMA main.journal_mode=WAL;')
        cur.execute('PRAGMA count_changes=OFF;')
        cur.execute('PRAGMA main.temp_store=MEMORY;')

        cur.execute('DROP TABLE IF EXISTS idTileIndex;')
        cur.execute('CREATE TABLE idTileIndex (id int, w int, z int, y int, x int);')
        cur.execute('CREATE INDEX I_idTileIndex ON idTileIndex (id);')

        cur.execute('DROP TABLE IF EXISTS segmentInfo;')
        cur.execute('CREATE TABLE segmentInfo (id int, name text, size int, confidence int);')
        cur.execute('CREATE UNIQUE INDEX I_segmentInfo ON segmentInfo (id);')

        cur.execute('DROP TABLE IF EXISTS relabelMap;')
        cur.execute('CREATE TABLE relabelMap ( fromId int PRIMARY KEY, toId int);')

        for entry_index in xrange(0, self.id_tile_list.shape[0]):
            cur.execute("INSERT INTO idTileIndex VALUES({0}, {1}, {2}, {3}, {4});".format( *self.id_tile_list[entry_index, :] ))

        taken_names = {}

        for segment_index in xrange( 1, self.id_max  + 1 ):
            if len( self.id_counts ) > segment_index and self.id_counts[ segment_index ] > 0:
                if segment_index == 0:
                    new_name = '__boundary__'
                else:
                    new_name = "segment{0}".format( segment_index )
                cur.execute('INSERT INTO segmentInfo VALUES({0}, "{1}", {2}, {3});'.format( segment_index, new_name, self.id_counts[ segment_index ], 0 ))

        con.commit()

        con.close()

        #Output TiledVolumeDescription xml file

        print 'Writing TiledVolumeDescription file'

        ( original_image_num_pixels_x, original_image_num_pixels_y,numTilesZ ) = all_shape

        tiledVolumeDescription = lxml.etree.Element( "tiledVolumeDescription",
            fileExtension = "hdf5",
            numTilesX = str( int( math.ceil( original_image_num_pixels_x / self.tile_num_pixels_x ) ) ),
            numTilesY = str( int( math.ceil( original_image_num_pixels_y / self.tile_num_pixels_y ) ) ),
            numTilesZ = str( numTilesZ ),
            numTilesW = str( self.tile_index_w ),
            numVoxelsPerTileX = str( self.tile_num_pixels_x ),
            numVoxelsPerTileY = str( self.tile_num_pixels_y ),
            numVoxelsPerTileZ = str( 1 ),
            numVoxelsX = str( original_image_num_pixels_x ),
            numVoxelsY = str( original_image_num_pixels_y ),
            numVoxelsZ = str( numTilesZ ),
            dxgiFormat = 'R32_UInt',
            numBytesPerVoxel = str( 4 ),
            isSigned = str( False ).lower() )

        with open( self.output_tile_volume_file, 'w' ) as file:
            file.write( lxml.etree.tostring( tiledVolumeDescription, pretty_print = True ) )


    def mkdir_safe( self, dir_to_make ):

        if not os.path.exists( dir_to_make ):
            execute_string = 'mkdir -p ' + '"' + dir_to_make + '"'
            print execute_string
            os.system( execute_string )

    def save_hdf5( self, file_path, dataset_name, array ):

        hdf5             = h5py.File( file_path, 'w' )
        hdf5.create_dataset( dataset_name, data=array )
        hdf5.close()

        print file_path
        print