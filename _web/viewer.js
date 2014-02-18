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
  this._image_buffer_ready = false;

  this._segmentation_buffer = document.createElement('canvas');
  this._segmentation_buffer.width = 512;
  this._segmentation_buffer.height = 512;
  this._segmentation_buffer_context = this._segmentation_buffer.getContext('2d');
  this._pixel_data_buffer = this._segmentation_buffer_context.createImageData(512, 512);

  this._offscreen_buffer = document.createElement('canvas');
  // _container.appendChild(this._offscreen_buffer);
  this._offscreen_buffer.width = 512;
  this._offscreen_buffer.height = 512;

  this._image = null;
  this._segmentation = null;

  this._colormap = null;
  this._gl_colormap = null;
  this._max_colors = 0;

  this._overlay_opacity = 100;  

  this._loader = new J.loader(this);
  this._camera = new J.camera(this);
  this._controller = new J.controller(this);
  this._offscreen_renderer = new J.offscreen_renderer(this);
  if (!this._offscreen_renderer.init('vs1', 'fs1')) {
    console.log('WebGL not supported.');
  }

};

J.viewer.prototype.init = function(callback) {

  // get contents
  this._loader.load_json('/image/contents', function(res) {

    this._image = JSON.parse(res.response);

    // type cast some stuff
    this._image.width = parseInt(this._image.width, 10);
    this._image.height = parseInt(this._image.height, 10);
    this._image.zoomlevel_count = parseInt(this._image.zoomlevel_count, 10);
    this._image.max_z_tiles = parseInt(this._image.max_z_tiles, 10);

    this._image.zoom_levels = this.calc_zoomlevels();

    // set to default zoom level (smallest in MOJO notation)
    this._camera._w = this._image.zoomlevel_count - 1;

    this._interactor = new J.interactor(this);

    this._image_buffer.width = this._image.width;
    this._image_buffer.height = this._image.height;

    this._loader.load_json('/segmentation/contents', function(res) {

      this._segmentation = JSON.parse(res.response);

      // TODO support if we don't have a segmentation
      this._loader.load_json('/segmentation/colormap', function(res) {

        this._colormap = JSON.parse(res.response);
        this._max_colors = this._colormap.length;
        this._gl_colormap = new Uint8Array(3*this._max_colors);

        var pos = 0;
        for (var i=0; i<this._max_colors; i++) {
          
          var c = this._colormap[i];

          this._gl_colormap[pos++] = c[0];
          this._gl_colormap[pos++] = c[1];
          this._gl_colormap[pos++] = c[2];

        }

        this._camera.reset();

        // start rendering loop
        this.render();

        // now create websocket connection
        this._websocket = new J.websocket(this);

      }.bind(this)); // /segmentation/colormap

    }.bind(this)); // load /segmentation/contents

  }.bind(this)); // load /image/contents

};

J.viewer.prototype.calc_zoomlevels = function() {

  var zoom_levels = [];

  // largest zoom level
  zoom_levels[0] = [Math.ceil(this._image.width/512), Math.ceil(this._image.height/512), this._image.width/512, this._image.height/512];

  var _width = this._image.width/2;
  var _height = this._image.height/2;

  for (var w=1; w<this._image.zoomlevel_count; w++) {
    
    var level_x_count = Math.ceil(_width / 512);
    var level_y_count = Math.ceil(_height / 512);

    zoom_levels[w] = [level_x_count, level_y_count, _width / 512, _height / 512];

    _width /= 2;
    _height /= 2;

  }

  return zoom_levels;

};

J.viewer.prototype.redraw = function() {

  // trigger re-draw
  this.loading(true);

  this._loader.load_tiles(this._camera._x, this._camera._y, this._camera._z, this._camera._w, this._camera._w, false);

};

J.viewer.prototype.draw_image = function(x,y,z,w,i,s) {
  
  this._image_buffer_context.drawImage(i,0,0,512,512,x*512,y*512,512,512);

  // draw segmentation
  var pixel_data = this._pixel_data_buffer;
  var pixel_data_data = pixel_data.data;
  var segmentation_data = s;//;new Uint32Array(s.buffer);

  var opacity = this._overlay_opacity;
  var highlighted_id = this._controller._highlighted_id;
  var activated_id = this._controller._activated_id;

  var pos = 0; // running pixel (rgba) index, increases by 4
  var max_colors = this._max_colors;
  var colormap = this._colormap;

  var right_border = 1;
  var left_border = 0;

  // // run through all 512*512 bytes
  // for (var p=0; p<262144; p++) {

  //   var id = this.lookup_id(segmentation_data[p]);

  //   var color = this.get_color(id);

  //   // if (++right_border == 511) {
  //   //   right_border = 1;
  //   // }

  //   // if (++left_border == 512) {
  //   //   left_border = 0;
  //   // }

  //   // var border = false;
  //   // border = (p>0 && left_border > 0 && id != this.lookup_id(segmentation_data[p-1])) || // left
  //   //          (p<262143 && right_border > 1 && id != this.lookup_id(segmentation_data[p+1])) //|| // right
  //   //          // (p>511 && id != segmentation_data[p-512]) || // top
  //   //          // (p<261631 && id != segmentation_data[p+512]); // bottom
    
  //   // if (border) {
  //   //   // console.log('border')
  //   //   pixel_data_data[pos++] = 0;
  //   //   pixel_data_data[pos++] = 0;
  //   //   pixel_data_data[pos++] = 0;
  //   //   pixel_data_data[pos++] = 255;
  //   //   continue;
  //   // }

  //   pixel_data_data[pos++] = color[0];
  //   pixel_data_data[pos++] = color[1];
  //   pixel_data_data[pos++] = color[2];
  //   pixel_data_data[pos++] = 255;

  //   // if (id == highlighted_id || id == activated_id) {
  //   //   pixel_data_data[pos++] = 200;
  //   // } else {    
  //   //   pixel_data_data[pos++] = opacity;
  //   // }

  // }
  
  // send pixel data to WebGL and get the processed return
  var s_new = this._offscreen_renderer.draw(s);
  //console.log(s_new)

  //pixel_data.data = s_new.buffer);

  for (var p=0; p<262144; p++) {

    pixel_data_data[pos] = s_new[pos++];
    pixel_data_data[pos] = s_new[pos++];
    pixel_data_data[pos] = s_new[pos++];
    pixel_data_data[pos] = s_new[pos++];

  }

  //console.log(pixel_data.data)

  this._segmentation_buffer_context.putImageData(pixel_data, 0, 0);
  this._image_buffer_context.drawImage(this._segmentation_buffer,0,0,512,512,x*512,y*512,512,512);

};

J.viewer.prototype.lookup_id = function(id) {

  // check if this has an entry in the merge table
  while(typeof this._controller._merge_table[id] !== 'undefined') {
    id = this._controller._merge_table[id];
  }

  return id;

};

J.viewer.prototype.get_color = function(id) {
  console.log(id, id % this._max_colors, this._colormap[id % this._max_colors]);
  return this._colormap[id % this._max_colors];

};

J.viewer.prototype.clear_buffer = function(width, height) {

  this._image_buffer_context.clearRect(0, 0, width, height);

};

J.viewer.prototype.clear = function() {

  var _width = this._width;
  var _height = this._height;

  this._context.save();
  this._context.setTransform(1, 0, 0, 1, 0, 0);
  this._context.clearRect(0, 0, _width, _height);
  this._context.restore();

};

J.viewer.prototype.loading = function(value) {
  // console.log('loading', value)
  this._image_buffer_ready = !value;
};

J.viewer.prototype.render = function() {

  this._context.setTransform(this._camera._view[0], this._camera._view[1], this._camera._view[3], this._camera._view[4], this._camera._view[6], this._camera._view[7]);

  if (this._image_buffer_ready) {
    this.clear();
    // put image buffer
    this._context.drawImage(this._image_buffer, 0, 0);
  }

  this._AnimationFrameID = window.requestAnimationFrame(this.render.bind(this));

};

J.viewer.prototype.xy2uv = function(x, y) {

  var u = x - this._camera._view[6];
  var v = y - this._camera._view[7];
  // console.log(u, this._camera._view[6], x, this._image.zoom_levels[this._camera._zoom_level][0])
  //if (u < 0 || u >= this._camera._view[0] * this._zoom_level*512) {
  if (u < 0 || u >= this._camera._view[0] * this._image.zoom_levels[this._camera._w][2] *512) {
    u = -1;
  }

  //if (v < 0 || v >= this._camera._view[4] * this._zoom_level*512) {
  if (v < 0 || v >= this._camera._view[4] * this._image.zoom_levels[this._camera._w][3] *512) {
    v = -1;
  }

  return [u, v];

};

// returns the pixel coordinates looking at the largest image
J.viewer.prototype.xy2ij = function(x, y) {

  var u_v = this.xy2uv(x, y);

  if (u_v[0] == -1 || u_v[1] == -1) {
    return [-1, -1];
  }

  var i_j = [Math.floor(((u_v[0]/this._image.zoom_levels[this._camera._w][2])*this._image.zoom_levels[0][2])/this._camera._view[0]), 
             Math.floor(((u_v[1]/this._image.zoom_levels[this._camera._w][3])*this._image.zoom_levels[0][3])/this._camera._view[4])];

  return i_j;

};

J.viewer.prototype.ij2xy = function(i, j) {

  var x = this._camera._view[6] + (i * this._image.zoom_levels[this._camera._w][2]);
  var y = this._camera._view[7] + (j * this._image.zoom_levels[this._camera._w][3]);

  return [x, y];

};

J.viewer.prototype.get_segmentation_id = function(i, j, callback) {

  var x = Math.floor(i / 512);
  var y = Math.floor(j / 512);
  var z = this._camera._z;
  var w = 0;
  
  this._loader.get_segmentation(x, y, z, w, function(s) {

    var pixel_data = new Uint32Array(s.buffer);

    var id = this.lookup_id(pixel_data[(j % 512) * 512 + (i % 512)]);

    callback(id);

  }.bind(this));

};