var J = J || {};

J.camera = function(viewer) {

  this._viewer = viewer;
  this._loader = this._viewer._loader;

  this._x = 0;
  this._y = 0;
  this._z = 0;
  this._w = 1;

  // we need to cache this here since manipulations to the camera matrix might mess things up
  this._i_j = [-1, -1];

  // a c e
  // b d f
  // 0 0 1
  this._view = [1, 0, 0, 0, 1, 0, 0, 0, 1];

  this._linear_zoom_factor = 0.1;

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

  // perform linear zooming until a new image zoom level is reached
  // then reset scale to 1 and show the image

  var u_v = this._viewer.xy2uv(x,y);

  // only do stuff if we are over the image data
  if (u_v[0] == -1 || u_v[1] == -1) {
    return;
  }

  var wheel_sign = sign(delta/120);

  var future_w = this._w - wheel_sign;

  var future_zoom_level = this._view[0] + wheel_sign * this._linear_zoom_factor;

  // clamp the linear pixel zoom
  if (future_zoom_level < 1.0 || future_zoom_level >= 5.0) return;

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
  if ((new_scale >= 2 && wheel_sign > 0) || (new_scale <= 1 && wheel_sign < 0)) {

    future_zoom_level = this._w - wheel_sign;

    // clamp zooming
    if (future_zoom_level >= 0 && future_zoom_level < this._viewer._image.zoomlevel_count) {

      console.log('new tile', future_zoom_level);
      // console.log('old scale', old_scale);
      // console.log('new scale', new_scale)

      //this._viewer.loading(true);

      // this time we really draw (no_draw = false)
      // setTimeout(function() {
      this._loader.load_tiles(x, y, this._z, this._w, future_zoom_level, false);
      // }.bind(this), 100);
      this._w = future_zoom_level;

      // console.log('w', future_zoom_level);

      // reset pixel size to 1
      this._view[0] = 1;
      this._view[4] = 1;


      if (wheel_sign < 0) {
        console.log(old_scale, new_scale);
        old_scale = 2.2;
        new_scale = 2;
        this._view[0] = 2;
        this._view[4] = 2;      
      }
      //   this._view[6] += 256;
      //   this._view[7] += 256;  
      //   // return;    
      // }
      
    }    
    
  }

  u_new = u_v[0]/old_scale * new_scale;
  v_new = u_v[1]/old_scale * new_scale;

  // translate to correct point
  this._view[6] -= wheel_sign * Math.abs(u_v[0] - u_new);
  this._view[7] -= wheel_sign * Math.abs(u_v[1] - v_new);  

};

J.camera.prototype.image_zoom = function(x, y, delta) {

  var u_v = this._viewer.xy2uv(x,y);

  //console.log('zoom')

  // only do stuff if we are over the image data
  if (u_v[0] == -1 || u_v[1] == -1) {
    console.log('out')
    return;
  }  

  this._viewer.loading(true);

  var wheel_sign = sign(delta/120);

  //var future_zoom_level = this._view[0] + wheel_sign;
  var future_zoom_level = this._w - wheel_sign;

  // clamp zooming
  if (future_zoom_level < 0 || future_zoom_level == this._viewer._image.zoomlevel_count) {
    this._viewer.loading(false);
    return;
  }

  // trigger tile loading
  //this._loader.load_tile(x, y, this._z, this._view[0], future_zoom_level);
  this._loader.load_tiles(x, y, this._z, this._w, future_zoom_level);

  //var old_scale = this._view[0];
  var old_scale_w = this._viewer._image.zoom_levels[this._w][2];//this._zoom_level;
  var old_scale_h = this._viewer._image.zoom_levels[this._w][3];

  // perform zooming
  //this._view[0] += wheel_sign;
  //this._view[4] += wheel_sign;
  this._x = x;
  this._y = y;
  this._w -= wheel_sign;

  //var new_scale = this._view[0];
  var new_scale_w = this._viewer._image.zoom_levels[this._w][2];
  var new_scale_h = this._viewer._image.zoom_levels[this._w][3];

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

J.camera.prototype.slice_up = function() {

  if (this._z == this._viewer._image.max_z_tiles-1) return;

  this._viewer.loading(true);
  this._loader.load_tiles(this._x, this._y, ++this._z, this._w, this._w);

  DOJO.update_slice_number(this._z+1);

};

J.camera.prototype.slice_down = function() {

  if (this._z == 0) return;

  this._viewer.loading(true);
  this._loader.load_tiles(this._x, this._y, --this._z, this._w, this._w);

  DOJO.update_slice_number(this._z+1);

};