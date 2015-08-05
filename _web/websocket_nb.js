var J = J || {};

J.websocketNB = function(viewer) {

  this._viewer = viewer;

  this._socket = null;

  this._port = 3003;

  this.connect();

};

J.websocketNB.prototype.connect = function() {

  try {

    var host = "ws://"+window.location.hostname+":"+this._port;  
    this._socket = new WebSocket(host);

    this._socket.onopen = this.on_open.bind(this);
    this._socket.onmessage = this.on_message.bind(this);
    this._socket.onclose = this.on_close.bind(this);

  } catch (e) {
    console.log('Websocket connection failed.');
  }

};

J.websocketNB.prototype.on_open = function() {

  console.log('Established websocket connection to Neuroblocks.');  

};

J.websocketNB.prototype.on_message = function(m) {

  // console.log('Received', m);
  // this._viewer._controller.receive(m);

  var ids = JSON.parse(m.data);

  DOJO.viewer._controller.reset_fixed_3d_labels();
  DOJO.viewer._controller.reset_3d_labels();
  DOJO.viewer._controller._use_3d_labels = true;



  for (var i=0; i<ids.length; i++) {

    var id = ids[i];
    DOJO.viewer._controller.add_fixed_3d_label(id);
    DOJO.viewer._controller.add_3d_label(id);

    console.log(id);

  }

};

J.websocketNB.prototype.send = function(m) {

  this._socket.send(m);

};

J.websocketNB.prototype.on_close = function() {

  console.log('Websocket connection dropped.');

};
