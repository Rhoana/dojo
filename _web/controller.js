var J = J || {};

J.controller = function(viewer) {

  this._viewer = viewer;

  this._last_id = null;

  this._merge_table = null;

  this._gl_merge_table_keys = null;
  this._gl_merge_table_values = null;
  this._merge_table_length = -1;

  this._lock_table = null;

  this._gl_lock_table = null;
  this._lock_table_length = -1;

  this._highlighted_id = null;

  this._activated_id = null;

  this._use_3d_labels = false;
  this._3d_labels = {};
  this._fixed_3d_labels = {};
  this._gl_3d_labels = null;
  this._gl_3d_labels_length = -1;

  this._origin = makeid() // TODO

  this._cursors = {};
  this._cursors_3d = {};

  this._problem_table = null;
  this._exclamationmarks_2d = {};
  this._exclamationmarks_3d = {};

  this._split_id = -1;
  this._split_mode = -1;
  this._split_line = [];
  this._adjust_mode = -1;
  this._adjust_id = -1;
  this._brush_bbox = [];
  this._brush_size = 3;
  this._brush_ijs = [];

  this.create_gl_3d_labels();

};

J.controller.prototype.activate = function(id) {
  if (this._activated_id == id) return;

  this._activated_id = id;

  this._viewer.redraw();

  if (DOJO.threeD)
    this.add_3d_label(id);

}

J.controller.prototype.highlight = function(id) {
  if (this._highlighted_id == id) return;

  if (DOJO.threeD)
    this.highlight_in_3d(id);

  this._highlighted_id = id;

  this._viewer.redraw();   

}

J.controller.prototype.receive = function(data) {

  var input = JSON.parse(data.data);

  if (input.name == 'LOG') {
    DOJO.update_log(input);
    return;
  } 

  if (input.origin == this._origin) {
    // we are the sender or the requester

    if (input.name == 'SPLITRESULT') {
      console.log(input)
      this.show_split_line(input.value);
      return;
    } else if (input.name == 'SPLITDONE') {
      this.finish_split(input.value);
    } else if (input.name == 'ADJUSTDONE') {
      this.finish_adjust(input.value);
    } else if (input.name == 'SAVED') {
      console.log('All saved. Yahoo!');
    }

    return;
  }

  if (input.name == 'WELCOME') {

    this.send('WELCOME', {});

  } else if (input.name == 'MERGETABLE') {

    // received new merge table
    this._viewer._controller.update_merge_table(input.value);

  } else if (input.name == 'LOCKTABLE') {

    // received new lock table
    this._viewer._controller.update_lock_table(input.value);

  } else if (input.name == 'REDRAW') {

    this._viewer.redraw();
    this.update_threeD();

  } else if (input.name == 'MOUSEMOVE') {

    if (DOJO.link_active)
      this.on_mouse_move(input.origin, input.id, input.value);

  } else if (input.name == 'PROBLEMTABLE') {

    this.update_problem_table(input.value);

  } else if (input.name == 'RELOAD') {

    // force reload
    console.log('force reload');
    this.reload_tiles(input.value);


  }

};

J.controller.prototype.save = function() {

  this.send('SAVE', null);

};


J.controller.prototype.on_mouse_move = function(origin, id, value) {

  var i = value[0];
  var j = value[1];
  var k = value[2];

  // special case for 3d (we always show then)
  if (DOJO.threeD)
    this.on_mouse_move_3d(origin, id, i, j, k);

  if (k != this._viewer._camera._z) return;

  var x_y = this._viewer.ij2xy(i, j);

  var cursor = this._cursors[id];

  if (!cursor) {

    // clone the cursor
    cursor = document.getElementById('cursor').cloneNode();

    var color = this._viewer.get_color(id+100);

    cursor.style.backgroundColor = 'rgb('+color[0]+','+color[1]+','+color[2]+')';

    cursor.id = '';

    document.body.appendChild(cursor);

    this._cursors[id] = cursor;

  } 

  cursor.style.left = x_y[0];
  cursor.style.top = x_y[1];

  cursor.style.display = 'block';

};

J.controller.prototype.on_mouse_move_3d = function(origin, id, i, j, k) {

  var cursor = this._cursors_3d[id];

  var height = DOJO.threeD.volume.dimensions[2]*DOJO.threeD.volume.spacing[2] + 50;

  var x_y_z = this._viewer.ijk2xyz(i, j, k);

  if (!cursor) {

    var color = this._viewer.get_color(id+100);    

    cursor = new X.cube();
    cursor.dojo_type = '3dcursor';
    cursor.lengthX = cursor.lengthY = cursor.lengthZ = 10;
    cursor.center = [0,0,-height];
    cursor.color = [color[0]/255, color[1]/255, color[2]/255];
    var line = new X.object();
    line.points = new X.triplets(6);
    line.normals = new X.triplets(6);
    line.type = 'LINES';
    line.points.add(0,0,0);
    line.points.add(0,0,-height);
    line.normals.add(0,0,0);
    line.normals.add(0,0,0);
    line.color = cursor.color;
    cursor.children.push(line);

    DOJO.threeD.renderer.add(cursor);

    this._cursors_3d[id] = cursor;

  }

  cursor.transform.matrix[12] = x_y_z[0];
  cursor.transform.matrix[13] = x_y_z[1];
  cursor.transform.matrix[14] = x_y_z[2];

  cursor.children[0].transform.matrix[12] = x_y_z[0];
  cursor.children[0].transform.matrix[13] = x_y_z[1];
  cursor.children[0].transform.matrix[14] = x_y_z[2];


};

J.controller.prototype.reset_cursors = function() {

  for (c in this._cursors) {
    document.body.removeChild(this._cursors[c]);
  }

  this._cursors = {};

};

J.controller.prototype.pick3d = function(o) {

  var x = o.transform.matrix[12];
  var y = o.transform.matrix[13];
  var z = o.transform.matrix[14];

  var i_j_k = this._viewer.xyz2ijk(x, y, z);


  if (o.dojo_type == '3dcursor') {
    
    this._viewer._camera.jump(i_j_k[0], i_j_k[1], i_j_k[2]);

  } else if (o.dojo_type == '3dproblem') {

    this._viewer._camera.jump(i_j_k[0], i_j_k[1], i_j_k[2]);

    this.redraw_exclamationmarks();

  }

};

J.controller.prototype.send = function(name, data) {

  var output = {};
  output.name = name;
  output.origin = this._origin;
  output.value = data;

  this._viewer._websocket.send(JSON.stringify(output));

};


///
///
///

J.controller.prototype.update_threeD = function() {

  if (DOJO.threeD) {
    DOJO.threeD.renderer.updateFromDojo(this._viewer._gl_colormap, 
                     this._viewer._max_colors,
                     this._gl_merge_table_keys, 
                     this._gl_merge_table_values, 
                     this._merge_table_length,
                     this._gl_3d_labels,
                     this._gl_3d_labels_length,
                     this._use_3d_labels);
  }

};


J.controller.prototype.update_problem_table = function(data) {
  
  this._problem_table = data;

  if (DOJO.link_active)
    this.redraw_exclamationmarks();

};

J.controller.prototype.redraw_exclamationmarks = function() {

  this.clear_exclamationmarks();
  this.clear_exclamationmarks3d();

  for (var e in this._problem_table) {
    var i_j_k = this._problem_table[e];
    var i = i_j_k[0];
    var j = i_j_k[1];
    var k = i_j_k[2];

    // 3d
    if (DOJO.threeD)
      this.create_exclamationmark_3d(i, j, k, e);

    // 2d
    if (k == this._viewer._camera._z)
      this.create_exclamationmark_2d(i, j, e);

  }

};

J.controller.prototype.add_exclamationmark = function(x, y) {

  var i_j = DOJO.viewer.xy2ij(x, y);

  if (i_j[0] == -1) return;

  this._problem_table.push([i_j[0], i_j[1], DOJO.viewer._camera._z]);

  this.redraw_exclamationmarks();

  this.send_problem_table();

  var log = 'User $USER marked a <font color="red">problem</font> in slice <strong>'+(DOJO.viewer._camera._z+1)+'</strong>.';
  this.send_log(log);  

};

J.controller.prototype.clear_exclamationmarks3d = function() {

  for (var e in this._exclamationmarks_3d) {
    DOJO.threeD.renderer.remove(this._exclamationmarks_3d[e]);
  }

  this._exclamationmarks_3d = {};

};

J.controller.prototype.clear_exclamationmarks = function() {

  for (var e in this._exclamationmarks_2d) {
    document.body.removeChild(this._exclamationmarks_2d[e]);
  }

  this._exclamationmarks_2d = {};

};

J.controller.prototype.remove_exclamationmark_2d = function(id) {

    var e = document.getElementById('em'+id);
    document.body.removeChild(e);

    delete this._exclamationmarks_2d[id];
    this._problem_table.splice(id,1);

    this.send_problem_table();

    var log = 'User $USER resolved a <font color="green">problem</font> in slice <strong>'+(DOJO.viewer._camera._z+1)+'</strong>.';
    this.send_log(log);      

};

J.controller.prototype.remove_exclamationmark_3d = function(id) {
  
  if (DOJO.threeD)
    DOJO.threeD.renderer.remove(this._exclamationmarks_3d[id]);

};

J.controller.prototype.create_exclamationmark_2d = function(i, j, id) {

  var x_y = this._viewer.ij2xy(i, j);

  // clone the exclamationmark
  var e = document.getElementById('exclamationmark').cloneNode(true);

  e.id = 'em'+id;

  document.body.appendChild(e);

  e.style.display = 'block';

  e.style.left = x_y[0]-3;
  e.style.top = x_y[1]-15;

  e.onclick = function(id) {
    
    this.remove_exclamationmark_3d(id);    
    this.remove_exclamationmark_2d(id);

  }.bind(this, id);


  this._exclamationmarks_2d[id] = e;

};

J.controller.prototype.create_exclamationmark_3d = function(i, j, k, id) {

  var height = DOJO.threeD.volume.dimensions[2]*DOJO.threeD.volume.spacing[2] + 50;  

  var x_y_z = this._viewer.ijk2xyz(i, j, k);

  var e = new X.cube();
  e.dojo_type = '3dproblem';
  e.center = [0,0,-height];
  e.lengthX = e.lengthY = e.lengthZ = 10;
  var e_top = new X.cube();
  e_top.dojo_type = '3dproblem';
  e_top.center = [0,0,-height - 40];
  e_top.lengthX = e_top.lengthY = 10;
  e_top.lengthZ = 50;
  e_top.modified();
  e.children.push(e_top);

  var line = new X.object();
  line.points = new X.triplets(6);
  line.normals = new X.triplets(6);
  line.type = 'LINES';
  line.points.add(0,0,0);
  line.points.add(0,0,-height);
  line.normals.add(0,0,0);
  line.normals.add(0,0,0);
  e.children.push(line);

  e.transform.matrix[12] = x_y_z[0];
  e.transform.matrix[13] = x_y_z[1];
  e.transform.matrix[14] = x_y_z[2];

  e.children[0].transform.matrix[12] = x_y_z[0];
  e.children[0].transform.matrix[13] = x_y_z[1];
  e.children[0].transform.matrix[14] = x_y_z[2];

  e.children[1].transform.matrix[12] = x_y_z[0];
  e.children[1].transform.matrix[13] = x_y_z[1];
  e.children[1].transform.matrix[14] = x_y_z[2];  

  this._exclamationmarks_3d[id] = e;

  DOJO.threeD.renderer.add(e);

  // DOJO.threeD.renderer.resetBoundingBox();

};

J.controller.prototype.send_problem_table = function() {

  this.send('PROBLEMTABLE', this._problem_table);

};

J.controller.prototype.update_merge_table = function(data) {

  // console.log('Received new merge table', data);

  this._merge_table = data;

  this.create_gl_merge_table();

};

J.controller.prototype.send_merge_table = function() {

  this.send('MERGETABLE', this._merge_table);

};

J.controller.prototype.send_lock_table = function() {

  this.send('LOCKTABLE', this._lock_table);

};

J.controller.prototype.send_mouse_move = function(i_j_k) {

  this.send('MOUSEMOVE', i_j_k);

}

J.controller.prototype.update_lock_table = function(data) {

  // console.log('Received new lock table', data);

  this._lock_table = data;

  this.create_gl_lock_table();

};

J.controller.prototype.send_log = function(message) {

  this.send('LOG', message);

};

J.controller.prototype.is_locked = function(id) {
  return (id in this._lock_table);
};

J.controller.prototype.lock = function(x, y) {

  if (!this._lock_table) {
    throw new Error('Lock table does not exist.');
  }

  var i_j = this._viewer.xy2ij(x, y);

  if (i_j[0] == -1 || i_j[1] == -1) return;

  this._viewer.get_segmentation_id(i_j[0], i_j[1], function(id) {

    var verb = 'locked';

    if (id in this._lock_table) {
      delete this._lock_table[id];

      // console.log('Unlocking', id);
      verb = 'unlocked';
    } else {
      this._lock_table[id] = true;
      // console.log('Locking', id);
    }

    var color1 = DOJO.viewer.get_color(id);
    var color1_hex = rgbToHex(color1[0], color1[1], color1[2]);
    var log = 'User $USER '+verb+' label <font color="'+color1_hex+'">'+id+'</font>.';

    this.send_log(log);

    this.create_gl_lock_table();

    this.send_lock_table();

    this._viewer.redraw();

  }.bind(this));

};

J.controller.prototype.larger_brush = function() {

  this._brush_size = Math.min(10, this._brush_size+=1);

};

J.controller.prototype.smaller_brush = function() {

  this._brush_size = Math.max(1, this._brush_size-=1);  

};

J.controller.prototype.reload_tiles = function(values) {

  var z = values['z'];
  var full_bbox = JSON.parse(values['full_bbox']);


  var x = this._viewer._camera._x;
  var y = this._viewer._camera._y;
  var z2 = this._viewer._camera._z; // the actual displayed z
  var w = this._viewer._camera._w;
  this._viewer._loader.clear_cache_segmentation(x,y,z,w);

  for (var l=0;l<this._viewer._image.zoomlevel_count;l++) {  

    // only draw if current z == z2 and l == w (meaning only if zoomlevel and z are displayed right now)
    var draw = (z == z2 && w == l);
    // console.log('reload tile', l, draw, full_bbox);
    this._viewer._loader.load_tiles(x,y,z,l,l,!draw); // negate draw since it is a no_draw flag woot woot

  }
  
  // update 3d with lowest zoomlevel (== always one tile)
  // setTimeout(function() {

    var lowest_w = this._viewer._image.zoomlevel_count-1;
    this._viewer._loader.get_segmentation(0, 0, z, lowest_w, function(x, y, z, lowest_w, s) {
      
      this.update_3D_textures(z, full_bbox, s);

    }.bind(this, 0, 0, z, lowest_w));

  // }.bind(this),2000); // TODO this should not be fixed
  

};

J.controller.prototype.update_3D_textures = function(z, full_bbox, texture) {

  if (!DOJO.threeD) return;

  // console.log(full_bbox, texture);
  // console.log('upd 3d', full_bbox);

  var x1 = Math.floor(full_bbox[0] / this._viewer._image.zoom_levels[0][2]);
  var y1 = Math.floor(full_bbox[1] / this._viewer._image.zoom_levels[0][2]);
  var x2 = Math.floor(full_bbox[2] / this._viewer._image.zoom_levels[0][2]);
  var y2 = Math.floor(full_bbox[3] / this._viewer._image.zoom_levels[0][2]);

  // var byte_start = (x1+y1*512)*4;
  // var byte_end = (x2+y2*512)*4+4;

  // console.log('a',byte_start, byte_end, texture.length)

  var vol = DOJO.threeD.volume;
  var dim_x = vol.dimensions[0];
  var dim_y = vol.dimensions[1];
  var dim_z = vol.dimensions[2];

  // update pixel data in z
  vol.children[2].children[z].labelmap.texture.updateTexture(texture);
  vol.children[2].children[z].labelmap.modified();

  var bytes_start_t = (x1+y1*512)*4;
  var bytes_end_t = (x1+y2*512)*4;

  var bytes_per_value = 4;

  var nb_pix_per_z = 512*512;

  var px = 0;
  for (var p=bytes_start_t; p<bytes_end_t; p+=bytes_per_value) {

    //var z = Math.floor(px / nb_pix_per_z);
    var y = Math.floor((px % nb_pix_per_z) / dim_x);
    var x = Math.floor((px % nb_pix_per_z) % dim_x);

    // var z_index = (x + y*dim_y)*bytes_per_value;
    var y_index = (x + z*dim_x)*bytes_per_value;
    var x_index = (y + z*dim_y)*bytes_per_value;

    var old_data_x = vol.children[0].children[x].labelmap.texture.rawData;
    var old_data_y = vol.children[1].children[y].labelmap.texture.rawData;

    for (var i=0;i<bytes_per_value;i++) {

      old_data_x[x_index+i] = texture[p+i];
      old_data_y[y_index+i] = texture[p+i];
      // slices_z[z][z_index+i] = data[p+i];

    }

    px++;

  }

  for (var x=0; x<dim_x; ++x) {

    var old_data_x = vol.children[0].children[x].labelmap.texture.rawData;
    vol.children[0].children[x].labelmap.texture.updateTexture(old_data_x);
    vol.children[0].children[x].labelmap.modified();

  }

  for (var y=0; y<dim_y; ++y) {

    var old_data_y = vol.children[1].children[y].labelmap.texture.rawData;
    vol.children[1].children[y].labelmap.texture.updateTexture(old_data_y);
    vol.children[1].children[y].labelmap.modified();

  }

  // // update pixel data in x
  // for (var x=x1;x<x2;x++) {

  //   var labelmap_x = vol.children[0].children[x].labelmap;

  //   var offset_x = x;
  //   var old_data = vol.children[0].children[x].labelmap.texture.rawData;
  //   // replace pixels
  //   var bytes_start_t = (x1+offset_x+y1*512)*4;
  //   var bytes_end_t = (x1+offset_x+y2*512)*4+4;
  //   // var cur_x = (dim[2] - z)*4;
  //   // var cur_y = (y1)*4;
  //   // var bytes_start_x = cur_x + cur_y*dim[2];
  //   var bytes_start_x = (y1+z*dim[1])*4;
  //   console.log(bytes_start_t, bytes_end_t, bytes_start_x);
  //   old_data.set(texture.subarray(bytes_start_t, bytes_end_t), bytes_start_x);

  //   labelmap_x.texture.updateTexture(old_data);
  //   labelmap_x.modified();
  // }



};

J.controller.prototype.start_adjust = function(id, x, y) {

  if (this._adjust_mode != -1) return;

  console.log('start adjust');

  this._adjust_mode = 1;
  this._adjust_id = id;
  this._brush_ijs = [];

  this._viewer._canvas.style.cursor = 'crosshair';

  this.activate(id);

};

J.controller.prototype.draw_adjust = function(x, y) {

  if (this._adjust_mode != 1 && this._adjust_mode != 2) return;

  this._adjust_mode = 2;

  var i_js = this._viewer.xy2ij(x, y);

  // this._viewer.get_segmentation_id(i_js[0], i_js[1], function(id) {

    // if (this._adjust_id == id) return;

    var color = this._viewer.get_color(this._adjust_id);

    var id = this._viewer._overlay_buffer_context.createImageData(this._brush_size, this._brush_size);
    var d = id.data;
    for(var j=0;j<this._brush_size*this._brush_size;j++) {
      d[j*4+0] = color[0];
      d[j*4+1] = color[1];
      d[j*4+2] = color[2];
      d[j*4+3] = this._viewer._overlay_opacity;
    }

    var brush_ij = [Math.floor(i_js[0]-this._brush_size/2), Math.floor(i_js[1]-this._brush_size/2)];
    var u_v = this._viewer.ij2uv_no_zoom(brush_ij[0], brush_ij[1]);

    this._brush_ijs.push(brush_ij);

    this._viewer._overlay_buffer_context.putImageData(id, u_v[0], u_v[1]);

  // }.bind(this));

};

J.controller.prototype.end_adjust = function() {

  if (this._adjust_mode != 2) return;

  // send via ajax (id, brush_bbox, brush_i_js, z, brushsize)
  var data = {};
  data['id'] = this._adjust_id;
  data['i_js'] = this._brush_ijs;
  data['z'] = this._viewer._camera._z;
  data['brush_size'] = this._brush_size;
  this.send('ADJUST', data);

  this._adjust_mode = 3;

  this._viewer._canvas.style.cursor = '';

};

J.controller.prototype.finish_adjust = function(values) {

  // reload all slices, set to split mode -1
  this.reload_tiles(values);

  this._viewer.clear_overlay_buffer();

  this._adjust_mode = -1;
  this.activate(null);

  var color1 = DOJO.viewer.get_color(this._adjust_id);
  var color1_hex = rgbToHex(color1[0], color1[1], color1[2]);
  var log = 'User $USER adjusted label <font color="'+color1_hex+'">'+this._adjust_id+'</font>.';
  this.send_log(log);  

};

J.controller.prototype.finish_split = function(values) {

  // reload all slices, set to split mode -1
  this.reload_tiles(values);

  this._viewer.clear_overlay_buffer();

  this._split_mode = -1;
  this.activate(null);


  var color1 = DOJO.viewer.get_color(this._split_id);
  var color1_hex = rgbToHex(color1[0], color1[1], color1[2]);
  var log = 'User $USER splitted label <font color="'+color1_hex+'">'+this._split_id+'</font>.';
  this.send_log(log);

};

J.controller.prototype.start_split = function(id, x, y) {

  if (this._split_mode == -1) {
    // select label
    // console.log('splitting', id);
    this._split_mode = 1;
    this._split_id = id;
    this.activate(id);    

    this._viewer._canvas.style.cursor = 'crosshair';

  } else if (this._split_mode == 1) {
    // start drawing
    //ar u_v = this._viewer.xy2uv(x*this._viewer._camera._view[0],y*this._viewer._camera._view[4]);
    var i_j = this._viewer.xy2ij(x, y);
    var u_v = this._viewer.ij2uv_no_zoom(i_j[0],i_j[1]);
    // var u_v = this._viewer.ij2uv(i_j[0], i_j[1]);
    // var u_v = [x*this._viewer._camera._view[0],y*this._viewer._camera._view[4]];

    var context = this._viewer._overlay_buffer_context;

    // context.save();
    // var view = this._viewer._camera._view;
    //context.setTransform(view[0], view[1], view[3], view[4], 0,0);
    this._brush_ijs = [];
    this._brush_bbox = [];
    context.beginPath();
    context.moveTo(u_v[0], u_v[1]);
    // context.restore();

  } else if (this._split_mode == 4) {

    // user picked the region
    var i_j = this._viewer.xy2ij(x, y);

    var data = {};
    data['id'] = this._split_id;
    data['line'] = this._split_line;
    data['z'] = this._viewer._camera._z;
    data['click'] = i_j;
    data['bbox'] = this._brush_bbox;
    this.send('FINALIZESPLIT', data);

  }



};

J.controller.prototype.show_split_line = function(i_js) {

  // clear marked line
  this._viewer.clear_overlay_buffer();

  if (i_js.length == 0) {
    console.log('Invalid split line.');
    this._split_mode = 1;
    return;
  }

  var id = this._viewer._overlay_buffer_context.createImageData(1,1);
  var d = id.data;
  d[0] = 0;
  d[1] = 255;
  d[2] = 0;
  d[3] = 255;

  var i_js_count = i_js.length;  

  for(var i=0;i<i_js_count;i++) {

    var u_v = this._viewer.ij2uv_no_zoom(i_js[i][0], i_js[i][1]);

    this._viewer._overlay_buffer_context.putImageData(id, u_v[0], u_v[1]);

  }

  this._viewer.rerender();

  this._split_mode = 4;
  this._split_line = i_js;

};

J.controller.prototype.discard = function() {

  if (this._split_mode == 4) {
    // line was drawn, user pressed ESC
    console.log('Discard split');

    // stay in split mode but start over
    this._split_mode = 1;
    // and reset
    this._brush_bbox = [];
    this._brush_ijs = [];    
    this._viewer._canvas.style.cursor = 'crosshair';

    this._viewer.clear_overlay_buffer();
  } else {

    this._adjust_mode = -1;
    this._adjust_id = -1;

    this._split_mode = -1;
    this._brush_bbox = [];
    this._brush_ijs = []; 
    this._last_id = null;   
    this.activate(null);
    this._viewer._canvas.style.cursor = '';
    this._viewer.clear_overlay_buffer();
  }

};

J.controller.prototype.draw_split = function(x, y) {

  if (this._split_mode == 1 || this._split_mode == 2) {
   
    this._split_mode = 2;
    // var u_v = this._viewer.xy2uv(x*this._viewer._camera._view[0],y*this._viewer._camera._view[4]);
    var i_j = this._viewer.xy2ij(x, y);
    if (i_j[0] == -1) return;
    var u_v = this._viewer.ij2uv_no_zoom(i_j[0],i_j[1]);
    // console.log(i_j, u_v)
    // console.log(i_j);
    // var u_v = this._viewer.ij2uv(i_j[0], i_j[1]);  
    // console.log(u_v);  
    //var u_v = [x*this._viewer._camera._view[0],y*this._viewer._camera._view[4]];
    // console.log('draw split');

    var context = this._viewer._overlay_buffer_context;

    // context.save();
    // var view = this._viewer._camera._view;
    //context.setTransform(view[0], view[1], view[3], view[4], 0,0);

    // update bounding box
    if (this._brush_bbox.length > 0) {

      var brush = Math.ceil(this._brush_size);

      var factor = 1;

      // smallest i
      this._brush_bbox[0] = Math.max(0,Math.min(this._brush_bbox[0], i_j[0]-factor*brush));
      // largest i
      this._brush_bbox[1] = Math.max(0,Math.max(this._brush_bbox[1], i_j[0]+factor*brush));
      // smallest j
      this._brush_bbox[2] = Math.max(0,Math.min(this._brush_bbox[2], i_j[1]-factor*brush));
      // largest j
      this._brush_bbox[3] = Math.max(0,Math.max(this._brush_bbox[3], i_j[1]+factor*brush));
      
    } else {
      this._brush_bbox.push(Math.max(i_j[0]));
      this._brush_bbox.push(Math.max(0,i_j[0]));
      this._brush_bbox.push(Math.max(i_j[1]));
      this._brush_bbox.push(Math.max(i_j[1]));
    }

    // and store the i_j's for later use
    this._brush_ijs.push(i_j);

    context.lineTo(u_v[0], u_v[1]);
    context.strokeStyle = 'rgba(0,191,255,0.1)';
    context.lineWidth = this._brush_size;
    context.stroke();
    // context.restore();
  }

};

J.controller.prototype.end_draw_split = function(x, y) {

  if (this._split_mode == 2) {
    console.log('end draw', x, y);

    // one more stroke..
    this.draw_split(x, y);

    var context = this._viewer._image_buffer_context;    
    context.closePath();

    // console.log(this._brush_bbox);
    // console.log(this._brush_ijs);

    // send via ajax (id, brush_bbox, brush_i_js, z, brushsize)
    var data = {};
    data['id'] = this._split_id;
    data['brush_bbox'] = this._brush_bbox;
    data['i_js'] = this._brush_ijs;
    data['z'] = this._viewer._camera._z;
    data['brush_size'] = this._brush_size;
    this.send('SPLIT', data);



    this._split_mode = 3;

    this._viewer._canvas.style.cursor = '';

  }



};

J.controller.prototype.merge = function(id) {

  if (!this._merge_table) {
    throw new Error('Merge-table does not exist.');
  }

  if (!this._last_id) {
    this._last_id = this._viewer.lookup_id(id);

    this.activate(id);

    return;
  }

  if (this._last_id == id) return;

  // console.log('Merging', this._last_id, id);

  // if (!(id in this._merge_table)) {
  //   this._merge_table[id] = [];
  // }

  // this._merge_table[id].push(this._last_id);

  this._merge_table[id] = this._last_id;

  var color1 = DOJO.viewer.get_color(id);
  var color1_hex = rgbToHex(color1[0], color1[1], color1[2]);
  var color2 = DOJO.viewer.get_color(this._last_id);
  var color2_hex = rgbToHex(color2[0], color2[1], color2[2]);

  var colored_id1 = id;
  var colored_id2 = this._last_id;

  var log = 'User $USER merged labels <font color="'+color1_hex+'">'+colored_id1+'</font> and <font color="'+color2_hex+'">' +colored_id2 + '</font>.';

  this.send_log(log);
  // shouldn't be required
  // DOJO.update_log(log);

  // this._viewer.redraw();

  this.create_gl_merge_table();

  // this._viewer.redraw();

  this.send_merge_table();

  this.highlight(this._last_id);

};

J.controller.prototype.undo = function(x, y) {

  var i_j = this._viewer.xy2ij(x, y);

  if (i_j[0] == -1) return;

  this._viewer.get_segmentation_id_before_merge(i_j[0], i_j[1], function(id) {

    delete this._merge_table[id];


    var color1 = DOJO.viewer.get_color(id);
    var color1_hex = rgbToHex(color1[0], color1[1], color1[2]);

    var colored_id1 = id;

    var log = 'User $USER removed merge for label <font color="'+color1_hex+'">'+colored_id1+'</font>.';

    this.send_log(log);

    this.create_gl_merge_table();

    // this._viewer.redraw();

    this.send_merge_table();  

    this.activate(null);


  }.bind(this));

};

J.controller.prototype.create_gl_merge_table = function() {

  var keys = Object.keys(this._merge_table);
  var no_keys = keys.length;

  if (no_keys == 0) {

    // we need to pass an empty array to the GPU
    this._merge_table_length = 2;
    this._gl_merge_table_keys = new Uint8Array(4 * 2);
    this._gl_merge_table_values = new Uint8Array(4 * 2);
    return;

  }

  var new_length = Math.pow(2,Math.ceil(Math.log(no_keys)/Math.log(2)));

  this._merge_table_length = new_length;

  this._gl_merge_table_keys = new Uint8Array(4 * new_length);

  var pos = 0;
  for (var k=0; k<no_keys; k++) {
    // pack value to 4 bytes (little endian)
    var value = parseInt(keys[k],10);
    var b = from32bitTo8bit(value);
    this._gl_merge_table_keys[pos++] = b[0];
    this._gl_merge_table_keys[pos++] = b[1];
    this._gl_merge_table_keys[pos++] = b[2];
    this._gl_merge_table_keys[pos++] = b[3];
  }

  this._gl_merge_table_values = new Uint8Array(4 * new_length);

  pos = 0;
  for (var k=0; k<no_keys; k++) {
    // pack value to 4 bytes (little endian)
    var key = parseInt(keys[k],10);
    var value = this._merge_table[key];
    var b = from32bitTo8bit(value);
    this._gl_merge_table_values[pos++] = b[0];
    this._gl_merge_table_values[pos++] = b[1];
    this._gl_merge_table_values[pos++] = b[2];
    this._gl_merge_table_values[pos++] = b[3];
  }  

};

J.controller.prototype.create_gl_lock_table = function() {

  var keys = Object.keys(this._lock_table);
  var no_keys = keys.length;

  if (no_keys == 0) {

    // we need to pass an empty array to the GPU
    this._lock_table_length = 2;
    this._gl_lock_table = new Uint8Array(4 * 2);
    return;

  }

  var new_length = Math.pow(2,Math.ceil(Math.log(no_keys)/Math.log(2)));

  this._gl_lock_table = new Uint8Array(4 * new_length);

  this._lock_table_length = new_length;

  var pos = 0;
  for (var i=0; i<no_keys; i++) {

    var b = from32bitTo8bit(keys[i]);
    this._gl_lock_table[pos++] = b[0];
    this._gl_lock_table[pos++] = b[1];
    this._gl_lock_table[pos++] = b[2];
    this._gl_lock_table[pos++] = b[3];

  }

};

J.controller.prototype.create_gl_3d_labels = function() {

  var keys = Object.keys(this._3d_labels);
  var no_keys = keys.length;

  if (no_keys == 0) {

    // we need to pass an empty array to the GPU
    this._gl_3d_labels_length = 2;
    this._gl_3d_labels = new Uint8Array(4 * 2);
    return;

  }

  var new_length = Math.pow(2,Math.ceil(Math.log(no_keys)/Math.log(2)));

  this._gl_3d_labels = new Uint8Array(4 * new_length);

  this._gl_3d_labels_length = new_length;

  var pos = 0;
  for (var i=0; i<no_keys; i++) {

    var b = from32bitTo8bit(keys[i]);
    this._gl_3d_labels[pos++] = b[0];
    this._gl_3d_labels[pos++] = b[1];
    this._gl_3d_labels[pos++] = b[2];
    this._gl_3d_labels[pos++] = b[3];

  }

};

J.controller.prototype.is_3d_label = function(id) {

  return (id in this._3d_labels && id != this._highlighted_id);

};

J.controller.prototype.add_3d_label = function(id) {

  this._3d_labels[id] = true;

  this.create_gl_3d_labels();
  this.update_threeD();

};

J.controller.prototype.add_fixed_3d_label = function(id) {
  this._fixed_3d_labels[id] = true;


};

J.controller.prototype.remove_3d_label = function(id) {

  delete this._3d_labels[id];

  this.create_gl_3d_labels();
  this.update_threeD();

};

J.controller.prototype.remove_fixed_3d_label = function(id) {

  delete this._fixed_3d_labels[id];

};

J.controller.prototype.reset_3d_labels = function() {

  this._3d_labels = {};

  this._use_3d_labels = false;

  for (var k in this._fixed_3d_labels) {
    this._3d_labels[k] = true;

    this._use_3d_labels = true;
  }

  this.create_gl_3d_labels();

  

  this.update_threeD();


};

J.controller.prototype.reset_fixed_3d_labels = function() {

  this._fixed_3d_labels = {};

};

J.controller.prototype.highlight_in_3d = function(id, clear) {

  if (this._highlighted_id && !(this._highlighted_id in this._fixed_3d_labels))
    this.remove_3d_label(this._highlighted_id);

  this.add_3d_label(id);

  if (this._activated_id) {
    this.add_3d_label(this._activated_id);    
  }

  this._use_3d_labels = true;

};

J.controller.prototype.toggle_3d_labels = function() {

  this._use_3d_labels = !this._use_3d_labels;

  this.update_threeD();

};

J.controller.prototype.end = function() {

  
  this._viewer.clear_overlay_buffer();

  this._split_mode = -1;
  this._adjust_mode = -1;
  this._adjust_id = -1;
  this._split_id = -1;
  this._viewer._canvas.style.cursor = '';
  this._last_id = null;

  this.activate(null);

};
