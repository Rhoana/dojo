
function makeCube(size) {

  var points = [
    // Front face
    -size/2, -size/2,  size/2,
     size/2, -size/2,  size/2,
     size/2,  size/2,  size/2,
    -size/2,  size/2,  size/2,

    // Back face
    -size/2, -size/2, -size/2,
    -size/2,  size/2, -size/2,
     size/2,  size/2, -size/2,
     size/2, -size/2, -size/2,

    // Top face
    -size/2,  size/2, -size/2,
    -size/2,  size/2,  size/2,
     size/2,  size/2,  size/2,
     size/2,  size/2, -size/2,

    // Bottom face
    -size/2, -size/2, -size/2,
     size/2, -size/2, -size/2,
     size/2, -size/2,  size/2,
    -size/2, -size/2,  size/2,

    // Right face
     size/2, -size/2, -size/2,
     size/2,  size/2, -size/2,
     size/2,  size/2,  size/2,
     size/2, -size/2,  size/2,

    // Left face
    -size/2, -size/2, -size/2,
    -size/2, -size/2,  size/2,
    -size/2,  size/2,  size/2,
    -size/2,  size/2, -size/2,
    ];

  var normals = [

    0, 0, 1,
    0, 0, 1,
    0, 0, 1,
    0, 0, 1,
    
    0, 0, -1,
    0, 0, -1,
    0, 0, -1,
    0, 0, -1,

    0, 1, 0,
    0, 1, 0,
    0, 1, 0,
    0, 1, 0,
    
    0, -1, 0,
    0, -1, 0,
    0, -1, 0,
    0, -1, 0,

    1, 0, 0,
    1, 0, 0,
    1, 0, 0,
    1, 0, 0,
    
    -1, 0, 0,
    -1, 0, 0,
    -1, 0, 0,
    -1, 0, 0          
    
  ];

  var indices = [
      0, 1, 2,      0, 2, 3,    // Front face
      4, 5, 6,      4, 6, 7,    // Back face
      8, 9, 10,     8, 10, 11,  // Top face
      12, 13, 14,   12, 14, 15, // Bottom face
      16, 17, 18,   16, 18, 19, // Right face
      20, 21, 22,   20, 22, 23  // Left face
  ];

  // create geometry
  return new Geometry(new Float32Array(points), new Float32Array(normals), new Uint16Array(indices));

};

function makeSphere(radius, slices, stacks) {

  if (slices <= 1) throw new Error('Slices must be > 1');
  if (stacks < 2) throw new Error('Stacks must be >= 2');

  var radPerSlice = 2 * Math.PI / slices;
  var radPerStack = Math.PI / stacks;

  var longSin = new Array(slices+1);
  var longCos = new Array(slices+1);
  var latSin = new Array(stacks+1);
  var latCos = new Array(stacks+1);

  var points = [];
  var normals = [];
  var tex = [];
  var tangent = [];
  var binormal = [];

  var indices = [];

  for (var i = 0; i < slices + 1; ++i) {
    longSin[i] = Math.sin(radPerSlice * i);
    longCos[i] = Math.cos(radPerSlice * i);
  }
  for (i = 0; i < stacks + 1; ++i) {
    latSin[i] = Math.sin(radPerStack * i);
    latCos[i] = Math.cos(radPerStack * i);
  }

  for (i = 0; i < slices + 1; ++i) {
    for (var j = 0; j < stacks + 1; ++j) {

      var x = longCos[i] * latSin[j];
      var y = longSin[i] * latSin[j];
      var z = latCos[j];

      // add normal
      normals.push(x, y, z);

      // add point
      points.push(x * radius, y * radius, z * radius);

      // add texture coords
      tex.push(1.0/slices*i, 1.0/stacks*j);
      // tangents
      tangent.push(-longSin[i], longCos[i], 0);
      // binormals
      var b = vec3.cross(vec3.create(), [x, y, z], [-longSin[i], longCos[i], 0]);
      binormal.push(b[0], b[1], b[2]);

      // indices
      if (i < slices && j < stacks) {
        indices.push((stacks+1) * i + j);
        indices.push((stacks+1) * i + j + 1);
        indices.push((stacks+1) * (i + 1) + j + 1);
        indices.push((stacks+1) * i + j);
        indices.push((stacks+1) * (i + 1) + j + 1);
        indices.push((stacks+1) * (i + 1) + j);
      }

    }
  }

  // create geometry
  return new Geometry(new Float32Array(points), new Float32Array(normals), new Uint16Array(indices));
  
};
