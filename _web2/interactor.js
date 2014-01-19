var J = J || {};

J.interactor = function(viewer) {

  this._viewer = viewer;

  this._scale = 1;
  this._originx = 0;
  this._originy = 0;  

  this._left_down = false;
  this._right_down = false;

  this._last_mouse = [0,0];

  this.init();

};

J.interactor.prototype.init = function() {

  // mouse move
  this._viewer._canvas.onmousemove = this.onmousemove.bind(this);

  // mouse down and up
  this._viewer._canvas.onmousedown = this.onmousedown.bind(this);
  this._viewer._canvas.onmouseup = this.onmouseup.bind(this);
  this._viewer._canvas.oncontextmenu = function() { return false; };

  // mouse wheel
  this._viewer._canvas.onmousewheel = this.onmousewheel.bind(this);



};

J.interactor.prototype.onmousemove = function(e) {

  var x = e.clientX;
  var y = e.clientY;

  var u_v = this._viewer.xy2uv(x, y);

  // jump out if we are not inside the real image data
  if (u_v[0] == -1 || u_v[1] == -1) {
    return;
  }

  if (this._left_down) {
    
  } else if (this._right_down) {
    // pan
    this._viewer._camera.pan(x-this._last_mouse[0], y-this._last_mouse[1]);    
  }

  console.log(this._left_down, e.clientX, e.clientY, u_v[0], u_v[1], this._viewer._camera._view[0], this._viewer._camera._view[6]);

  this._last_mouse = [x, y];

};

J.interactor.prototype.onmousedown = function(e) {

  if (e.button == 0) {
    // left
    this._left_down = true;
  } else if (e.button == 2) {
    this._right_down = true;
  }

};

J.interactor.prototype.onmouseup = function(e) {

if (e.button == 0) {
  // left
  this._left_down = false;
} else if (e.button == 2) {
  // right
  this._right_down = false;
}

};

J.interactor.prototype.onmousewheel = function(e) {

  // if (e.wheelDeltaY < 0) {
  //   this._viewer._camera.zoom_out();
  // } else {
  //   this._viewer._camera.zoom_in();
  // }

  // this._viewer._camera.center();

  var canvas = this._viewer._canvas;
  var context = this._viewer._context;

  var pos = this._viewer.xy2uv(e.clientX, e.clientY);

  var wheel = e.wheelDelta/120;//n or -n
  //var zoom = Math.pow(1 + Math.abs(wheel)/2 , wheel > 0 ? 1 : -1);

  if (this._viewer._camera._view[0] + wheel < 0) return;
  if (this._viewer._camera._view[0] + wheel > 7) return;

  console.log( pos[0]  - (pos[0] - this._viewer._camera._view[6]) * this._viewer._camera._view[0]);
  return

  this._viewer._camera._view[0] += wheel;
  this._viewer._camera._view[4] += wheel;

  this._viewer._camera._view[6] -= pos[0] * this._viewer._camera._view[0];
  this._viewer._camera._view[7] += pos[1] * this._viewer._camera._view[0];

  // this._viewer._camera._view[6] = this._viewer._width/2 - this._viewer._camera._view[0]*512/2;
  // this._viewer._camera._view[7] = this._viewer._height/2 - this._viewer._camera._view[4]*512/2;


  // var originx = this._originx;
  // var originy = this._originy;
  // var scale = this._scale;

  //   var mousex = event.clientX - canvas.offsetLeft;
  //   var mousey = event.clientY - canvas.offsetTop;
  //   var wheel = event.wheelDelta/120;//n or -n

  //   console.log(mousex, mousey);

  //   //according to Chris comment
  //   //var zoom = Math.pow(1 + Math.abs(wheel)/2 , wheel > 0 ? 1 : -1);
  //   zoom = wheel
  //   console.log(zoom)
  //   // this._viewer._camera._view[6] = originx;
  //   // this._viewer._camera._view[7] = originy;

  //   this._viewer._camera._view[0] += zoom;
  //   this._viewer._camera._view[4] += zoom;

  //   this._viewer._camera._view[6] += -( mousex / scale + originx - mousex / ( scale * zoom ) );
  //   this._viewer._camera._view[7] += -( mousey / scale + originy - mousey / ( scale * zoom ) );    

    // context.translate(
    //     originx,
    //     originy
    // );
    // context.scale(zoom,zoom);
    // context.translate(
    //     -( mousex / scale + originx - mousex / ( scale * zoom ) ),
    //     -( mousey / scale + originy - mousey / ( scale * zoom ) )
    // );




    // this._originx = ( mousex / scale + originx - mousex / ( scale * zoom ) );
    // this._originy = ( mousey / scale + originy - mousey / ( scale * zoom ) );
    // this._scale *= zoom;

};


