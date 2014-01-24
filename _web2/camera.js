var J = J || {};

J.camera = function(viewer) {

  this._viewer = viewer;
  this._loader = this._viewer._loader;

  this._z = 0;

  // a c e
  // b d f
  // 0 0 1
  this._view = [1, 0, 0, 0, 1, 0, 0, 0, 1];

  this._zoom_level = 1;

};


J.camera.prototype.center = function() {

  this._view[6] = this._viewer._width/2 - 512/2;
  this._view[7] = this._viewer._height/2 - 512/2;
  // this._view[6] = this._viewer._width/2 - this._view[0]*512/2;
  // this._view[7] = this._viewer._height/2 - this._view[4]*512/2;

};

J.camera.prototype.auto_scale = function() {

  // var _w_scale = this._viewer._width / 512*this._viewer._zoom_level;
  // var _h_scale = this._viewer._height / 512*this._viewer._zoom_level;

  // var _auto_scale = parseInt(Math.min(_w_scale, _h_scale),10);

  // this._view[0] = _auto_scale;
  // this._view[4] = _auto_scale;

};

J.camera.prototype.reset = function() {

  this.auto_scale();
  this.center();

};


///

J.camera.prototype.zoom = function(x, y, delta) {
  
  var u_v = this._viewer.xy2uv(x,y);

  //console.log('zoom')

  // only do stuff if we are over the image data
  if (u_v[0] == -1 || u_v[1] == -1) {
    console.log('out')
    return;
  }  

  var wheel_sign = sign(delta/120);

  //var future_zoom_level = this._view[0] + wheel_sign;
  var future_zoom_level = this._zoom_level - wheel_sign;

  // clamp zooming
  if (future_zoom_level < 0 || future_zoom_level == this._viewer._image.zoomlevel_count) return;

  // trigger tile loading
  //this._loader.load_tile(x, y, this._z, this._view[0], future_zoom_level);
  this._loader.load_tiles(x, y, this._z, this._zoom_level, future_zoom_level);

  //var old_scale = this._view[0];
  var old_scale_w = this._viewer._image.zoom_levels[this._zoom_level][2];//this._zoom_level;
  var old_scale_h = this._viewer._image.zoom_levels[this._zoom_level][3];

  // perform zooming
  //this._view[0] += wheel_sign;
  //this._view[4] += wheel_sign;
  this._zoom_level -= wheel_sign;

  //var new_scale = this._view[0];
  var new_scale_w = this._viewer._image.zoom_levels[this._zoom_level][2];
  var new_scale_h = this._viewer._image.zoom_levels[this._zoom_level][3];

  // var u_new = u_v[0] * new_scale;
  // var v_new = u_v[1] * new_scale;
  // if (old_scale != 0) {

    u_new = u_v[0]/old_scale_w * new_scale_w;
    v_new = u_v[1]/old_scale_h * new_scale_h;

  // }

  // translate to correct point
  this._view[6] -= wheel_sign * Math.abs(u_v[0] - u_new);
  this._view[7] -= wheel_sign * Math.abs(u_v[1] - v_new);

};

J.camera.prototype.pan = function(dx, dy) {

  this._view[6] += dx;
  this._view[7] += dy;

};