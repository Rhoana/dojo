var J = J || {};

J.loader = function(viewer) {
  
  this._viewer = viewer;

  this._image_cache = [];
  this._segmentation_cache = [];

  this._z_cache_size = 3;

  this._image_loading = [];

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

J.loader.prototype.get_image = function(x, y, z, w, callback, no_cache) {

  // check if we have a cached version
  if (this._image_cache[z]) {

    if (this._image_cache[z][w]) {
      if (this._image_cache[z][w][x]) {
        if (this._image_cache[z][w][x][y]) {
          // we have it cached
          //console.log('cache hit', z, w, x, y);
          var i = this._image_cache[z][w][x][y];

          if (!no_cache) {
            this.cache_image(x, y, z, w);
          }

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

  if (!no_cache) {
    this.cache_image(x, y, z, w);
  }

};

J.loader.prototype.cache_image = function(x, y, z, w) {
  return;
  // now get some more images  
  for (var j=1;j<=this._z_cache_size;j++) {
    if (z+j < this._viewer._image.max_z_tiles) {
      this.get_image(x, y, z+j, w, function(i) {
        //console.log('cached', i);
      }, true);
    }
  }

};

J.loader.prototype.get_segmentation = function(x, y, z, w, callback, no_cache) {

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

  // if (!no_cache) {
  //   this.cache_segmentation(x, y, z, w);
  // }  

};

J.loader.prototype.cache_segmentation = function(x, y, z, w) {

  // now get some more images  
  for (var j=1;j<=this._z_cache_size;j++) {
    if (z+j < this._viewer._image.max_z_tiles) {      
      console.log('getting', z+j);
      this.get_segmentation(x, y, z+j, w, function(s) {
        console.log('cached', s);
      }, true);
    }
  }

};

J.loader.prototype.load_tiles = function(x, y, z, w, w_new, no_draw) {


  
  var mojo_w_new = w_new;//this._viewer._image.zoomlevel_count - 1 - w_new;

  if (mojo_w_new < 0) {
    this._viewer.loading(false);
    return;
  }

  // clear old tiles
  if (!no_draw) {
    this._viewer.clear_buffer(this._viewer._image.zoom_levels[w][0]*512, this._viewer._image.zoom_levels[w][1]*512);
  }

  //console.log('loading', x, y, z, w, w_new);

  // todo check which sub-tiles to load
  var tilescount_x = this._viewer._image.zoom_levels[mojo_w_new][0];
  var tilescount_y = this._viewer._image.zoom_levels[mojo_w_new][1];
  
  // var to_draw = tilescount_x*tilescount_y;

  // don't recalculate I,J here
  var i_j = this._viewer._camera._i_j;

  // console.log(x,y,i_j);
  x = Math.floor(i_j[0] / (this._viewer._image.width/this._viewer._image.zoom_levels[mojo_w_new][2]));
  y = Math.floor(i_j[1] / (this._viewer._image.height/this._viewer._image.zoom_levels[mojo_w_new][3]));

  var tiles_to_load = [];
  tiles_to_load.push([x,y]);

  // grab the surrounding tiles as well
  // var no_left = Math.floor((this._viewer._width - (x * 512 + this._viewer._camera._view[6]))/512);
  // var no_top = Math.floor((this._viewer._height - (y * 512 + this._viewer._camera._view[7]))/512);
  // console.log('load left', no_left);
  // // console.log('load top', no_top);

  var current_tile_x = (this._viewer._camera._view[6]+x*512);
  var current_tile_y = (this._viewer._camera._view[7]+y*512);

  var space_left = Math.max(0,current_tile_x);
  var space_top = Math.max(0,current_tile_y);
  var space_right = Math.max(0, this._viewer._width - (current_tile_x+512));
  var space_bottom = Math.max(0, this._viewer._height - (current_tile_y+512));

  var no_left = Math.ceil(space_left/512);
  var no_top = Math.ceil(space_top/512);
  var no_right = Math.ceil(space_right/512);
  var no_bottom = Math.ceil(space_bottom/512);


  // var no_left = Math.ceil((this._viewer._camera._view[6]+x*512)/512);
  // var no_top = Math.ceil((this._viewer._camera._view[7]+y*512)/512);
  // console.log('----------------')
  // console.log('load left', no_left);

  // for (var l=x;l>=0 && l<=no_left;l--) {
  //   for (var t=y;t>=0 && t<=no_top;t--) {
  //     tiles_to_load.push([l,t]);
  //   }
  // }
  // var no_right = Math.ceil((this._viewer._width - (this._viewer._camera._view[6]+x*512)+512)/512);
  // var no_bottom = Math.ceil((this._viewer._height - (this._viewer._camera._view[7]+y*512)+512)/512);

  for (var l=1; l<=no_left; l++) {
    var new_x = x-l;
    
    if (new_x < 0) break;
    tiles_to_load.push([new_x,y]);
  }

  for (var t=1; t<=no_top; t++) {
    var new_y = y-t;
    if (new_y < 0) break;
    tiles_to_load.push([x, new_y]);
  }  

  for (var r=1; r<=no_right; r++) {
    var new_x = x+r;
    
    if (new_x >= tilescount_x) break;
    
    tiles_to_load.push([new_x, y]);
  }

  for (var b=1; b<=no_bottom; b++) {
    var new_y = y+b;
    if (new_y >= tilescount_y) break;
    tiles_to_load.push([x, new_y]);
  }

  // for(var l=1;x-l>=0 && l<=no_left;l++) {
  //   tiles_to_load.push([x-l,y]);
  // }

  // for (var l=1;l<=no_left;l++) {
  //   // if ([x-l,y])
  //   tiles_to_load.push([x-l,y]);
  // }
  // for (var t=1;y-t>=0 && t<=no_top;t++) {
  //   tiles_to_load.push([x,y-t]);
  // }  
  // for (var r=1;r<=no_right;r++) {
  //   tiles_to_load.push([x+r,y]);
  // }    
  // for (var b=1;b<=no_bottom;b++) {
  //   tiles_to_load.push([x,y+b]);
  // }
  // console.log('load right', no_right);
  // console.log('load bottom', no_bottom);
  // for (var r=x;r>=0 && r<=no_right;r--) {
  //   for (var b=y;b>=0 && t<=no_bottom;b--) {
  //     tiles_to_load.push([r,b]);
  //   }
  // }
  // var tiles_to_load = [];
  // tiles_to_load.push([x,y]);
  // tiles_to_load = remove_duplicates(tiles_to_load);

  // console.log(tiles_to_load);

  // console.log(i_j,x,y,this._viewer._image.zoom_levels[mojo_w_new][1]*512);
  // for (var y=0; y<tilescount_y; y++) {
  //   for (var x=0; x<tilescount_x; x++) {
  var to_draw = tiles_to_load.length;
  console.log(to_draw);
  console.log(tiles_to_load)
  var max_to_draw = tiles_to_load.length;
  for (var k=0; k<max_to_draw; k++) {

    var x_y = tiles_to_load[k];
    x = tiles_to_load[k][0];
    y = tiles_to_load[k][1];
    console.log('loading',x,y)

    this.get_image(x, y, z, mojo_w_new, function(x, y, z, mojo_w_new, i) {

      this.get_segmentation(x, y, z, mojo_w_new, function(x, y, z, mojo_w_new, s) {
        // console.log('drawing', x, y);
        if (!no_draw) this._viewer.draw_image(x, y, z, mojo_w_new, i, s);

        to_draw--;

        if (to_draw == 0) {
          this._viewer.loading(false);
        }

      }.bind(this, x, y, z, mojo_w_new));

    }.bind(this, x, y, z, mojo_w_new));

  }
  //   }
  // }

};