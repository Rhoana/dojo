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

function connect(){  
    try{  
  
    var socket;  
    var host = "ws://"+window.location.hostname+":31337/";  
    var socket = new WebSocket(host);  
  
        console.log('<p class="event">Socket Status: '+socket.readyState);  
  
        socket.onopen = function(){  
             console.log('<p class="event">Socket Status: '+socket.readyState+' (open)');  
        }  
  
        socket.onmessage = function(msg){  
             console.log('<p class="message">Received: '+msg.data);  
        }  
  
        socket.onclose = function(){  
             console.log('<p class="event">Socket Status: '+socket.readyState+' (Closed)');  
        }             
  
    } catch(exception){  
         console.log('<p>Error'+exception);  
    }  
}  

// from http://stackoverflow.com/a/5624139/1183453
function rgbToHex(r, g, b) {
  return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}