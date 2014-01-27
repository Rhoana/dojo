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
    var host = "ws://monster.krash.net:1337/dojo/";  
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