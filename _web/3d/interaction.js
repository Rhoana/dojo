
function initCallbacks() {

  window.document.onmousemove = motion;
  window.document.onmousedown = window.document.onmouseup = mouse;
  window.document.onkeypress = keyboard;

  // remove the oncontextmenu
  window.document.oncontextmenu = function() { return false; }

  // monitor window resizing
  window.onresize = reshape;

};

/**
 * Gets called on window resize.
 */
function reshape() {

  var canvas = document.getElementById('c');
  canvas.width = window.document.body.clientWidth;
  canvas.height = window.document.body.clientHeight;

  // update the canvas size
  gl.viewportWidth = canvas.width;
  gl.viewportHeight = canvas.height;

  arcballScreenRadius = 0.25*Math.min(gl.viewportWidth, gl.viewportHeight);

  // .. and the viewport
  gl.viewport(0, 0, gl.viewportWidth, gl.viewportHeight);

  updateFrustFovY();

};

/**
 * Gets called on mouse movement.
 */
function motion(e) {

  var dx = e.clientX - mouseClickX;
  var dy = e.clientY - mouseClickY;
  
  var A = skyRbt;

  switch (currentMode) {
    case 0:

      A = skyRbt;

    break;
    case 1:

      A = makeMixedFrame(new RigTForm(), skyRbt);

    break;
  }


  var m = new RigTForm();
  if (mouseLClickButton && !mouseRClickButton) {

    // rotation
    if(!showArcball) {

      if (currentMode == 0 && currentManipulation == 'SKY') {
        dx *= -1;
        dy *= -1;
      }

      // multiply (we need to pass radii)
      var q_x = quat.rotateX(quat.create(), quat.create(), dy * Math.PI/180);
      var q_y = quat.rotateY(quat.create(), quat.create(), dx * Math.PI/180);
      var q = quat.multiply(quat.create(), q_x, q_y);

      m.setRotation(q);

    } else {

      var sphCtr = invEyeRbt.multiply(sphereRbt).getTranslation();

      var ctr =  getScreenSpaceCoord(sphCtr, projectionMatrix, frustNear, frustFovY, gl.viewportWidth, gl.viewportHeight);

      var s1 = vec2.fromValues(e.clientX, gl.viewportHeight-e.clientY);
      var sqz = arcballScreenRadius*arcballScreenRadius - vec2.squaredDistance(s1,ctr);
      if (sqz < 0) sqz = 0;
      var v1 = [s1[0]-ctr[0], s1[1]-ctr[1], Math.sqrt(sqz)];
      vec3.normalize(v1,v1);

      var s2 = vec2.fromValues(mouseClickX, gl.viewportHeight-mouseClickY);
      sqz = arcballScreenRadius*arcballScreenRadius - vec2.squaredDistance(s2,ctr);
      if (sqz < 0) sqz = 0;
      var v2 = [s2[0]-ctr[0], s2[1]-ctr[1], Math.sqrt(sqz)];
      vec3.normalize(v2,v2);

      var q = quat.multiply(quat.create(), [v2[0], v2[1], v2[2], 0], [-v1[0], -v1[1], -v1[2], 0]);
      m = new RigTForm(null, q);

    }

  } else if (mouseRClickButton && !mouseLClickButton) {

    // invert translation if translating the world camera
    if ((currentMode == 1 && currentManipulation == 'SKY') || (currentView == currentManipulation && currentManipulation != 'SKY')) {
      dx *= -0.1;
      dy *= -0.1;
    }

    var scale = 0.01;
    if (showArcball) {
      scale = arcballScale;
    }

    // translation x,y
    m.setTranslation(vec3.scale(vec3.create(), [dx, -dy, 0], scale));

  } else if (mouseMClickButton || (mouseLClickButton && mouseRClickButton)) {

    if ((currentMode == 0 && currentView == currentManipulation && currentView == 'SKY') || (currentView != currentManipulation)) {
      // if not sky-world mode, invert z
      dy *= -1;
    }

    var scale = 0.01;
    if (showArcball) {
      scale = arcballScale;
    }

    // translation z
    m.setTranslation(vec3.scale(vec3.create(), [0, 0, -dy], scale));
  }

  switch(currentManipulation) {

    case 'SKY':
      skyRbt = doMtoOwrtA( m, skyRbt, A );
      sphereRbt = new RigTForm();
      break;

  }

  // show arcball if in world-sky manipulation mode
  // of if manipulating a cube without viewing from the cube
  // we also check in drawStuff if any mouse button is actually down
  showArcball = (currentView == 'SKY' && currentMode == 1) || 
                (currentManipulation != 'SKY' && currentView != currentManipulation);

  mouseClickX = e.clientX;
  mouseClickY = e.clientY;

};

/**
 * Gets called on mouse clicks.
 */
function mouse(e) {

  mouseClickX = e.clientX;
  mouseClickY = e.clientY;

  if (e.button == 0)
    mouseLClickButton = (e.type == "mousedown");
  if (e.button == 2)
    mouseRClickButton = (e.type == "mousedown");

  mouseMClickButton = (e.button == 1 && e.type == "mousedown") || (mouseLClickButton && mouseRClickButton);

  mouseClickDown = mouseLClickButton || mouseRClickButton || mouseMClickButton;

};

/**
 * Gets called on keypress.
 */
function keyboard(e) {
  
  switch(e.charCode) {

    // space
    case 32:
      //switch between modes
      MODE ^= 1;

      if (MODE == 0) {
        OPACITY = 1.0;
      } else {
        OPACITY = 0.3;
      }
      console.log('switched between modes');
      break;

    case 43:

      // increase opacity
      if (OPACITY <= 1.0) {
        console.log('increase opacity');
        OPACITY += 0.1;
      }
      break;

    case 45:
      // decrease opacity
      if (OPACITY > 0) {
        console.log('decrease opacity');
        OPACITY -= 0.1;
      }
      break;

    // m
    case 109:
      if (currentView == 'SKY' && currentManipulation == 'SKY') {
        currentMode ^= 1;
        console.log('switched between sky frame modes');
      } else {
        console.log('We can only switch the sky frame mode when manipulating the SKY and viewing from it');
      }
      break;


    // o:
    case 111:
      switch(currentManipulation) {
        case 'SKY':
          currentManipulation = 'CUBE1';
          break;
        case 'CUBE1':
          currentManipulation = 'CUBE2';
          break;
        case 'CUBE2':
          currentManipulation = 'SKY';
          break;
      }
      console.log('Now manipulating', currentManipulation);
    break;

  }

};

function progressbar() {
  return new JS_BRAMUS.jsProgressBar(document.getElementById('pb'), 0, {
        showText:false,
        barImage : Array('images/bramus/percentImage_back4.png',
            'images/bramus/percentImage_back3.png',
            'images/bramus/percentImage_back2.png',
            'images/bramus/percentImage_back1.png')
      });      
};
