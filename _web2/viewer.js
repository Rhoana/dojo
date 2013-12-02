DOJO.canvas = function(container) {

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

  // a c e
  // b d f
  // 0 0 1
  this._view = [2, 0, 0, 0, 2, 0, 0, 0, 1];

  this.init();

};

DOJO.canvas.prototype.init = function() {

  // get contents
  $.ajax({url:'/image/contents'}).done(function(res) {

    this._image = JSON.parse(res);

    // type cast some stuff
    this._image.width = parseInt(this._image.width, 10);
    this._image.height = parseInt(this._image.height, 10);

    this._image_buffer.width = this._image.width;
    this._image_buffer.height = this._image.height;

    $.ajax({url:'/segmentation/contents'}).done(function(res) {

      this._segmentation = JSON.parse(res);

      this.load_image(0,0,0,parseInt(this._image.zoomlevel_count,10)-1);

    }.bind(this));

  }.bind(this));

};

DOJO.canvas.prototype.load_image = function(x, y, z, w) {

  console.log('Loading',x,y,z,w);

  var i = new Image();
  i.src = '/image/'+pad(z,8)+'/'+w+'/'+x+'_'+y+'.jpg';
  i.onload = function() {
    this.draw_image(x,y,z,w,i);

    this.render();

  }.bind(this);

};

DOJO.canvas.prototype.draw_image = function(x,y,z,w,i) {

  console.log('Drawing',x,y,z,w);

  this._image_buffer_context.drawImage(i,0,0,512,512,x*512,y*512,512,512);

};

DOJO.canvas.prototype.render = function() {

  var _width = this._width;
  var _height = this._height;

  this._context.save();
  this._context.clearRect(-_width, -_height, 2 * _width, 2 * _height);
  this._context.restore();

  this._context.setTransform(this._view[0], this._view[1], this._view[3], this._view[4], this._view[6], this._view[7]);

  // put image buffer
  this._context.drawImage(this._image_buffer, 0, 0);

  this._AnimationFrameID = window.requestAnimationFrame(this.render.bind(this));

};

DOJO.canvas.prototype.zoom = function(level) {
  this._view[0] = level;
  this._view[4] = level;
}