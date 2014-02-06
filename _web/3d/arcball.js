
CS175_EPS = 1e-8;

// Return the screen space projection in terms of pixels of a 3d point
// given in eye-frame coordinates.
//
// Ideally you should never call this for a point behind the Z=0 plane,
// sinch such a point wouldn't be visible.
//
// But if you do pass in a point behind Z=0 plane, we'll just
// print a warning, and return the center of the screen.
function getScreenSpaceCoord(p, projection, frustNear, frustFovY, screenWidth, screenHeight) {

  if (p[2] > -CS175_EPS) {
    console.log('WARNING: getScreenSpaceCoord of a point near or behind Z=0 plane. Returning screen-center instead.');
    return vec2.fromValues((screenWidth-1)/2.0, (screenHeight-1)/2.0);
  }

  var q = vec4.transformMat4(vec4.create(), vec4.fromValues(p[0], p[1], p[2], 1), projection);
  var clipCoord = vec3.scale(vec3.create(), vec3.fromValues(q[0], q[1], q[2]), 1/q[3]);

  return vec2.fromValues(clipCoord[0] * screenWidth / 2.0 + (screenWidth - 1)/2.0,
                         clipCoord[1] * screenHeight / 2.0 + (screenHeight - 1)/2.0);

}

// Return the scale between 1 unit in screen pixels and 1 unit in the eye-frame
// (or world-frame, since we always use rigid transformations to represent one
// frame with resepec to another frame)
//
// Ideally you should never call this using a z behind the Z=0 plane,
// sinch such a point wouldn't be visible.
//
// But if you do pass in a point behind Z=0 plane, we'll just
// print a warning, and return 1
function getScreenToEyeScale(z, frustFovY, screenHeight) {

  if (z > -CS175_EPS) {
    console.log('WARNING: getScreenToEyeScale on z near or behind Z=0 plane. Returning 1 instead.');
    return 1;
  }

  return -(z * Math.tan(frustFovY * Math.PI/360.0)) * 2 / screenHeight;

}
