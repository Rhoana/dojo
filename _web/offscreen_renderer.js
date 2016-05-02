var J = J || {};

J.offscreen_renderer = function(viewer) {

  this._viewer = viewer;
  this._canvas = this._viewer._offscreen_buffer;
  this._controller = this._viewer._controller;

  this._gl = null;

  this._program = null;

  this._square_buffer = null;
  this._uv_buffer = null;

  this._width = this._canvas.width;
  this._height = this._canvas.height;

  this._merge_table_changed = true;

};

J.offscreen_renderer.prototype.init = function(vs_id, fs_id) {

  var canvas = this._canvas;
  var gl = canvas.getContext('experimental-webgl') || canvas.getContext('webgl');

  if (!gl) {
    return false;
  }

  gl.viewport(0, 0, this._width, this._height);
  gl.clearColor(0,0,0,1.);
  gl.clearDepth(0);

  // enable transparency
  gl.blendEquation(gl.FUNC_ADD);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.enable(gl.BLEND);

  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);

  // create shaders
  this._program = linkShaders(gl, vs_id, fs_id);
  var h = this._program;
  if (!h) {
    return false;
  }
  gl.useProgram(h);

  // textures Hoffer 2016-03-13
  this.h_uImageSampler = gl.getUniformLocation(h, 'uImageSampler');
  this.h_uTextureSampler = gl.getUniformLocation(h, 'uTextureSampler');
  this.h_uColorMapSampler = gl.getUniformLocation(h, 'uColorMapSampler');
  this.h_uMergeTableKeySampler = gl.getUniformLocation(h, 'uMergeTableKeySampler');
  this.h_uMergeTableValueSampler = gl.getUniformLocation(h, 'uMergeTableValueSampler');
  this.h_uLockTableSampler = gl.getUniformLocation(h, 'uLockTableSampler');

  this.h_uOpacity = gl.getUniformLocation(h, 'uOpacity');
  this.h_uHighlightedId = gl.getUniformLocation(h, 'uHighlightedId');
  this.h_uActivatedId = gl.getUniformLocation(h, 'uActivatedId');
  this.h_uSplitMode = gl.getUniformLocation(h, 'uSplitMode');  
  this.h_uAdjustMode = gl.getUniformLocation(h, 'uAdjustMode');  
  this.h_uMaxColors = gl.getUniformLocation(h, 'uMaxColors');
  this.h_uBorders = gl.getUniformLocation(h, 'uBorders');
  this.h_uOnlyLocked = gl.getUniformLocation(h, 'uOnlyLocked');
  this.h_uMergeTableEnd = gl.getUniformLocation(h, 'uMergeTableEnd');
  this.h_uMergeTableLength = gl.getUniformLocation(h, 'uMergeTableLength');
  this.h_uLockTableLength = gl.getUniformLocation(h, 'uLockTableLength');
  this.h_uShowOverlay = gl.getUniformLocation(h, 'uShowOverlay');
  // this.h_uTextureSampler2 = gl.getUniformLocation(h, 'uTextureSampler2');  

  this.h_aPosition = gl.getAttribLocation(h, 'aPosition');
  this.h_aTexturePosition = gl.getAttribLocation(h, 'aTexturePosition');

  // create geometry
  this._square_buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, this._square_buffer);
  var vertices = new Float32Array([
    -1, -1., 0.,
     1., -1., 0.,
    -1.,  1., 0.,
    1.,  1., 0.
    ]);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

  this._gl = gl;

  this.init_buffers();

  return true;

};

J.offscreen_renderer.prototype.init_buffers = function() {

  var gl = this._gl;

  // create colormap texture buffer
  this._colormap_texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, this._colormap_texture);

  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);

  gl.bindTexture(gl.TEXTURE_2D, null);

  // create segmentation texture buffer
  this._segmentation_texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, this._segmentation_texture);

  // clamp to edge
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);

  gl.bindTexture(gl.TEXTURE_2D, null);


  // create image texture buffer
  this._image_texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, this._image_texture);

  // clamp to edge
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);

  gl.bindTexture(gl.TEXTURE_2D, null);  


  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
  this._merge_table_keys = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, this._merge_table_keys);

  // clamp to edge
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);

  gl.bindTexture(gl.TEXTURE_2D, null);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);

  this._merge_table_values = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, this._merge_table_values);
  
  // clamp to edge
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);

  gl.bindTexture(gl.TEXTURE_2D, null);


  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
  this._lock_table = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, this._lock_table);

  // clamp to edge
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);

  gl.bindTexture(gl.TEXTURE_2D, null);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);

  // u-v
  this._uv_buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, this._uv_buffer);
  var uvs = new Float32Array([
    0., 0.,
    1., 0.,
    0., 1.,
    1., 1.
    ]);
  gl.bufferData(gl.ARRAY_BUFFER, uvs, gl.STATIC_DRAW);  

};

J.offscreen_renderer.prototype.draw = function(i, s, c, x, y) {

  var gl = this._gl;

  gl.viewport(0, 0, this._width, this._height);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);


  if (this._controller._gl_colormap_changed) {

    // update colormap texture buffer
    gl.bindTexture(gl.TEXTURE_2D, this._colormap_texture);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, this._viewer._max_colors, 1, 0, gl.RGB, gl.UNSIGNED_BYTE, this._viewer._gl_colormap);

    this._controller._gl_colormap_changed = false;

  }



  // create segmentation texture buffer
  gl.bindTexture(gl.TEXTURE_2D, this._segmentation_texture);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 512, 512, 0, gl.RGBA, gl.UNSIGNED_BYTE, s);


  // create image texture buffer
  gl.bindTexture(gl.TEXTURE_2D, this._image_texture);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, i);


  //
  // MERGE TABLE
  //
  var merge_table_length = this._controller._merge_table_length;
  var merge_table_end = this._controller._merge_table_end;

  if (this._controller._gl_merge_table_changed) {

    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);

    gl.bindTexture(gl.TEXTURE_2D, this._merge_table_keys);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, merge_table_length, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, this._controller._gl_merge_table_keys);

    gl.bindTexture(gl.TEXTURE_2D, this._merge_table_values);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, merge_table_length, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, this._controller._gl_merge_table_values);
  
    this._controller._gl_merge_table_changed = false;

    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);

  }
  

  //
  // LOCK TABLE
  //
  var lock_table_length = this._controller._lock_table_length;

  if (this._controller._gl_lock_table_changed) {

    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);

    gl.bindTexture(gl.TEXTURE_2D, this._lock_table);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, lock_table_length, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, this._controller._gl_lock_table);

    this._controller._gl_lock_table_changed = false;    

    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);    

  }





  // now really draw
  gl.enableVertexAttribArray(this.h_aPosition);
  gl.bindBuffer(gl.ARRAY_BUFFER, this._square_buffer);
  gl.vertexAttribPointer(this.h_aPosition, 3, gl.FLOAT, false, 0, 0);

  // some values
  gl.uniform1f(this.h_uActivatedId, this._viewer._controller._activated_id);
  gl.uniform1f(this.h_uHighlightedId, this._viewer._controller._highlighted_id);
  gl.uniform1f(this.h_uOpacity, this._viewer._overlay_opacity);
  gl.uniform1f(this.h_uMaxColors, this._viewer._max_colors);
  gl.uniform1i(this.h_uBorders, this._viewer._overlay_borders);
  gl.uniform1i(this.h_uOnlyLocked, this._viewer._only_locked);

  gl.uniform1i(this.h_uSplitMode, this._viewer._controller._split_mode);
  gl.uniform1i(this.h_uAdjustMode, this._viewer._controller._adjust_mode);

  gl.uniform1i(this.h_uMergeTableEnd, merge_table_end);
  gl.uniform1i(this.h_uMergeTableLength, merge_table_length);
  gl.uniform1i(this.h_uLockTableLength, lock_table_length);
  gl.uniform1i(this.h_uShowOverlay, this._viewer._overlay_show);


  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, this._segmentation_texture);
  gl.uniform1i(this.h_uTextureSampler, 0);

  gl.activeTexture(gl.TEXTURE1);
  gl.bindTexture(gl.TEXTURE_2D, this._colormap_texture);
  gl.uniform1i(this.h_uColorMapSampler, 1);

  gl.activeTexture(gl.TEXTURE2);
  gl.bindTexture(gl.TEXTURE_2D, this._merge_table_keys);
  gl.uniform1i(this.h_uMergeTableKeySampler, 2);

  gl.activeTexture(gl.TEXTURE3);
  gl.bindTexture(gl.TEXTURE_2D, this._merge_table_values);
  gl.uniform1i(this.h_uMergeTableValueSampler, 3);

  gl.activeTexture(gl.TEXTURE4);
  gl.bindTexture(gl.TEXTURE_2D, this._lock_table);
  gl.uniform1i(this.h_uLockTableSampler, 4);

  gl.activeTexture(gl.TEXTURE5);
  gl.bindTexture(gl.TEXTURE_2D, this._image_texture);
  gl.uniform1i(this.h_uImageSampler, 5);  

  gl.enableVertexAttribArray(this.h_aTexturePosition);
  gl.bindBuffer(gl.ARRAY_BUFFER, this._uv_buffer);
  gl.vertexAttribPointer(this.h_aTexturePosition, 2, gl.FLOAT, false, 0, 0);  

  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

  c.drawImage(this._canvas,0,0,512,512,x*512,y*512,512,512);

};