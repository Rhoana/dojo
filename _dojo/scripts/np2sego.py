import os
import math
import mahotas
import numpy as np
import h5py
import lxml
import lxml.etree
import sqlite3

class Sego:
    def __init__(self, seg, output_dir):

        seg = np.array(seg).astype(np.uint8)
        shape = seg.shape
        transpose = True

        tile_num_pixels_y             = 512
        tile_num_pixels_x             = 512

        output_path                   = output_dir

        nimages_to_process            = shape[2]
        ncolors                       = 1000

        output_ids_path                = output_path + os.sep + 'ids'
        output_tile_ids_path           = output_ids_path + os.sep + 'tiles'

        output_tile_volume_file       = output_ids_path + os.sep + 'tiledVolumeDescription.xml'
        output_color_map_file         = output_ids_path + os.sep + 'colorMap.hdf5'
        output_segment_info_db_file   = output_ids_path + os.sep + 'segmentInfo.db'

        def mkdir_safe( dir_to_make ):

            if not os.path.exists( dir_to_make ):
                execute_string = 'mkdir -p ' + '"' + dir_to_make + '"'
                print execute_string
                print
                os.system( execute_string )

        def save_hdf5( file_path, dataset_name, array ):

            hdf5             = h5py.File( file_path, 'w' )
            hdf5.create_dataset( dataset_name, data=array )
            hdf5.close()

            print file_path
            print

        def load_id_image ( file_path ):
            print file_path
            ids = np.int32( np.array( mahotas.imread( file_path ) ) )

            return ids

        def sbdm_string_hash( in_string ):
            hash = 0
            for i in xrange(len(in_string)):
                hash = ord(in_string[i]) + (hash << 6) + (hash << 16) - hash
            return np.uint32(hash % 2**32)

        id_max               = 0
        id_counts            = np.zeros( 0, dtype=np.int64 )
        id_tile_list         = []

        # Make a color map
        color_map = np.zeros( (ncolors + 1, 3), dtype=np.uint8 )
        for color_i in xrange( 1, ncolors + 1 ):
            rand_vals = np.random.rand(3)
            color_map[ color_i ] = [ rand_vals[0]*255, rand_vals[1]*255, rand_vals[2]*255 ]

        for tile_index_z in range(nimages_to_process):

            original_ids = np.int32(seg[:,:,tile_index_z])
            if transpose: original_ids = original_ids.T

            ## Grow regions until there are no boundaries

            current_image_counts = np.bincount( original_ids.ravel() )
            current_image_counts_ids = np.nonzero( current_image_counts )[0]
            current_max = np.max( current_image_counts_ids )

            if id_max < current_max:
                id_max = current_max
                id_counts.resize( id_max + 1 )

            id_counts[ current_image_counts_ids ] = id_counts[ current_image_counts_ids ] + np.int64( current_image_counts [ current_image_counts_ids ] )

            ( original_image_num_pixels_x, original_image_num_pixels_y ) = original_ids.shape

            current_image_num_pixels_y = original_image_num_pixels_y
            current_image_num_pixels_x = original_image_num_pixels_x
            current_tile_data_space_y  = tile_num_pixels_y
            current_tile_data_space_x  = tile_num_pixels_x
            tile_index_w               = 0
            ids_stride                 = 1

            while current_image_num_pixels_y > tile_num_pixels_y / 2 or current_image_num_pixels_x > tile_num_pixels_x / 2:

                current_tile_ids_path    = output_tile_ids_path     + os.sep + 'w=' + '%08d' % ( tile_index_w ) + os.sep + 'z=' + '%08d' % ( tile_index_z )

                mkdir_safe( current_tile_ids_path )

                current_ids = original_ids[ ::ids_stride, ::ids_stride ]

                num_tiles_y = int( math.ceil( float( current_image_num_pixels_y ) / tile_num_pixels_y ) )
                num_tiles_x = int( math.ceil( float( current_image_num_pixels_x ) / tile_num_pixels_x ) )

                for tile_index_y in range( num_tiles_y ):
                    for tile_index_x in range( num_tiles_x ):

                        y = tile_index_y * tile_num_pixels_y
                        x = tile_index_x * tile_num_pixels_x

                        current_tile_ids_name    = current_tile_ids_path    + os.sep + 'y=' + '%08d' % ( tile_index_y ) + ','  + 'x=' + '%08d' % ( tile_index_x ) + '.hdf5'

                        tile_ids                                                                   = np.zeros( ( tile_num_pixels_y, tile_num_pixels_x ), np.uint32 )
                        tile_ids_non_padded                                                        = current_ids[ y : y + tile_num_pixels_y, x : x + tile_num_pixels_x ]
                        tile_ids[ 0:tile_ids_non_padded.shape[0], 0:tile_ids_non_padded.shape[1] ] = tile_ids_non_padded[:,:]
                        save_hdf5( current_tile_ids_name, 'IdMap', tile_ids )

                        unique_tile_ids = np.unique( tile_ids )

                        for unique_tile_id in unique_tile_ids:

                            id_tile_list.append( (unique_tile_id, tile_index_w, tile_index_z, tile_index_y, tile_index_x ) );

                current_image_num_pixels_y = current_image_num_pixels_y / 2
                current_image_num_pixels_x = current_image_num_pixels_x / 2
                current_tile_data_space_y  = current_tile_data_space_y  * 2
                current_tile_data_space_x  = current_tile_data_space_x  * 2
                tile_index_w               = tile_index_w               + 1
                ids_stride                 = ids_stride                 * 2

            tile_index_z = tile_index_z + 1



            if tile_index_z >= nimages_to_process:
                break


        ## Sort the tile list so that the same id appears together
        id_tile_list = np.array( sorted( id_tile_list ), np.uint32 )

        ## Write all segment info to a single file

        print 'Writing colorMap file (hdf5)'

        hdf5             = h5py.File( output_color_map_file, 'w' )

        hdf5['idColorMap'] = color_map

        hdf5.close()

        print 'Writing segmentInfo file (sqlite)'


        if os.path.exists(output_segment_info_db_file):
            os.remove(output_segment_info_db_file)
            print "Deleted existing database file."

        con = sqlite3.connect(output_segment_info_db_file)

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

        for entry_index in xrange(0, id_tile_list.shape[0]):
            cur.execute("INSERT INTO idTileIndex VALUES({0}, {1}, {2}, {3}, {4});".format( *id_tile_list[entry_index, :] ))

        taken_names = {}

        for segment_index in xrange( 1, id_max + 1 ):
            if len( id_counts ) > segment_index and id_counts[ segment_index ] > 0:
                if segment_index == 0:
                    new_name = '__boundary__'
                else:
                    new_name = "segment{0}".format( segment_index )
                cur.execute('INSERT INTO segmentInfo VALUES({0}, "{1}", {2}, {3});'.format( segment_index, new_name, id_counts[ segment_index ], 0 ))

        con.commit()

        con.close()

        #Output TiledVolumeDescription xml file

        print 'Writing TiledVolumeDescription file'

        tiledVolumeDescription = lxml.etree.Element( "tiledVolumeDescription",
            fileExtension = "hdf5",
            numTilesX = str( int( math.ceil( original_image_num_pixels_x / tile_num_pixels_x ) ) ),
            numTilesY = str( int( math.ceil( original_image_num_pixels_y / tile_num_pixels_y ) ) ),
            numTilesZ = str( tile_index_z ),
            numTilesW = str( tile_index_w ),
            numVoxelsPerTileX = str( tile_num_pixels_x ),
            numVoxelsPerTileY = str( tile_num_pixels_y ),
            numVoxelsPerTileZ = str( 1 ),
            numVoxelsX = str( original_image_num_pixels_x ),
            numVoxelsY = str( original_image_num_pixels_y ),
            numVoxelsZ = str( tile_index_z ),
            dxgiFormat = 'R32_UInt',
            numBytesPerVoxel = str( 4 ),
            isSigned = str( False ).lower() )

        with open( output_tile_volume_file, 'w' ) as file:
            file.write( lxml.etree.tostring( tiledVolumeDescription, pretty_print = True ) )
