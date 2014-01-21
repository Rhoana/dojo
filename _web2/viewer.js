var J = J || {};

J.viewer = function(container) {

  var _container = document.getElementById(container);

  var _canvas = document.createElement('canvas');
  _canvas.width = _container.clientWidth;
  _canvas.height = _container.clientHeight;
  _container.appendChild(_canvas);

  this._width = _canvas.width;
  this._height = _canvas.height;

  this._canvas = _canvas;
  this._context = this._canvas.getContext('2d');

  this._image_buffer = document.createElement('canvas');
  //_container.appendChild(this._image_buffer);
  this._image_buffer_context = this._image_buffer.getContext('2d');

  this._zoom_level = 1;
  this._zoom_level_count = 1;

  this._loader = new J.loader(this);
  this._camera = new J.camera(this);
  this._interactor = new J.interactor(this);

  this.init();

};

J.viewer.prototype.init = function() {

  // get contents
  this._loader.load_json('/image/contents', function(res) {

    this._image = JSON.parse(res.response);

    // type cast some stuff
    this._image.width = parseInt(this._image.width, 10);
    this._image.height = parseInt(this._image.height, 10);

    this._image.zoomlevel_count = parseInt(this._image.zoomlevel_count, 10);
    this._zoom_level_count = this._image.zoomlevel_count;

    this._image.max_z_tiles = parseInt(this._image.max_z_tiles, 10);

    this._image_buffer.width = this._image.width;
    this._image_buffer.height = this._image.height;

    this._loader.load_json('/segmentation/contents', function(res) {    

      this._segmentation = JSON.parse(res.response);

      var x = 0;
      var y = 0;
      var z = 0;
      var w = parseInt(this._image.zoomlevel_count,10)-1;
      this._loader.get_image(x, y, z, w, function(i) {

        this.draw_image(x, y, z, w, i);

        this._camera.reset();

        this.render();

      }.bind(this));

    }.bind(this));

  }.bind(this));

};

J.viewer.prototype.draw_image = function(x,y,z,w,i) {

  console.log('Drawing',x,y,z,w, i);

  this._image_buffer_context.drawImage(i,0,0,512,512,x*512,y*512,512,512);

};


J.viewer.prototype.render = function() {

  var _width = this._width;
  var _height = this._height;

  this._context.save();
  this._context.clearRect(-_width, -_height, 2 * _width, 2 * _height);
  this._context.restore();

  this._context.setTransform(this._camera._view[0], this._camera._view[1], this._camera._view[3], this._camera._view[4], this._camera._view[6], this._camera._view[7]);

  // put image buffer
  this._context.drawImage(this._image_buffer, 0, 0);

  this._AnimationFrameID = window.requestAnimationFrame(this.render.bind(this));

};

J.viewer.prototype.xy2uv = function(x, y) {

  var u = x - this._camera._view[6];
  var v = y - this._camera._view[7];

  if (u < 0 || u >= this._camera._view[0] * this._zoom_level*512) {
    u = -1;
  }

  if (v < 0 || v >= this._camera._view[4] * this._zoom_level*512) {
    v = -1;
  }

  return [u, v];

};

J.viewer.prototype.xy2ij = function(x, y) {

  var u_v = this.xy2uv(x, y);

  if (u_v[0] == -1 || u_v[1] == -1) {
    return [-1, -1];
  }

  return [(u_v[0]/(this._camera._view[0])), (u_v[1]/(this._camera._view[4]))];

};

J.viewer.prototype.ij2xy = function(i, j) {

  var x = this._camera._view[6] + (i * this._camera._view[0]);
  var y = this._camera._view[7] + (j * this._camera._view[4]);

  return [x, y];

};