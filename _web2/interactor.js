var J = J || {};

J.interactor = function(viewer) {

  this._viewer = viewer;

  this.init();

};

J.interactor.prototype.init = function() {

  // mouse wheel
  this._viewer._canvas.onmousewheel = this.onmousewheel.bind(this);



};

J.interactor.prototype.onmousewheel = function(e) {

  console.log(e);


};


