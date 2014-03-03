
// The DOJO namespace
var DOJO = DOJO || {};

DOJO.mode = null;
DOJO.modes = {
  pan_zoom:0, 
  merge:1,
  threeD:2
};

DOJO.init = function() {

  DOJO.viewer = new J.viewer('dojo1');
  DOJO.viewer.init(function() {

    DOJO.update_slice_number(1);

  });

  DOJO.setup_buttons();

};

DOJO.setup_buttons = function() {

  var merge = document.getElementById('merge');

  merge.onclick = function() {

    threed.style.border = '';

    if (DOJO.mode != DOJO.modes.merge) {

      merge.style.border = '1px solid white';

      DOJO.mode = DOJO.modes.merge;

    } else {

      merge.style.border = '';

      DOJO.mode = DOJO.modes.pan_zoom;

      DOJO.viewer._controller.end_merge();

    }

  };

  var threed = document.getElementById('3d');

  threed.onclick = function() {

    merge.style.border = '';

    if (DOJO.mode != DOJO.modes.threeD) {

      threed.style.border = '1px solid white';

      DOJO.mode = DOJO.modes.threeD;

    } else {

      threed.style.border = '';

      DOJO.mode = DOJO.modes.pan_zoom;

      DOJO.viewer._controller.activate(null);
      DOJO.viewer._controller.highlight(null);      

    }

  };

};

DOJO.onleftclick = function(x, y) {

  // get pixel coordinates
  var i_j = DOJO.viewer.xy2ij(x,y);

  if (i_j[0] == -1) return;
  
  DOJO.viewer.get_segmentation_id(i_j[0], i_j[1], function(id) {
    
    // now we have the segmentation id

    if (DOJO.mode == DOJO.modes.threeD) {
      threeD_window = window.open("3d/?id=" + id,"","location=no,width=800,height=600");

      DOJO.viewer._controller.activate(id);
    } else if (DOJO.mode == DOJO.modes.merge) {

      if (!DOJO.viewer.is_locked(id))
        DOJO.viewer._controller.merge(id);
      
    }
    

  });

};

DOJO.update_slice_number = function(n) {

  var slicenumber = document.getElementById('slicenumber');
  slicenumber.innerHTML = n+'/'+DOJO.viewer._image.max_z_tiles;

};

DOJO.update_label = function(x, y) {

  var i_j = DOJO.viewer.xy2ij(x,y);

  var label = document.getElementById('label');

  if (i_j[0] == -1) {
    label.innerHTML = 'Label n/a';
    return;
  }

  DOJO.viewer.get_segmentation_id(i_j[0], i_j[1], function(id) {

    if (!id) return;

    var color = DOJO.viewer.get_color(id);
    var color_hex = rgbToHex(color[0], color[1], color[2]);

    label.innerHTML = 'Label <font color="' + color_hex + '">' + id + '</font>';

    DOJO.viewer._controller.highlight(id);

  });

};

DOJO.update_log = function(message) {

  var log = document.getElementById('log');

  // add timestamp
  message = timestamp() + ' ' + message;

  log.innerHTML = message + '<br>' + log.innerHTML;

};

DOJO.init_threeD = function() {

  DOJO.threeD = DOJO.threeD || {};

  // create and initialize a 3D renderer
  var r = new X.renderer3D();
  r.container = 'threeD';
  r.init();

  var vol = new X.volume();
  vol.dimensions = [512,512,75];
  vol.spacing = [1,1,3];
  vol.file = '/image/volume/00000001/&.RZ';
  //vol.file = 'http://localhost:1337/segmentation/volume/00000001/&.RZ';
  vol.labelmap.use32bit = true;
  vol.labelmap.file = '/segmentation/volume/00000001/&.RZ';
  vol.labelmap.dimensions = vol.dimensions;
  vol.labelmap.opacity = 0.5;
  // vol.labelmap._dirty = true;


  DOJO.threeD.volume = vol;
  DOJO.threeD.renderer = r;  

  DOJO.viewer._controller.update_threeD();

  r.add(vol);
  // r.add(s)

  
  var box = new X.object();
  box.points = new X.triplets(72);
  box.normals = new X.triplets(72);
  box.type = 'LINES';
  var _x = vol.dimensions[0]*vol.spacing[0] / 2;
  var _y = vol.dimensions[1]*vol.spacing[1] / 2;
  var _z = vol.dimensions[2]*vol.spacing[2] / 2;
  box.points.add(_x, -_y, _z);
  box.points.add(-_x, -_y, _z);
  box.points.add(_x, _y, _z);
  box.points.add(-_x, _y, _z);
  box.points.add(_x, -_y, -_z);
  box.points.add(-_x, -_y, -_z);
  box.points.add(_x, _y, -_z);
  box.points.add(-_x, _y, -_z);
  box.points.add(_x, -_y, _z);
  box.points.add(_x, -_y, -_z);
  box.points.add(-_x, -_y, _z);
  box.points.add(-_x, -_y, -_z);
  box.points.add(_x, _y, _z);
  box.points.add(_x, _y, -_z);
  box.points.add(-_x, _y, _z);
  box.points.add(-_x, _y, -_z);
  box.points.add(_x, _y, _z);
  box.points.add(_x, -_y, _z);
  box.points.add(-_x, _y, _z);
  box.points.add(-_x, -_y, _z);
  box.points.add(-_x, _y, -_z);
  box.points.add(-_x, -_y, -_z);
  box.points.add(_x, _y, -_z);
  box.points.add(_x, -_y, -_z);
  for ( var i = 0; i < 24; ++i) {
    box.normals.add(0, 0, 0);
  }
  r.add(box);

  var slice = new X.object();
  slice.points = new X.triplets(24);
  slice.normals = new X.triplets(24);
  slice.type = 'LINES';
  slice.points.add(_x, _y, 0);
  slice.points.add(-_x, _y, 0);
  slice.points.add(_x, _y, 0);
  slice.points.add(_x, -_y, 0);
  slice.points.add(_x, -_y, 0);  
  slice.points.add(-_x, -_y, 0);  
  slice.points.add(-_x, _y, 0);  
  slice.points.add(-_x, -_y, 0);
  slice.color = [1,0,0];
  for ( var i = 0; i < 8; ++i) {
    slice.normals.add(0, 0, 0);
  }
  slice.transform.translateZ(-vol.dimensions[2]*vol.spacing[2]);
  r.add(slice);

  DOJO.threeD.slice = slice;

  r.camera.position = [-100,-400,-700]

  r.render(); // ..and render it

  r.onShowtime = function() {

    vol.volumeRendering = true;
    vol.opacity = 0.3;

  }


};