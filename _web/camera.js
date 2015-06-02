var J = J || {};

J.camera = function(viewer) {

  this._viewer = viewer;
  this._loader = this._viewer._loader;

  this._x = 0;
  this._y = 0;
  this._z = 0;
  this._w = 1;

  // we need to cache this here since manipulations to the camera matrix might mess things up
  this._i_j = [0, 0];

  // a c e
  // b d f
  // 0 0 1
  this._view = [1, 0, 0, 0, 1, 0, 0, 0, 1];

  this._linear_zoom_factor = 0.3;

  this._zoom_end_timeout = null;

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

J.camera.prototype.zoom_end = function() {

  // this._loader.load_tiles(this._x, this._y, this._z, this._w, this._w, false);



};

J.camera.prototype.jump = function(i, j, k) {

  this._z = k;

  var x_y_z = this._viewer.ijk2xyz(i, j, k);

  if (DOJO.threeD)
    DOJO.threeD.slice.transform.matrix[14] = x_y_z[2];

  DOJO.update_slice_number(k+1);

  this._loader.load_tiles(i, j, k, this._w, this._w, false);

};

///
J.camera.prototype.zoom = function(x, y, delta) {

  // don't zoom when using adjust or split
  if (this._viewer._controller._split_mode != -1) return;
  if (this._viewer._controller._adjust_mode != -1 && !DOJO.single_segment) return;

  // perform linear zooming until a new image zoom level is reached
  // then reset scale to 1 and show the image

  this._viewer._controller.clear_exclamationmarks();
  this._viewer._controller.reset_cursors();

  var u_v = this._viewer.xy2uv(x,y);

  // only do stuff if we are over the image data
  if (u_v[0] == -1 || u_v[1] == -1) {
    return;
  }

  if (this._zoom_end_timeout) clearTimeout(this._zoom_end_timeout);

  var wheel_sign = sign(delta/120);

  var future_w = this._w - wheel_sign;
  var future_zoom_level = Math.round((this._view[0] + wheel_sign * this._linear_zoom_factor)*10)/10;

  // clamp the linear pixel zoom
  if (future_zoom_level <= 0.7 || future_zoom_level >= 5.0) return;

  if (future_w >= 0 && future_w < this._viewer._image.zoomlevel_count) {
    // start loading the tiles immediately but set no_draw to true
    this._loader.load_tiles(x, y, this._z, this._w, future_w, true);
  }

  var old_scale = this._view[0];

  // perform pixel zooming
  this._view[0] = future_zoom_level;
  this._view[4] = future_zoom_level;

  // console.log(future_zoom_level);

  var new_scale = future_zoom_level;

  // here we check if we pass an image zoom level, if yes we need to draw other tiles
  if ((new_scale >= 2 && wheel_sign > 0) || (new_scale-this._linear_zoom_factor < 1 && wheel_sign < 0)) {

    future_zoom_level = this._w - wheel_sign;

    // clamp zooming
    if (future_zoom_level >= 0 && future_zoom_level < this._viewer._image.zoomlevel_count) {

      // this._viewer.loading(true);

      // this time we really draw (no_draw = false)
      this._loader.load_tiles(x, y, this._z, this._w, future_zoom_level, false);
      
      this._w = future_zoom_level;

      if (wheel_sign < 0) {

        // zooming out
        old_scale *= 2;
        new_scale *= 2;
        
      } else {

        // zooming in
        new_scale /= 2;
        old_scale /= 2;


      }

      this._view[0] = new_scale;
      this._view[4] = new_scale;

    }    
    
  }

  u_new = u_v[0]/old_scale * new_scale;
  v_new = u_v[1]/old_scale * new_scale;

  // translate to correct point
  this._view[6] -= wheel_sign * Math.abs(u_v[0] - u_new);
  this._view[7] -= wheel_sign * Math.abs(u_v[1] - v_new);  

  this._zoom_end_timeout = setTimeout(this.zoom_end.bind(this), 60);

};

J.camera.prototype.pan = function(dx, dy) {

  this._view[6] += dx;
  this._view[7] += dy;

  this._viewer._controller.clear_exclamationmarks();
  this._viewer._controller.reset_cursors();

  this._loader.load_tiles(this._x, this._y, this._z, this._w, this._w, false);

};

J.camera.prototype.slice_up = function() {

  if (this._z == this._viewer._image.max_z_tiles-1) return;

  // dont slice when using tools
  if (this._viewer._controller._split_mode != -1) return;
  if (this._viewer._controller._adjust_mode != -1 && !DOJO.single_segment) return;

  this._viewer._controller.clear_exclamationmarks();
  this._viewer._controller.reset_cursors();

  this._viewer.loading(true);
  this._loader.load_tiles(this._x, this._y, ++this._z, this._w, this._w, false);

  if (DOJO.threeD)
    DOJO.threeD.slice.transform.translateZ(DOJO.threeD.volume.spacing[2]);

  DOJO.update_slice_number(this._z+1);

};

J.camera.prototype.slice_down = function() {

  if (this._z == 0) return;

  // dont slice when using tile tools
  if (this._viewer._controller._split_mode != -1) return;
  if (this._viewer._controller._adjust_mode != -1 && !DOJO.single_segment) return;

  this._viewer._controller.clear_exclamationmarks();
  this._viewer._controller.reset_cursors();

  this._viewer.loading(true);
  this._loader.load_tiles(this._x, this._y, --this._z, this._w, this._w, false);

  if (DOJO.threeD)
    DOJO.threeD.slice.transform.translateZ(-DOJO.threeD.volume.spacing[2]);

  DOJO.update_slice_number(this._z+1);

};
