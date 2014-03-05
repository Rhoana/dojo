
// The DOJO namespace
var DOJO = DOJO || {};

DOJO.mode = null;
DOJO.modes = {
  pan_zoom:0, 
  merge:1
};
DOJO.threeD_active = false;
DOJO.link_active = false;
DOJO.mousemove_timeout = null;

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

    if (DOJO.mode != DOJO.modes.merge) {

      merge.style.border = '1px solid white';

      DOJO.mode = DOJO.modes.merge;

      // reset 3d view
      DOJO.viewer._controller.reset_fixed_3d_labels();
      DOJO.viewer._controller.reset_3d_labels();

    } else {

      merge.style.border = '';

      DOJO.mode = DOJO.modes.pan_zoom;

      DOJO.viewer._controller.end_merge();

      // reset 3d view
      DOJO.viewer._controller.reset_fixed_3d_labels();
      DOJO.viewer._controller.reset_3d_labels();      

    }

  };

  var threed = document.getElementById('3d');

  threed.onclick = function() {

    if (!DOJO.threeD_active) {

      threed.style.border = '1px solid white';

      document.getElementById('threeD').style.display = 'block';

      if (!DOJO.threeD) {
        DOJO.make_resizable();
        DOJO.init_threeD();
      }

      DOJO.threeD_active = true;

    } else {

      threed.style.border = '';

      document.getElementById('threeD').style.display = 'none';

      DOJO.threeD_active = false;

    }

  };

  var link = document.getElementById('link');

  link.onclick = function() {

    if (!DOJO.link_active) {

      link.style.border = '1px solid white';

      DOJO.link_active = true;

    } else {

      link.style.border = '';

      DOJO.viewer._controller.reset_cursors();

      DOJO.link_active = false;

    }


  };

};

DOJO.onleftclick = function(x, y) {

  // get pixel coordinates
  var i_j = DOJO.viewer.xy2ij(x,y);

  if (i_j[0] == -1) {
    DOJO.viewer._controller.reset_fixed_3d_labels();
    DOJO.viewer._controller.reset_3d_labels();
    return;
  }
  
  DOJO.viewer.get_segmentation_id(i_j[0], i_j[1], function(id) {
    
    // now we have the segmentation id
    if (DOJO.mode == DOJO.modes.merge) {

      if (!DOJO.viewer.is_locked(id))
        DOJO.viewer._controller.merge(id);
      
    } else {

      if (DOJO.threeD_active) {

        DOJO.viewer._controller._use_3d_labels = true;

        if (!DOJO.viewer._controller.is_3d_label(id)) {
          DOJO.viewer._controller.add_fixed_3d_label(id);
          DOJO.viewer._controller.add_3d_label(id);
        } else {
          DOJO.viewer._controller.remove_fixed_3d_label(id);
          DOJO.viewer._controller.remove_3d_label(id);
        }

      }

    }
    

  });

};

DOJO.onmousemove = function(x, y) {

  if (DOJO.link_active) {

    var i_j = DOJO.viewer.xy2ij(x,y);

    if (i_j[0] == -1) return;

    if (DOJO.mousemove_timeout) {
      clearTimeout(DOJO.mousemove_timeout);
    }

    DOJO.mousemove_timeout = setTimeout(function() {
      DOJO.viewer._controller.send_mouse_move([i_j[0], i_j[1], DOJO.viewer._camera._z]);
    }, 100);

  }

};

DOJO.update_slice_number = function(n) {

  var slicenumber = document.getElementById('slicenumber');
  slicenumber.innerHTML = n+'/'+DOJO.viewer._image.max_z_tiles;

  // reset the cursors if we are in collab mode
  if (DOJO.link_active) {
    DOJO.viewer._controller.reset_cursors();
  }

};

DOJO.update_label = function(x, y) {

  var i_j = DOJO.viewer.xy2ij(x,y);

  var label = document.getElementById('label');

  if (i_j[0] == -1) {
    label.innerHTML = 'Label n/a';
    if (DOJO.mode != DOJO.modes.merge)
      DOJO.viewer._controller.reset_3d_labels();
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

DOJO.update_log = function(input) {

  var log = document.getElementById('log');

  // add timestamp
  var message = timestamp() + ' ' + input.message;

  log.innerHTML = message + '<br>' + log.innerHTML;

};

DOJO.make_resizable = function() {

// Using DragResize is simple!
// You first declare a new DragResize() object, passing its own name and an object
// whose keys constitute optional parameters/settings:

var dragresize = new DragResize('dragresize',
 { handles: ['bl'], minWidth: 300, minHeight: 300, minLeft: 20, minTop: 20, maxLeft: 600, maxTop: 600 });

// Optional settings/properties of the DragResize object are:
//  enabled: Toggle whether the object is active.
//  handles[]: An array of drag handles to use (see the .JS file).
//  minWidth, minHeight: Minimum size to which elements are resized (in pixels).
//  minLeft, maxLeft, minTop, maxTop: Bounding box (in pixels).

// Next, you must define two functions, isElement and isHandle. These are passed
// a given DOM element, and must "return true" if the element in question is a
// draggable element or draggable handle. Here, I'm checking for the CSS classname
// of the elements, but you have have any combination of conditions you like:

dragresize.isElement = function(elm)
{
 if (elm.className && elm.className.indexOf('threeDpanel') > -1) return true;
};
dragresize.isHandle = function(elm)
{
 if (elm.className && elm.className.indexOf('threeDpanel') > -1) return true;
};

// You can define optional functions that are called as elements are dragged/resized.
// Some are passed true if the source event was a resize, or false if it's a drag.
// The focus/blur events are called as handles are added/removed from an object,
// and the others are called as users drag, move and release the object's handles.
// You might use these to examine the properties of the DragResize object to sync
// other page elements, etc.

dragresize.ondragfocus = function() { };
dragresize.ondragstart = function(isResize) { };
dragresize.ondragmove = function(isResize) { fire_resize_event(); };
dragresize.ondragend = function(isResize) { };
dragresize.ondragblur = function() { };

// Finally, you must apply() your DragResize object to a DOM node; all children of this
// node will then be made draggable. Here, I'm applying to the entire document.
dragresize.apply(document);



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
  slice.transform.translateZ(-vol.dimensions[2]/2*vol.spacing[2]);
  r.add(slice);

  DOJO.threeD.slice = slice;

  r.camera.position = [-100,-400,-700]

  r.render(); // ..and render it

  r.onShowtime = function() {

    vol.volumeRendering = true;
    vol.opacity = 0.5;

  }

};