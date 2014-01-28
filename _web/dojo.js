
// The DOJO namespace
var DOJO = DOJO || {};

DOJO.mode = null;
DOJO.modes = {
  pan_zoom:0, 
  merge:1
};

DOJO.init = function() {

  DOJO.viewer = new J.viewer('dojo1');

  DOJO.setup_buttons();

};

DOJO.setup_buttons = function() {

  var merge = document.getElementById('merge');

  merge.onclick = function() {

    if (DOJO.mode != DOJO.modes.merge) {

      merge.style.border = '1px solid white';

      DOJO.mode = DOJO.modes.merge;

    } else {

      merge.style.border = '';

      DOJO.mode = DOJO.modes.pan_zoom;

    }

  };

};

DOJO.onleftclick = function(x, y) {

  // get pixel coordinates
  var i_j = DOJO.viewer.xy2ij(x,y);
  
  DOJO.viewer.get_segmentation_id(i_j[0], i_j[1], function(id) {
    console.log(i_j, id);
  });

};

