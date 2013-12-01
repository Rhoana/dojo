DOJO.renderer = function(container) {
  
  var _container = document.getElementById(container);

  var _canvas = document.createElement('canvas');
  _canvas.width = _container.clientWidth;
  _canvas.height = _container.clientHeight;
  _container.appendChild(_canvas);

  this._canvas = _canvas;

};

DOJO.renderer.prototype.open = function(tiles) {



};

