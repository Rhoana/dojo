import os
import sys
import string
import math
import mahotas
import PIL
import PIL.Image
import numpy as np
import scipy
import scipy.io
# import cv2
import h5py
import lxml
import lxml.etree
import glob
import sqlite3
import colorsys
import tifffile as tif

def run(input_dir, output_dir):

    tile_num_pixels_y             = 512
    tile_num_pixels_x             = 512

    generate_memorable_names      = False
    compress_ids                  = False

    #original_input_ids_path       = 'D:\\dev\\datasets\\NewPipelineResults2\\output_labels'
    #output_path                   = 'D:\\dev\\datasets\\NewPipelineResults2x20\\mojo'
    ##nimages_to_process            = 1104
    #nimages_to_process            = 20
    #ncolors                       = 10000
    #input_file_format             = 'tif'

    original_input_ids_path  = input_dir
    output_path     = output_dir

    nimages_to_process            = 1697 
    ncolors                       = 1000
    input_file_format             = 'tif'

    #original_input_ids_path       = 'C:\\dev\\datasets\\conn\\main_dataset\\5K_cube\\diced_xy=512_z=32_xyOv=128_zOv=12_dwnSmp=1\\res_from_0ct15_PF\\FS=1\\stitched\\labels_grow'
    #output_path                   = 'C:\\dev\\datasets\\Cube1x10\\mojo'
    #nimages_to_process            = 10
    #ncolors                       = 10000
    #input_file_format             = 'png'

    #original_input_ids_path       = 'C:\\dev\\datasets\\conn\\main_dataset\\ac3train\\diced_xy=512_z=32_xyOv=128_zOv=12_dwnSmp=1\\res_from_sept_30_minotrC_PF\\FS=1\\stitched\\labels_grow'
    #output_path                   = 'C:\\dev\\datasets\\ac3x75_compress\\mojo'
    #nimages_to_process            = 75
    #ncolors                       = 1000
    #input_file_format             = 'png'

    #original_input_ids_path       = 'C:\\dev\\datasets\\conn\\main_dataset\\ac3train\\diced_xy=512_z=32_xyOv=128_zOv=12_dwnSmp=1\\res_from_sept_30_minotrC_PF\\FS=1\\stitched\\labels_grow'
    #output_path                   = 'C:\\dev\\datasets\\ac3x20\\mojo'
    #nimages_to_process            = 20
    #ncolors                       = 1000
    #input_file_format             = 'png'

    output_ids_path                = output_path + os.sep + 'ids'
    output_tile_ids_path           = output_ids_path + os.sep + 'tiles'

    output_tile_volume_file       = output_ids_path + os.sep + 'tiledVolumeDescription.xml'
    output_color_map_file         = output_ids_path + os.sep + 'colorMap.hdf5'
    output_segment_info_db_file   = output_ids_path + os.sep + 'segmentInfo.db'

    #color_map_variable_name       = 'cmap'
    ids_upscale_factor            = 1

    def mkdir_safe( dir_to_make ):

        if not os.path.exists( dir_to_make ):
            execute_string = 'mkdir -p ' + '"' + dir_to_make + '"'
            print execute_string
            print
            os.system( execute_string )



    def save_hdf5( file_path, dataset_name, array ):
        
        hdf5             = h5py.File( file_path, 'w' )
        #dataset          = hdf5.create_dataset( dataset_name, data=array, chunks=True, compression='gzip' )
        dataset          = hdf5.create_dataset( dataset_name, data=array )
        hdf5.close()

        print file_path
        print



    def save_image( file_path, image ):

        image.save( file_path )
        print file_path
        print



    def load_id_image ( file_path ):
        print file_path
        ids = tif.imread( file_path ).astype(np.uint32)

        # if len( ids.shape ) == 3:
        #     ids = ids[ :, :, 0 ] + ids[ :, :, 1 ] * 2**8 + ids[ :, :, 2 ] * 2**16
        # else:
        #     # Read from pipeline format
        #     ids = ids.transpose() - 1

        return ids


        
    def sbdm_string_hash( in_string ):
        hash = 0
        for i in xrange(len(in_string)):
            hash = ord(in_string[i]) + (hash << 6) + (hash << 16) - hash
        return np.uint32(hash % 2**32)
        

    #color_map_mat_dict   = scipy.io.loadmat( original_input_color_map_path )
    #id_color_map         = color_map_mat_dict[ 'cmap' ]
    input_search_string  = original_input_ids_path + os.sep + '*.' + input_file_format
    files                = sorted( glob.glob( input_search_string ) )

    files = files[1595:]

    print "Found {0} input images in {1}".format( len(files), input_search_string )

    if len(files) > 0:

        #Only load names if there is something to name
        if generate_memorable_names:
            print 'Loading words for memorable name generation.'
            import nltk
            import random
            from nltk.corpus import wordnet
            
            # Seed based on input path so that names will be the same for multiple volumes
            random.seed( sbdm_string_hash( original_input_ids_path ) )

            nouns, verbs, adjectives, adverbs = [list(wordnet.all_synsets(pos=POS)) for POS in [wordnet.NOUN, wordnet.VERB, wordnet.ADJ, wordnet.ADV]]
            nouns_verbs = nouns + verbs
            adjectives_adverbs = adjectives + adverbs

            nouns_verbs = [x for x in nouns_verbs if not ( '_' in x.lemmas[0].name or '-' in x.lemmas[0].name )]
            adjectives_adverbs = [x for x in adjectives_adverbs if not ( '_' in x.lemmas[0].name or '-' in x.lemmas[0].name )]
            
            def make_memorable_name():

                while True:
                    word1 = random.choice(random.choice(adjectives_adverbs).lemmas).name
                    #ignore hyphenated words
                    if not ('_' in word1 or '-' in word1):
                        break

                while True:
                    word2 = random.choice(random.choice(nouns_verbs).lemmas).name
                    #ignore hyphenated words
                    if not ('_' in word2 or '-' in word2):
                        break

                return word1.capitalize() + word2.capitalize()

        else:
            print 'Using boring names.'


        id_max               = 0;
        id_counts            = np.zeros( 0, dtype=np.int64 );
        id_tile_list         = [];
        tile_index_z         = 1595

        # Make a color index
        #id_label = id_color_map[ :, 0 ] + id_color_map[ :, 1 ] * 2**8 + id_color_map[ :, 2 ] * 2**16
        #id_label_index = np.zeros( np.max(id_label) + 1, dtype=int )
        #id_label_index[ id_label ] = range(len(id_label))

        # Make a color map
        color_map = np.zeros( (ncolors + 1, 3), dtype=np.uint8 );
        for color_i in xrange( 1, ncolors + 1 ):
            rand_vals = np.random.rand(3);
            #color_map[ color_i ] = [ x*255 for x in colorsys.hsv_to_rgb( rand_vals[0], rand_vals[1] * 0.3 + 0.7, rand_vals[2] * 0.3 + 0.7 ) ];
            color_map[ color_i ] = [ rand_vals[0]*255, rand_vals[1]*255, rand_vals[2]*255 ];


        # Make a compressed id map
        if compress_ids:
            print "Compressing ids..."
            compressed_id_map = np.zeros( 1, dtype=np.uint32 );
            # Read all files so that ids will be consistent across for multiple volumes
            for file in files:
                original_input_ids_name = file
                original_ids = load_id_image( original_input_ids_name )

                unique_ids = np.unique( original_ids )
                max_unique = np.max( unique_ids )

                if max_unique >= compressed_id_map.shape[0]:
                    compressed_id_map.resize( max_unique + 1 )

                compressed_id_map[ unique_ids ] = 1

                print "Read file {0}. Max id = {1}.".format(file, compressed_id_map.shape[0])

            compressed_id_map[ 0 ] = 0
            valid_ids = np.nonzero(compressed_id_map)[0]
            compressed_id_map[ valid_ids ] = np.arange(1, len(valid_ids) + 1, dtype=np.uint32)

            print "Compressing {0} ids down to {1}.".format(compressed_id_map.shape[0], len(valid_ids))


        for file in files:

            original_input_ids_name = file

            original_ids = load_id_image( original_input_ids_name )
            #print original_ids, original_ids.dtype
            ## Grow regions until there are no boundaries

            ## Method 4 - watershed
            #original_ids = mahotas.cwatershed(np.zeros(original_ids.shape, dtype=np.uint32), original_ids, return_lines=False)

            if compress_ids:
                original_ids = compressed_id_map[original_ids]

            #boundaries = original_ids == 0
            #boundary_indices = np.nonzero(boundaries)
            #grow_count = 0
            #while len(boundary_indices[0]) > 0:

            #    ## Method 1 - dilate (slow)
            #    #original_ids[boundary_indices] = mahotas.dilate(original_ids)[boundary_indices] - 1

            #    ## Method 2 - conditional dilate (doesn't work)
            #    #original_ids[boundary_indices] = mahotas.cdilate(original_ids, boundaries==0)[boundary_indices] - 1

            #    ## Method 3 - direct shift
            #    shift_left = np.roll(original_ids, -1, 0);
            #    shift_left[-1,:] = 0
            #    shift_right = np.roll(original_ids, 1, 0);
            #    shift_right[0,:] = 0
            #    shift_up = np.roll(original_ids, -1, 1);
            #    shift_up[:,-1] = 0
            #    shift_down = np.roll(original_ids, 1, 1);
            #    shift_down[:,0] = 0
            #    original_ids[boundary_indices] = np.maximum(shift_left[boundary_indices], np.maximum(shift_right[boundary_indices], np.maximum(shift_up[boundary_indices], shift_down[boundary_indices])))


            #    boundaries = original_ids == 0
            #    boundary_indices = np.nonzero(boundaries)

            #    grow_count = grow_count + 1
            #    print "Grow count {0}: {1} boundary pixels remaining.".format(grow_count, len(boundary_indices[0]))
            
            current_image_counts = np.bincount( original_ids.ravel() )
            current_image_counts_ids = np.nonzero( current_image_counts )[0]
            current_max = np.max( current_image_counts_ids )
            if id_max < current_max:
                id_max = current_max;
                id_counts.resize( id_max + 1 );
           
            #print '1',current_image_counts_ids 
            if len(current_image_counts_ids) > 1:
                id_counts[ current_image_counts_ids ] = id_counts[ current_image_counts_ids ] + np.int64( current_image_counts [ current_image_counts_ids ] )
            
            ( original_image_num_pixels_x, original_image_num_pixels_y ) = original_ids.shape

            current_image_num_pixels_y = original_image_num_pixels_y
            current_image_num_pixels_x = original_image_num_pixels_x
            current_tile_data_space_y  = tile_num_pixels_y
            current_tile_data_space_x  = tile_num_pixels_x
            tile_index_w               = 0
            ids_stride                 = 1
            
            while current_image_num_pixels_y > tile_num_pixels_y / 2 or current_image_num_pixels_x > tile_num_pixels_x / 2:

                #current_pyramid_ids_path = output_pyramid_ids_path  + '\\' + 'w=' + '%08d' % ( tile_index_w )
                #current_pyramid_ids_name = current_pyramid_ids_path + '\\' + 'z=' + '%08d' % ( tile_index_z ) + '.hdf5'
                current_tile_ids_path    = output_tile_ids_path     + os.sep + 'w=' + '%08d' % ( tile_index_w ) + os.sep + 'z=' + '%08d' % ( tile_index_z )
            
                #current_pyramid_colors_path = output_pyramid_colors_path  + '\\' + 'w=' + '%08d' % ( tile_index_w )
                #current_pyramid_colors_name = current_pyramid_colors_path + '\\' + 'z=' + '%08d' % ( tile_index_z ) + '.png'
                #current_tile_colors_path    = output_tile_colors_path     + '\\' + 'w=' + '%08d' % ( tile_index_w ) + '\\' + 'z=' + '%08d' % ( tile_index_z )

                mkdir_safe( current_tile_ids_path )
                #mkdir_safe( current_pyramid_ids_path )
                #mkdir_safe( current_tile_colors_path )
                #mkdir_safe( current_pyramid_colors_path )

                current_ids = original_ids[ ::ids_stride, ::ids_stride ]
                #save_hdf5( current_pyramid_ids_name, 'IdMap', current_ids )
                            
                #current_colors       = id_color_map[ current_ids ]
                #current_colors_image = PIL.Image.fromarray( current_colors )
                #save_image( current_pyramid_colors_name, current_colors_image )
                
                num_tiles_y = int( math.ceil( float( current_image_num_pixels_y ) / tile_num_pixels_y ) )
                num_tiles_x = int( math.ceil( float( current_image_num_pixels_x ) / tile_num_pixels_x ) )

                for tile_index_y in range( num_tiles_y ):
                    for tile_index_x in range( num_tiles_x ):

                        y = tile_index_y * tile_num_pixels_y
                        x = tile_index_x * tile_num_pixels_x
                        
                        current_tile_ids_name    = current_tile_ids_path    + os.sep + 'y=' + '%08d' % ( tile_index_y ) + ','  + 'x=' + '%08d' % ( tile_index_x ) + '.hdf5'
                        #current_tile_colors_name = current_tile_colors_path + '\\' + 'y=' + '%08d' % ( tile_index_y ) + ','  + 'x=' + '%08d' % ( tile_index_x ) + '.png'

                        tile_ids                                                                   = np.zeros( ( tile_num_pixels_y, tile_num_pixels_x ), np.uint32 )
                        tile_ids_non_padded                                                        = current_ids[ y : y + tile_num_pixels_y, x : x + tile_num_pixels_x ]
                        tile_ids[ 0:tile_ids_non_padded.shape[0], 0:tile_ids_non_padded.shape[1] ] = tile_ids_non_padded[:,:]
                        save_hdf5( current_tile_ids_name, 'IdMap', tile_ids )

                        #tile_colors       = id_color_map[ tile_ids ]
                        #tile_colors_image = PIL.Image.fromarray( tile_colors )
                        #save_image( current_tile_colors_name, tile_colors_image )

                        #tile_index      = ( tile_index_x, tile_index_y, tile_index_z, tile_index_w )                
                        unique_tile_ids = np.unique( tile_ids )
                        
                        for unique_tile_id in unique_tile_ids:

                            id_tile_list.append( (unique_tile_id, tile_index_w, tile_index_z, tile_index_y, tile_index_x ) );
                            
                            #if not unique_tile_id in id_tile_map.keys():
                            #    id_tile_map[ unique_tile_id ] = []
                            #    
                            #id_tile_map[ unique_tile_id ].append( tile_index )
                                
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
                elif generate_memorable_names:
                    new_name = make_memorable_name()
                    while new_name in taken_names:
                        print 'Duplicate name - regenerating.'
                        new_name = make_memorable_name()
                    taken_names[ new_name ] = 1
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
