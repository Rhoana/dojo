var J = J || {};

J.loader = function(viewer) {
  
  this._viewer = viewer;

  this._image_cache = [];
  this._segmentation_cache = [];

  this._z_cache_size = 0;

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
          // console.log('cache hit', z, w, x, y);
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

J.loader.prototype.clear_cache_segmentation = function(x,y,z,w) {

  this._segmentation_cache[z] = [];
  console.log('cache cleared.');

};

J.loader.prototype.load_tiles = function(x, y, z, w, w_new, no_draw) {

  var mojo_w_new = w_new;

  if (mojo_w_new < 0) {
    this._viewer.loading(false);
    return;
  }

  // console.log(w, w_new, this._viewer._camera._w)


  // // TILESCOUNT FOR CURRENT ZOOMLEVEL IN X AND Y
  var tilescount_x = this._viewer._image.zoom_levels[mojo_w_new][0];
  var tilescount_y = this._viewer._image.zoom_levels[mojo_w_new][1];



  
  // I,J for the MOUSE (image space)
  var i_j = this._viewer._camera._i_j;
  if (i_j[0] == -1 || i_j[1] == -1) {
    i_j = [0,0];
  }
  
  // // the current image width based on the current zoomlevel and linear zoom
  // var current_image_width = 512*this._viewer._image.zoom_levels[w_new][2]*this._viewer._camera._view[0];
  // var current_image_height = 512*this._viewer._image.zoom_levels[w_new][3]*this._viewer._camera._view[4];

  // // var image_width_no_zoom = 512*this._viewer._image.zoom_levels[this._viewer._camera._w][2];
  // // var image_height_no_zoom = 512*this._viewer._image.zoom_levels[this._viewer._camera._w][3];


  // var image_width = (this._viewer._image.width/this._viewer._image.zoom_levels[mojo_w_new][2]);
  // var image_height = (this._viewer._image.height/this._viewer._image.zoom_levels[mojo_w_new][3]);

  
  // console.log('IJ', i_j[0], i_j[1])
  // console.log('wh', image_width, image_height)

  // X, Y as tile indices for the MOUSE on highest resolution
  x = Math.floor(i_j[0] / 512);
  y = Math.floor(i_j[1] / 512);

  // now for the new zoomlevel
  x = Math.floor(x / Math.pow(2, w_new));
  y = Math.floor(y / Math.pow(2, w_new));

  // console.log('XY',x,y)

  





  // offset of the top left of the whole image including linear zoom
  var offset_x = this._viewer._camera._view[6];
  var offset_y = this._viewer._camera._view[7];

  // console.log('OFFSET',offset_x, offset_y)

  // now we need the global offset of our tile
  var local_offset_x = (offset_x + x*(512 * this._viewer._camera._view[0]));
  var local_offset_y = (offset_y + y*(512 * this._viewer._camera._view[4]));
  // console.log('LOCAL OFFSET', local_offset_x)



  // console.log('OFFSET',offset_x_no_linear_zoom)
  
  // console.log('OFFSET', offset_x_no_linear_zoom, offset_y_no_linear_zoom)


  // var image_left = Math.max(0,-offset_x);
  // var image_top = Math.max(0,-offset_y);
    
  // var overflow_x = Math.min(0,this._viewer._width - (offset_x + current_image_width));
  // var overflow_y = Math.min(0,this._viewer._height - (offset_y + current_image_height));

  // var image_right = Math.min(current_image_width, current_image_width+overflow_x);
  // var image_bottom = Math.min(current_image_height, current_image_height+overflow_y);

  // var pixel_width = Math.min((image_right-image_left)/this._viewer._camera._view[0], current_image_width);
  // var pixel_height = Math.min((image_bottom-image_top)/this._viewer._camera._view[4], current_image_height);
  // console.log('IMAGESIZE', (image_right-image_left)/this._viewer._camera._view[0], )


  // console.log('IMAGESIZE', pixel_width, pixel_height)

  // console.log(image_left, image_top)

  // var x_tiles = [Math.floor(image_left/512), Math.floor(((image_left + pixel_width)/512))];
  // var y_tiles = [Math.floor(image_top/512), Math.floor(((image_top + pixel_height)/512))];

  // console.log(x_tiles, y_tiles)

  // return;

  

  // the offset of the current tile under the MOUSE in viewport coords
  // var current_tile_x = (this._viewer._camera._view[6]-x*512*this._viewer._camera._view[0]);
  // var current_tile_y = (this._viewer._camera._view[7]-y*512*this._viewer._camera._view[4]);

  // console.log('CURRENT',current_tile_x, current_tile_y)



  var tiles_to_load = [];
  tiles_to_load.push([x,y]);

  // console.log(tiles_to_load)



  // console.log('CURRENT TILE', current_tile_x, current_tile_y)

  // calculate the viewport in image space






  // check how many surrounding tiles we should load
  var space_left = Math.max(0,local_offset_x);
  var space_top = Math.max(0,local_offset_y);
  var space_right = Math.max(0, this._viewer._width - (local_offset_x+512*this._viewer._camera._view[0]));
  var space_bottom = Math.max(0, this._viewer._height - (local_offset_y+512*this._viewer._camera._view[4]));
  
  // console.log('VIEWPORT L', space_left, 'R', space_right, 'T', space_top, 'B', space_bottom)


  // console.log(space_right, current_tile_x)
  var no_left = Math.ceil(space_left/(512*this._viewer._camera._view[0]));
  var no_top = Math.ceil(space_top/(512*this._viewer._camera._view[4]));
  var no_right = Math.ceil(space_right/(512*this._viewer._camera._view[0]));
  var no_bottom = Math.ceil(space_bottom/(512*this._viewer._camera._view[4]));




  // console.log('LOADING L',no_left, 'R',no_right, 'T',no_top, 'B',no_bottom)
  

  // no_left = 0
  // no_top = 0
  // no_right = 0
  // no_bottom = 0


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


  for (var t=1; t<=no_top; t++) {
    var new_y = y-t;
    if (new_y < 0) break;    
    for (var r=1; r<=no_right; r++) {
      var new_x = x+r;
      if (new_x >= tilescount_x) break;
      tiles_to_load.push([new_x, new_y]);
    }
  }

  for (var b=1; b<=no_bottom; b++) {
    var new_y = y+b;
    if (new_y >= tilescount_y) break;
    for (var r=1; r<=no_right; r++) {
      var new_x = x+r;
      if (new_x >= tilescount_x) break;
      tiles_to_load.push([new_x, new_y]);
    }
  }

  for (var t=1; t<=no_top; t++) {
    var new_y = y-t;
    if (new_y < 0) break;    
    for (var l=1; l<=no_left; l++) {
      var new_x = x-l;
      
      if (new_x < 0) break;
      tiles_to_load.push([new_x,new_y]);
    }
  }

  for (var b=1; b<=no_bottom; b++) {
    var new_y = y+b;
    if (new_y >= tilescount_y) break;
    for (var l=1; l<=no_left; l++) {
      var new_x = x-l;
      
      if (new_x < 0) break;
      tiles_to_load.push([new_x,new_y]);
    }
  }


  // console.log(tiles_to_load.length)

  // clear old tiles
  if (!no_draw) {
    // console.log('clearing',this._viewer._image.zoom_levels[w][0]*512)
    // this._viewer.clear_buffer(this._viewer._image.zoom_levels[w][0]*512, this._viewer._image.zoom_levels[w][1]*512);
    this._viewer.clear_buffer(this._viewer._image.width, this._viewer._image.height);
  }

  var to_draw = tiles_to_load.length;
  var max_to_draw = tiles_to_load.length;
  for (var k=0; k<max_to_draw; k++) {

    var x_y = tiles_to_load[k];
    x = tiles_to_load[k][0];
    y = tiles_to_load[k][1];

    this.get_image(x, y, z, mojo_w_new, function(x, y, z, mojo_w_new, i) {

      this.get_segmentation(x, y, z, mojo_w_new, function(x, y, z, mojo_w_new, s) {

        if (!no_draw) this._viewer.draw_image(x, y, z, mojo_w_new, i, s);
        
        to_draw--;



        if (to_draw == 0) {

          this._viewer.loading(false);
        }

      }.bind(this, x, y, z, mojo_w_new));

    }.bind(this, x, y, z, mojo_w_new));

  }

};