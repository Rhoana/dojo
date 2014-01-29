var J = J || {};

J.controller = function(viewer) {

  this._viewer = viewer;

  this._last_id = null;

  this._merge_table = null;

  this._origin = makeid() // TODO

};

J.controller.prototype.receive = function(data) {

  var input = JSON.parse(data.data);

  if (input.origin == this._origin) {
    // we are the sender
    return;
  }

  if (input.name == 'MERGETABLE') {

    // received new merge table
    this._viewer._controller.update_merge_table(input.value);

  }

};

J.controller.prototype.send = function(name, data) {

  var output = {};
  output.name = name;
  output.origin = this._origin;
  output.value = data;

  this._viewer._websocket.send(JSON.stringify(output));

};


///
///
///


J.controller.prototype.update_merge_table = function(data) {

  console.log('Received new merge table', data);

  this._merge_table = data;

  this._viewer.redraw();

};

J.controller.prototype.send_merge_table = function() {

  this.send('MERGETABLE', this._merge_table);

};

J.controller.prototype.merge = function(id) {

  if (!this._merge_table) {
    throw new Error('Merge-table does not exist.');
  }

  if (!this._last_id) {
    this._last_id = id;

    return;
  }

  console.log('Merging', this._last_id, id);

  if (!(id in this._merge_table)) {
    this._merge_table[id] = [];
  }

  this._merge_table[id].push(this._last_id);

  this._viewer.redraw();

  this.send_merge_table();

  this._last_id = null;

};
