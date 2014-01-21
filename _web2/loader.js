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


};

J.loader.prototype.get_image = function(x, y, z, w, callback) {

  // check if we have a cached version
  if (this._image_cache[z]) {

    if (this._image_cache[z][w]) {
      if (this._image_cache[z][w][x]) {
        if (this._image_cache[z][w][x][y]) {
          // we have it cached
          console.log('cache hit', z, w, x, y);
          return this._image_cache[z][w][x][y];
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

J.loader.prototype.load_tile = function(x, y, z, w, w_new) {

  var mojo_w_new = this._viewer._zoom_level_count - w_new;

  if (mojo_w_new < 0) {
    return;
  }

  console.log('loading', x, y, z, w, w_new);

  // todo check which sub-tiles to load

  this.get_image(0, 0, z, mojo_w_new, function(i) {

    console.log(i);

  });

  this.get_image(0, 1, z, mojo_w_new, function(i) {

    console.log(i);

  });

  this.get_image(1, 0, z, mojo_w_new, function(i) {

    console.log(i);

  });  

  this.get_image(1, 1, z, mojo_w_new, function(i) {

    console.log(i);

  });  

};