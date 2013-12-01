DOJO.renderer = function(container) {

  var _container = document.getElementById(container);

  var _canvas = document.createElement('canvas');
  _canvas.width = _container.clientWidth;
  _canvas.height = _container.clientHeight;
  _container.appendChild(_canvas);

  this._canvas = _canvas;

};

DOJO.renderer.prototype.open = function(tiles) {

  console.log(tiles[0]);

  var i = new Image();
  i.src = 'http://monster.krash.net:1337/image/00000000/9/0_0.jpg';

  i.onload = function() {
    console.log('done');

    var c = this._canvas.getContext('2d');
    c.drawImage(i,10,10,1024,1024);

  }.bind(this);

};

