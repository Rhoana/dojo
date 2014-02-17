var J = J || {};

J.offscreen_renderer = function(viewer) {

  this._viewer = viewer;
  this._canvas = this._viewer._offscreen_buffer;

  this._gl = null;

  this._program = null;

  this._square_buffer = null;
  this._image_texture_buffer = null;
  this._segmentation_texture_buffer = null;
  this._uv_buffer = null;

};

J.offscreen_renderer.prototype.init = function(vs_id, fs_id) {

  var canvas = this._canvas;
  var gl = canvas.getContext('experimental-webgl') || canvas.getContext('webgl');

  if (!gl) {
    return false;
  }

  // store the canvas size
  gl.viewportWidth = canvas.width;
  gl.viewportHeight = canvas.height;

  gl.viewport(0, 0, gl.viewportWidth, gl.viewportHeight);
  gl.clearColor(0,0,0,0);//128./255., 200./255., 255./255., 1.);
  gl.clearDepth(0);
  // gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
  // gl.pixelStorei(gl.PACK_ALIGNMENT, 1);

  // enable transparency
  // gl.blendEquation(gl.FUNC_ADD);
  // gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  // gl.enable(gl.BLEND);

  // gl.enable(gl.DEPTH_TEST);
  // gl.depthFunc(gl.GREATER);

  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  // create shaders
  this._program = linkShaders(gl, vs_id, fs_id);
  var h = this._program;
  gl.useProgram(h);

  this.h_uTextureSampler = gl.getUniformLocation(h, 'uTextureSampler');
  // this.h_uTextureSampler2 = gl.getUniformLocation(h, 'uTextureSampler2');  

  this.h_aPosition = gl.getAttribLocation(h, 'aPosition');
  this.h_aTexturePosition = gl.getAttribLocation(h, 'aTexturePosition');

  // create geometry
  this._square_buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, this._square_buffer);
  var vertices = new Float32Array([
     1.,  1., 0.,
    -1.,  1., 0.,
     1., -1., 0.,
    -1, -1., 0.
    ]);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

  this._gl = gl;

  return true;

};

J.offscreen_renderer.prototype.draw = function(s) {

  var gl = this._gl;

  // create segmentation texture buffer
  this._segmentation_texture_buffer = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, this._segmentation_texture_buffer);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 512, 512, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(s.buffer));

  // clamp to edge
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);

  gl.bindTexture(gl.TEXTURE_2D, null);

  // u-v
  this._uv_buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, this._uv_buffer);
  var uvs = new Float32Array([
    1., 1.,
    0., 1.,
    1., 0.,
    0., 0.
    ]);
  gl.bufferData(gl.ARRAY_BUFFER, uvs, gl.STATIC_DRAW);

  // now really draw
  gl.enableVertexAttribArray(this.h_aPosition);
  gl.bindBuffer(gl.ARRAY_BUFFER, this._square_buffer);
  gl.vertexAttribPointer(this.h_aPosition, 3, gl.FLOAT, false, 0, 0);

  gl.activeTexture(gl.TEXTURE0);

  gl.bindTexture(gl.TEXTURE_2D, this._segmentation_texture_buffer);
  gl.uniform1i(this.h_uTextureSampler, 0);

  gl.enableVertexAttribArray(this.h_aTexturePosition);
  gl.bindBuffer(gl.ARRAY_BUFFER, this._uv_buffer);
  gl.vertexAttribPointer(this.h_aTexturePosition, 2, gl.FLOAT, false, 0, 0);  

  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

  var array = new Uint8Array(1048576);
  gl.readPixels(0, 0, 512, 512, gl.RGBA, gl.UNSIGNED_BYTE, array);

  return array;

};