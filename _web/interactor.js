var J = J || {};

J.interactor = function(viewer) {

  this._viewer = viewer;
  this._camera = this._viewer._camera;

  this._left_down = false;
  this._right_down = false;

  this._last_mouse = [0,0];

  this._keypress_callback = null;

  this.init();

};

J.interactor.prototype.init = function() {

  // mouse move
  this._viewer._canvas.onmousemove = this.onmousemove.bind(this);

  // mouse down and up
  this._viewer._canvas.onmousedown = this.onmousedown.bind(this);
  this._viewer._canvas.onmouseup = this.onmouseup.bind(this);
  // disable the context menu
  this._viewer._canvas.oncontextmenu = function() { return false; };

  // mouse wheel
  this._viewer._canvas.onmousewheel = this.onmousewheel.bind(this);
  // for firefox
  this._viewer._canvas.addEventListener('DOMMouseScroll', this.onmousewheel.bind(this), false);

  // keyboard
  window.onkeydown = this.onkeydown.bind(this);

};

J.interactor.prototype.onmousemove = function(e) {

  var x = e.clientX;
  var y = e.clientY;

  this._camera._x = x;
  this._camera._y = y;
  this._camera._i_j = this._viewer.xy2ij(x, y);

  //var u_v = this._viewer.xy2uv(x, y);

  DOJO.onmousemove(x, y);

  if (this._left_down) {

  } else if (this._right_down) {
    // pan
    this._camera.pan(x-this._last_mouse[0], y-this._last_mouse[1]);    
  } else {
    // show current label
    DOJO.update_label(x, y);
  }

  this._last_mouse = [x, y];

};

J.interactor.prototype.onmousedown = function(e) {

  var x = e.clientX;
  var y = e.clientY;

  this._camera._x = x;
  this._camera._y = y;  
  this._camera._i_j = this._viewer.xy2ij(x, y);

  if (e.button == 0) {
    // left
    this._left_down = true;

    DOJO.onleftclick(x, y);

  } else if (e.button == 2) {
    // right
    this._right_down = true;
  }

};

J.interactor.prototype.onmouseup = function(e) {

if (e.button == 0) {
  // left
  this._left_down = false;
} else if (e.button == 2) {
  // right
  this._right_down = false;
}

};

J.interactor.prototype.onmousewheel = function(e) {

  var delta = e.wheelDelta || -e.detail;

  var x = e.clientX;
  var y = e.clientY;

  this._camera._x = x;
  this._camera._y = y;  
  this._camera._i_j = this._viewer.xy2ij(x, y);

  this._camera.zoom(x, y, delta);

};

J.interactor.prototype.onkeydown = function(e) {
  
  if (!this._viewer._image_buffer_ready) return;

  if (this._keypress_callback) return;
  
  // 81: Q
  // 65: A TOGGLE BORDERS
  // 87: W SLICE UP
  // 83: S SLICE DOWN
  // 67: C ZOOM IN
  // 88: X ZOOM OUT
  // 90: Z MARK PROBLEM
  // 76: LOCK/UNLOCK

  if (e.keyCode == 87) {
  
    this._keypress_callback = setTimeout(function() {
      this._camera.slice_up();
      this._keypress_callback = null;
    }.bind(this),10);   

  } else if (e.keyCode == 83) {
  
    this._keypress_callback = setTimeout(function() {
      this._camera.slice_down();
      this._keypress_callback = null;
    }.bind(this),10);   

  } else if (e.keyCode == 67) {

    this._keypress_callback = setTimeout(function() {
      this._camera.zoom(this._camera._x, this._camera._y, 1);
      this._keypress_callback = null;
    }.bind(this),10); 

  } else if (e.keyCode == 88) {

    this._keypress_callback = setTimeout(function() {
      this._camera.zoom(this._camera._x, this._camera._y, -1);
      this._keypress_callback = null;
    }.bind(this),10); 

  } else if (e.keyCode == 65) {

    this._keypress_callback = setTimeout(function() {
      this._viewer.toggle_borders();
      this._keypress_callback = null;
    }.bind(this),10); 

  } else if (e.keyCode == 76) {

    this._keypress_callback = setTimeout(function() {
      this._viewer._controller.lock(this._camera._x, this._camera._y);
      this._keypress_callback = null;
    }.bind(this),10); 

  } else if (e.keyCode == 90) {

    this._keypress_callback = setTimeout(function() {
      this._viewer._controller.add_exclamationmark(this._camera._x, this._camera._y);
      this._keypress_callback = null;
    }.bind(this),10); 

  }

};
