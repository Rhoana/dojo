
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