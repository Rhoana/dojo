var J = J || {};

J.interactor = function(viewer) {

  this._viewer = viewer;
  this._camera = this._viewer._camera;

  this._left_down = false;
  this._right_down = false;

  this._last_mouse = [0,0];

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

  // keyboard
  window.onkeydown = this.onkeydown.bind(this);

};

J.interactor.prototype.onmousemove = function(e) {

  var x = e.clientX;
  var y = e.clientY;

  var u_v = this._viewer.xy2uv(x, y);

  if (this._left_down) {
    
  } else if (this._right_down) {
    // pan
    this._camera.pan(x-this._last_mouse[0], y-this._last_mouse[1]);    
  }

  this._last_mouse = [x, y];

};

J.interactor.prototype.onmousedown = function(e) {

  if (e.button == 0) {
    // left
    this._left_down = true;
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

  this._camera.zoom(e.clientX, e.clientY, e.wheelDelta);

};

J.interactor.prototype.onkeydown = function(e) {
  
  if (!this._viewer._image_buffer_ready) return;

  if (e.keyCode == 81) {
  
    this._camera.slice_up();

  } else if (e.keyCode == 65) {
  
    this._camera.slice_down();

  }

};
