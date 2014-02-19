// UTILITY FUNCTIONS

function pad(i,n) {
  var v = i + "";
  while (v.length < n) {
    v = "0" + v
  }
  return v;
}


function updateFrustFovY() {

  if (gl.viewportWidth >= gl.viewportHeight) {
    frustFovY = frustMinFov;
  } else {
    var RAD_PER_DEG = 0.5 * Math.PI/180;
    frustFovY = Math.atan2(Math.sin(frustMinFov * RAD_PER_DEG) * gl.viewportHeight / gl.viewportWidth, Math.cos(frustMinFov * RAD_PER_DEG)) / RAD_PER_DEG;
  }
};

function makeProjectionMatrix() {

  projectionMatrix = mat4.create();
  // we need to specify the frustFovY in radians
  mat4.perspective(projectionMatrix, frustFovY * Math.PI/180, gl.viewportWidth / gl.viewportHeight, frustNear, frustFar);

  // flip the Z axis according to CS175 convention
  projectionMatrix[10] *= -1;
  projectionMatrix[15] = 1;
  
  return projectionMatrix;

};

function sendProjectionMatrix(mat) {

  gl.uniformMatrix4fv(shaderStates[currentShader].h_uProjMatrix, false, mat);

};

function normalMatrix(mat) {

  var invm = mat4.invert(mat4.create(), mat);
  invm[12] = invm[13] = invm[14] = 0;

  return mat4.transpose(mat4.create(), invm);

};

function sendModelViewMatrix(mvm, nmvm) {

  gl.uniformMatrix4fv(shaderStates[currentShader].h_uModelViewMatrix, false, mvm);
  gl.uniformMatrix4fv(shaderStates[currentShader].h_uNormalMatrix, false, nmvm);

};



//
// frame related functions
//

function doMtoOwrtA(m, o, a) {

  var a_m = a.multiply(m);

  var a_inv = inv(a);

  var a_m_a_inv = a_m.multiply(a_inv);

  return a_m_a_inv.multiply(o);

};

function makeMixedFrame(t, l) {

  var trbt = transFact(t);
  var lrbt = linFact(l);
  return trbt.multiply(lrbt);

};




//
// shader utility functions
//
function readAndCompileShader(id) {

  var shaderScript = document.getElementById(id);

  if (!shaderScript) {
    return null;
  }

  var str = "";
  var k = shaderScript.firstChild;
  while (k) {
    if (k.nodeType == 3) {
      str += k.textContent;
    }
    k = k.nextSibling;
  }

  var shader;
  if (shaderScript.type == "x-shader/x-fragment") {
    shader = gl.createShader(gl.FRAGMENT_SHADER);
  } else if (shaderScript.type == "x-shader/x-vertex") {
    shader = gl.createShader(gl.VERTEX_SHADER);
  } else {
    return null;
  }
  
  gl.shaderSource(shader, str);
  gl.compileShader(shader);

  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    alert(gl.getShaderInfoLog(shader));
    return null;
  }

  return shader;

};

function linkShaders(vs_id, fs_id) {

  var fragmentShader = readAndCompileShader(fs_id);
  var vertexShader = readAndCompileShader(vs_id);

  var shaderProgram = gl.createProgram();
  gl.attachShader(shaderProgram, vertexShader);
  gl.attachShader(shaderProgram, fragmentShader);
  gl.linkProgram(shaderProgram);

  if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
      alert("Could not initialise shaders");

      console.log(gl.getShaderInfoLog(fragmentShader));
      console.log(gl.getShaderInfoLog(vertexShader));
      console.log(gl.getProgramInfoLog(shaderProgram));
  }

  return shaderProgram;

};



function initGLState() {

  // grab webgl context from canvas
  var canvas = document.getElementById('c');
  canvas.width = window.document.body.clientWidth;
  canvas.height = window.document.body.clientHeight;
  gl = canvas.getContext('experimental-webgl') || canvas.getContext('webgl');

  if (!gl) {
    alert('WebGL not supported.');
    return;
  }

  // store the canvas size
  gl.viewportWidth = canvas.width;
  gl.viewportHeight = canvas.height;

  gl.viewport(0, 0, gl.viewportWidth, gl.viewportHeight);
  gl.clearColor(0,0,0,0);//128./255., 200./255., 255./255., 1.);
  gl.clearDepth(0);
  gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
  gl.pixelStorei(gl.PACK_ALIGNMENT, 1);
  //gl.cullFace(gl.BACK);
  //gl.enable(gl.CULL_FACE);


  // enable transparency
  gl.blendEquation(gl.FUNC_ADD);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.enable(gl.BLEND);

  gl.enable(gl.DEPTH_TEST);
  gl.depthFunc(gl.GREATER);

  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

};

function initShaders() {

  // read, compile and link two shader programs
  shaderStates.push(new ShaderState('vs1', 'fs1'));
  //shaderStates.push(new ShaderState('vertexshader1', 'fragmentshader2'));

  // activate the first shader by default
  currentShader = 0;

};

function initGeometry() {

  initTextures(function() {

    initSlices();

    setTimeout(function() {

      document.getElementById('pb').style.display = 'none';

      updateFrustFovY();

      // start the drawStuff loop
      window.requestAnimationFrame(drawStuff);        


    },1000);

  });

};

function parseArgs() {

  // from http://stackoverflow.com/a/7826782/1183453
  var args = document.location.search.substring(1).split('&');
  argsParsed = {};
  for (var i=0; i < args.length; i++)
  {
      arg = unescape(args[i]);

      if (arg.length == 0) {
        continue;
      }

      if (arg.indexOf('=') == -1)
      {
          argsParsed[arg.replace(new RegExp('/$'),'').trim()] = true;
      }
      else
      {
          kvp = arg.split('=');
          argsParsed[kvp[0].trim()] = kvp[1].replace(new RegExp('/$'),'').trim();
      }
  }

  _ID_ = argsParsed['id'];

  if (typeof _ID_ == 'undefined') {

    // for demo purposes, make sure an ID is set
    _ID_ = 3036;

  }

};
