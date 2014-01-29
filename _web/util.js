// UTILITY FUNCTIONS

function pad(i,n) {
  var v = i + "";
  while (v.length < n) {
    v = "0" + v
  }
  return v;
}

// from http://jsperf.com/signs/3
function sign (x) {
  return typeof x === 'number' ? x ? x < 0 ? -1 : 1 : x === x ? 0 : NaN : NaN;
}

// from http://stackoverflow.com/a/5624139/1183453
function rgbToHex(r, g, b) {
  return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

function makeid()
{
  var text = "";
  var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

  for( var i=0; i < 5; i++ )
      text += possible.charAt(Math.floor(Math.random() * possible.length));

  return text;
}
