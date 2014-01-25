var J = J || {};

J.loader = function(viewer) {
  
  this._viewer = viewer;

  this._image_cache = [];
  this._segmentation_cache = [];

};

J.loader.prototype.load_json = function(url, callback) {

  var xhr = new XMLHttpRequest();
  xhr.open('GET', url, true);

  xhr.onload = callback.bind(this, xhr);

  xhr.send(null);

};

J.loader.prototype.load_image = function(x, y, z, w, callback) {

  var i = new Image();
  i.src = '/image/'+pad(z,8)+'/'+w+'/'+x+'_'+y+'.jpg';
  i.onload = callback.bind(this, i);

};

J.loader.prototype.load_segmentation = function(x, y, z, w, callback) {

  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/segmentation/'+pad(z,8)+'/'+w+'/'+x+'_'+y+'.raw', true);
  xhr.responseType = 'arraybuffer';

  xhr.onload = callback.bind(this, xhr);

  xhr.send(null);

};

J.loader.prototype.get_image = function(x, y, z, w, callback) {

  // check if we have a cached version
  if (this._image_cache[z]) {

    if (this._image_cache[z][w]) {
      if (this._image_cache[z][w][x]) {
        if (this._image_cache[z][w][x][y]) {
          // we have it cached
          // console.log('cache hit', z, w, x, y);
          var i = this._image_cache[z][w][x][y];

          callback(i);

          return;
        }
      }
    }

  }

  this.load_image(x, y, z, w, function(i) {

    // cache this image
    this._image_cache[z] = this._image_cache[z] ? this._image_cache[z] : [];
    this._image_cache[z][w] = this._image_cache[z][w] ? this._image_cache[z][w] : [];
    this._image_cache[z][w][x] = this._image_cache[z][w][x] ? this._image_cache[z][w][x] : [];
    this._image_cache[z][w][x][y] = i;

    // call real callback
    callback(i);

  });

};

J.loader.prototype.get_segmentation = function(x, y, z, w, callback) {

  // check if we have a cached version
  if (this._segmentation_cache[z]) {

    if (this._segmentation_cache[z][w]) {
      if (this._segmentation_cache[z][w][x]) {
        if (this._segmentation_cache[z][w][x][y]) {
          // we have it cached
          // console.log('cache hit', z, w, x, y);
          var i = this._segmentation_cache[z][w][x][y];

          callback(i);

          return;
        }
      }
    }

  }

  this.load_segmentation(x, y, z, w, function(s) {

    // uncompress
    var compressed = new Zlib.Inflate(new Uint8Array(s.response));
    var raw_s = compressed.decompress();

    // cache this image
    this._segmentation_cache[z] = this._segmentation_cache[z] ? this._segmentation_cache[z] : [];
    this._segmentation_cache[z][w] = this._segmentation_cache[z][w] ? this._segmentation_cache[z][w] : [];
    this._segmentation_cache[z][w][x] = this._segmentation_cache[z][w][x] ? this._segmentation_cache[z][w][x] : [];
    this._segmentation_cache[z][w][x][y] = raw_s;

    // call real callback
    callback(raw_s);

  });

};

J.loader.prototype.load_tiles = function(x, y, z, w, w_new) {



  var mojo_w_new = w_new;//this._viewer._image.zoomlevel_count - 1 - w_new;

  if (mojo_w_new < 0) {
    return;
  }

  // clear old tiles
  this._viewer.clear_buffer(this._viewer._image.zoom_levels[w][0]*512, this._viewer._image.zoom_levels[w][1]*512);

  //console.log('loading', x, y, z, w, w_new);

  // todo check which sub-tiles to load

  var tilescount_x = this._viewer._image.zoom_levels[mojo_w_new][0];
  var tilescount_y = this._viewer._image.zoom_levels[mojo_w_new][1];

  for (var y=0; y<tilescount_y; y++) {
    for (var x=0; x<tilescount_x; x++) {

      this.get_image(x, y, z, mojo_w_new, function(x, y, z, mojo_w_new, i) {

        this.get_segmentation(x, y, z, mojo_w_new, function(x, y, z, mojo_w_new, s) {

          this._viewer.draw_image(x, y, z, mojo_w_new, i, s);

        }.bind(this, x, y, z, mojo_w_new));

      }.bind(this, x, y, z, mojo_w_new));

    }
  }

};