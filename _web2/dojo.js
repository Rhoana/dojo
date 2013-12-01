
// The DOJO namespace
var DOJO = DOJO || {};

// the openseadragon viewer
DOJO.toc = {'images':null,'segmentations':null};
DOJO.viewer = null;
DOJO.tileSources = [];
DOJO.overlayTileSources = [];
DOJO.colormap = null;
DOJO.idmap = {};
DOJO.first_id = null;
DOJO.second_id = null;

DOJO.init = function() {

  // start the async chain by getting the contents from the server
  DOJO.get_contents();

};

/**
 *
 */
DOJO.get_contents = function() {

  $.ajax({url:'/image/contents'}).done( function(e) {

    var images = JSON.parse(e);

    DOJO.toc.images = images;

    DOJO.build_tilesources();

  });

  $.ajax({url:'/segmentation/contents'}).done( function(e) {

    var segmentations = JSON.parse(e);

    DOJO.toc.segmentations = segmentations;

    DOJO.build_tilesources();

  });

};

DOJO.build_tilesources = function() {

  if (!DOJO.toc['images'] || !DOJO.toc['segmentations']) {
    // we don't have the complete TOC yet
    return;
  }

  var no_images = DOJO.toc.images.max_z_tiles;
  var no_segmentations = DOJO.toc.segmentations.max_z_tiles;

  for (var i=0; i<no_images; i++) {

    DOJO.tileSources.push('/image/'+pad(i,8)+'/');

  }

  for (var s=0; s<no_segmentations; s++) {

    DOJO.overlayTileSources.push('/segmentation/'+pad(s,8)+'/');

  }  

  if (DOJO.toc.segmentations.colormap) {

    DOJO.get_colormap();

  }

};

DOJO.get_colormap = function() {

  $.ajax({url:'/segmentation/colormap'}).done( function(e) {

    DOJO.colormap = JSON.parse(e);

    DOJO.create_viewer();

  });

};

/**
 *
 */
DOJO.create_viewer = function() {

  // DOJO.viewer = OpenSeadragon({
  //   id: 'dojo1',
  //   prefixUrl: '/dojo/lib/openseadragon/images/',
  //   blendTime: 0,
  //   showNavigator: false,
  //   maxZoomPixelRatio: 4,  
  //   zCacheSize: 1,
  //   preserveViewport: true,
  //   tileSources: DOJO.tileSources,
  //   overlayTileSources: DOJO.overlayTileSources,
  //   colormap: DOJO.colormap,
  //   idmap: DOJO.idmap
  // });

  DOJO.viewer = new DOJO.renderer('dojo1');
  DOJO.viewer.open(DOJO.tileSources);
  // DOJO.setup_interaction();

};

/**
 *
 */
DOJO.setup_interaction = function() {

  DOJO.viewer.addHandler('canvas-click', function(e){
    
    console.log('Trying the merge');

    var image_coords = DOJO.viewer.viewport.viewportToImageCoordinates(DOJO.viewer.viewport.pointFromPixel(e.position, true));

    var x = Math.floor(image_coords.x/2);
    var y = Math.floor(image_coords.y/2);

    var image = new Uint32Array(DOJO.viewer.overlayDrawer.tilesMatrix[9][0][0].image.buffer);
        
    if (!image) {
      console.log('error');
      return;
    }

    var id = image[y*512 + x];

    if (!DOJO.first_id) {
      DOJO.first_id = id;
    } else if (DOJO.first_id != DOJO.second_id) {
      DOJO.second_id = id;
      DOJO.idmap[DOJO.first_id] = DOJO.second_id;
      console.log('Merging', DOJO.first_id, DOJO.second_id);
      DOJO.first_id = null;
      DOJO.second_id = null;
    } else {
      DOJO.first_id = null;
      DOJO.second_id = null;      
    }

  });

  window.onkeypress = function(e) {
    if (e.charCode == 113) {

      DOJO.viewer.goToPage(DOJO.viewer.currentPage()+1);

    } else if (e.charCode == 97) {

      DOJO.viewer.goToPage(DOJO.viewer.currentPage()-1);

    }
  }

};
