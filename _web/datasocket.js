var J = J || {};

J.datasocket = function(callback) {

  this._callback = callback;

  this._socket = null;

  this.connect();

};

J.datasocket.prototype.connect = function() {

  try {

    var host = "ws://"+window.location.hostname+":"+window.location.port+"/ds";  
    this._socket = new WebSocket(host);
    this._socket.binaryType = 'arraybuffer';

    this._socket.onopen = this.on_open.bind(this);
    this._socket.onmessage = this.on_message.bind(this);
    this._socket.onclose = this.on_close.bind(this);

  } catch (e) {
    console.log('Websocket connection failed.');
  }

};

J.datasocket.prototype.on_open = function() {

  console.log('Established websocket connection.');

};

J.datasocket.prototype.on_message = function(m) {

  // console.log('Received', m);
  this._callback(m);

};

J.datasocket.prototype.send = function(m) {

  this._socket.send(m);

};

J.datasocket.prototype.on_close = function() {

  console.log('Websocket connection dropped.');

};
