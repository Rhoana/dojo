var J = J || {};

J.interactor = function(viewer) {

  this._viewer = viewer;

  this._scale = 1;
  this._originx = 0;
  this._originy = 0;  

  this._left_down = false;
  this._right_down = false;

  this._last_mouse = [0,0];

  this._last_offset = [0,0];

  this.init();

};

J.interactor.prototype.init = function() {

  // mouse move
  this._viewer._canvas.onmousemove = this.onmousemove.bind(this);

  // mouse down and up
  this._viewer._canvas.onmousedown = this.onmousedown.bind(this);
  this._viewer._canvas.onmouseup = this.onmouseup.bind(this);
  this._viewer._canvas.oncontextmenu = function() { return false; };

  // mouse wheel
  this._viewer._canvas.onmousewheel = this.onmousewheel.bind(this);



};

J.interactor.prototype.onmousemove = function(e) {

  var x = e.clientX;
  var y = e.clientY;

  var u_v = this._viewer.xy2uv(x, y);

  // jump out if we are not inside the real image data
  // if (u_v[0] == -1 || u_v[1] == -1) {
  //   return;
  // }

  if (this._left_down) {
    
  } else if (this._right_down) {
    // pan
    this._viewer._camera.pan(x-this._last_mouse[0], y-this._last_mouse[1]);    
  }

  //console.log(this._left_down, e.clientX, e.clientY, u_v[0], u_v[1], this._viewer._camera._view[0], this._viewer._camera._view[6]);

  // console.log('XY', x, y);
  // console.log('UV', u_v[0], u_v[1]);
  // console.log('IJ', this._viewer.xy2ij(x, y));
  // console.log('SCALE', this._viewer._camera._view[0])
  // console.log('LASTOFFSET', this._last_offset);

  this._last_mouse = [x, y];
  this._last_offset = [this._viewer._camera._view[6], this._viewer._camera._view[7]];

};

J.interactor.prototype.onmousedown = function(e) {

  if (e.button == 0) {
    // left
    this._left_down = true;
  } else if (e.button == 2) {
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

  var canvas = this._viewer._canvas;
  var context = this._viewer._context;

  var x = e.clientX;
  var y = e.clientY;
  var u_v = this._viewer.xy2uv(x,y);
  
  if (u_v[0] == -1 || u_v[1] == -1) {
    return;
  }

  var wheel_sign = sign(e.wheelDelta/120);

  // clamp zooming
  if (this._viewer._camera._view[0] + wheel_sign <= 0) return;
  if (this._viewer._camera._view[0] + wheel_sign > 20) return;

  var old_scale = this._viewer._camera._view[0];

  // perform zooming
  this._viewer._camera._view[0] += wheel_sign;
  this._viewer._camera._view[4] += wheel_sign;

  var new_scale = this._viewer._camera._view[0];

  var u_new = u_v[0]/old_scale * new_scale;
  var v_new = u_v[1]/old_scale * new_scale;

  // translate to correct point
  this._viewer._camera._view[6] -= wheel_sign * Math.abs(u_v[0] - u_new);
  this._viewer._camera._view[7] -= wheel_sign * Math.abs(u_v[1] - v_new);

};


