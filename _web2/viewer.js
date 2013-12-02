DOJO.canvas = function(container) {

  var _container = document.getElementById(container);

  var _canvas = document.createElement('canvas');
  _canvas.width = _container.clientWidth;
  _canvas.height = _container.clientHeight;
  _container.appendChild(_canvas);

  this._canvas = _canvas;

  this.init();

};

DOJO.canvas.prototype.init = function() {

  // get contents
  $.ajax({url:'/image/contents'}).done(function(res) {

    this._image = JSON.parse(res);

    $.ajax({url:'/segmentation/contents'}).done(function(res) {

      this._segmentation = JSON.parse(res);

    }.bind(this));

  }.bind(this));

};


DOJO.canvas.prototype.open = function(tiles) {

  // get contents
  $.ajax({url:tiles[0]+'content'}).done(function(res) {

    res = JSON.parse(res);

    var i = new Image();
    i.src = tiles[0] + '/' + (parseInt(res.zoomlevel_count,10)-1)+ '/0_0.jpg';

    i.onload = function() {
      console.log('done');

      var c = this._canvas.getContext('2d');
      c.drawImage(i,10,10,1024,1024);

    }.bind(this);

  });

  console.log(tiles[0]);


};

