var J = J || {};

J.camera = function(viewer) {

  this._viewer = viewer;

  // a c e
  // b d f
  // 0 0 1
  this._view = [1, 0, 0, 0, 1, 0, 0, 0, 1];

};


J.camera.prototype.center = function() {

  this._view[6] = this._viewer._width/2 - this._view[0]*512/2;
  this._view[7] = this._viewer._height/2 - this._view[4]*512/2;

};

J.camera.prototype.auto_scale = function() {

  var _w_scale = this._viewer._width / 512*this._viewer._zoom_level;
  var _h_scale = this._viewer._height / 512*this._viewer._zoom_level;

  var _auto_scale = Math.min(_w_scale, _h_scale);

  this._view[0] = _auto_scale;
  this._view[4] = _auto_scale;

};

J.camera.prototype.reset = function() {

  this.auto_scale();
  this.center();

};


///

J.camera.prototype.zoom = function(level) {
  this._view[0] = level;
  this._view[4] = level;
};
