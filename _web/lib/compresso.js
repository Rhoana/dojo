var COMPRESSO = COMPRESSO || {};



// size of various dimensions

var row_size = -1;
var sheet_size = -1;
var grid_size = -1;



function IndicesToIndex(ix, iy, iz)
{
  return iz * sheet_size + iy * row_size + ix;
};



COMPRESSO.UnionFindElement = function(label)
{
  this.label = label;
  this.parent = this;
  this.rank = 0;
};



COMPRESSO.UnionFindElement.prototype.Find = function()
{
  if (this.parent != this) this.parent = this.parent.Find();
  return this.parent;
};



COMPRESSO.UnionFindElement.prototype.Union = function(y)
{
  xroot = this.Find();
  yroot = y.Find();

  if (xroot == yroot) return;

  if (xroot.rank < yroot.rank) {
    xroot.parent = yroot;
  }
  else if (xroot.rank > yroot.rank) {
    yroot.parent = xroot;
  }
  else {
    yroot.parent = xroot;
    xroot.rank = xroot.rank + 1;
  }
};



COMPRESSO.DecodeBoundaries = function(boundary_data, values_high, values_low, zres, yres, xres, zstep, ystep, xstep)
{
  var nzblocks = Math.trunc(Math.ceil(zres / zstep) + 0.5);
  var nyblocks = Math.trunc(Math.ceil(yres / ystep) + 0.5);
  var nxblocks = Math.trunc(Math.ceil(xres / xstep) + 0.5);

  var nwindows = nzblocks * nyblocks * nxblocks;

  var window_count = new Uint32Array(nwindows);
  for (var iv = 0; iv < nwindows; ++iv)
    window_count[iv] = 0;
  var offset_count = new Uint32Array(64);
  for (var iv = 0; iv < 64; ++iv)
    offset_count[iv] = 0;

  // allocate memory for array
  var boundaries = new Uint8Array(grid_size);
  for (var iv = 0; iv < grid_size; ++iv) 
    boundaries[iv] = 0;
  // TODO is this initialization needed 

  // iterate over every voxel
  for (var iz = 0; iz < zres; ++iz) {
    for (var iy = 0; iy < yres; ++iy) {
      for (var ix = 0; ix < xres; ++ix) {
        var iv = IndicesToIndex(ix, iy, iz);

        // get the block for this voxel
        var zblock = parseInt(iz / zstep, 10);
        var yblock = parseInt(iy / ystep, 10);
        var xblock = parseInt(ix / xstep, 10);

        // find the offset
        var zoffset = iz % zstep;
        var yoffset = iy % ystep;
        var xoffset = ix % xstep;

        // get the block and offset
        var block = zblock * (nyblocks * nxblocks) + yblock * nxblocks + xblock;
        var offset = zoffset * (ystep * xstep) + yoffset * xstep + xoffset;

        // get the reduced block value
        var block_value = boundary_data[block];

        offset_count[offset]++;
        window_count[block]++;

        // see if the offset belongs to values_high or values_low
        if (offset >= 32) {
          // get the offset from values high
          offset = offset % 32;

          // get the value corresponding to this block
          value = values_high[block_value];
          if ((value >> offset) % 2) boundaries[iv] = 1;
        }
        else {
          // get the value corresponding to this block
          value = values_low[block_value];
          if ((value >> offset) % 2) boundaries[iv] = 1;
        }
      }
    }
  }

  return boundaries;
};



COMPRESSO.ConnectedComponents = function(boundaries, zres, yres, xres)
{
  components = new Float64Array(grid_size);
  for (var iv = 0; iv < grid_size; ++iv) {
    components[iv] = 0;
  } 

  // run connected components for each slice
  for (var iz = 0; iz < zres; ++iz) {

    // create a vector for union find elements
    union_find = new Array();

    // current label in connected component
    var curlab = 1;
    for (var iy = 0; iy < yres; ++iy) {
      for (var ix = 0; ix < xres; ++ix) {
        var iv = IndicesToIndex(ix, iy, iz);

        // continue if boundary
        if (boundaries[iv]) continue;

        // only consider the pixel directly to the north and west
        var north = IndicesToIndex(ix - 1, iy, iz);
        var west = IndicesToIndex(ix, iy - 1, iz);

        var neighbor_labels = [ 0, 0 ];
        if (ix > 0) neighbor_labels[0] = components[north];
        if (iy > 0) neighbor_labels[1] = components[west];

        // if the neighbors are boundary create new label
        if (!neighbor_labels[0] && !neighbor_labels[1]) {
          components[iv] = curlab;

          // add to union find structure
          union_find.push(new COMPRESSO.UnionFindElement(0));

          // update the next label
          curlab++;
        }
        // the two pixels have equal non-trivial values
        else if (neighbor_labels[0] == neighbor_labels[1])
          components[iv] = neighbor_labels[0];
        // neighbors have differing values
        else {
          if (!neighbor_labels[0]) components[iv] = neighbor_labels[1];
          else if (!neighbor_labels[1]) components[iv] = neighbor_labels[0];
          // neighbors have differing non-trivial values
          else {
            // take minimum value
            components[iv] = Math.min(neighbor_labels[0], neighbor_labels[1]);

            // set the equivalence relationship
            union_find[neighbor_labels[0] - 1].Union(union_find[neighbor_labels[1] - 1]);
          }
        }
      }
    }

    // reset the current label to 1
    curlab = 1;

    // create connected components (ordered)
    for (var iy = 0; iy < yres; ++iy) {
      for (var ix = 0; ix < xres; ++ix) {
        var iv = IndicesToIndex(ix, iy, iz);

        if (boundaries[iv]) continue;

        // get the parent for this component
        comp = union_find[components[iv] - 1].Find();
        if (!comp.label) {
          comp.label = curlab;
          curlab++;
        }

        components[iv] = comp.label;
      }
    }
  }

  return components;
};



COMPRESSO.IDReverseMapping = function(components, ids, zres, yres, xres)
{
  var decompressed_data = new Float64Array(grid_size);
  for (var iv = 0; iv < grid_size; ++iv)
    decompressed_data[iv] = 0;

  var ids_index = 0;
  for (var iz = 0; iz < zres; ++iz) {
    // create mapping (not memory efficient but fast!!)
    // number of components is guaranteed to be less than ids.length
    var mapping = new Float64Array(ids.length);
    for (var iv = 0; iv < ids.length; ++iv) 
      mapping[iv] = 0;

    for (var iy = 0; iy < yres; ++iy) {
      for (var ix = 0; ix < xres; ++ix) {
        var iv = IndicesToIndex(ix, iy, iz);

        if (!mapping[components[iv]]) {
          mapping[components[iv]] = ids[ids_index];
          ids_index++;
        }

        decompressed_data[iv] = mapping[components[iv]] - 1;
      }
    }
  }

  return decompressed_data;
};


COMPRESSO.DecodeIndeterminateLocations = function(boundaries, decompressed_data, locations, zres, yres, xres)
{
  var iv = 0;
  var index = 0;

  // go through all coordinates
  for (var iz = 0; iz < zres; ++iz) {
    for (var iy = 0; iy < yres; ++iy) {
      for (var ix = 0; ix < xres; ++ix, ++iv) {
        var north = IndicesToIndex(ix - 1, iy, iz);
        var west = IndicesToIndex(ix, iy - 1, iz);

        if (!boundaries[iv]) continue;
        else if (ix > 0 && !boundaries[north]) {
          decompressed_data[iv] = decompressed_data[north];
        }
        else if (iy > 0 && !boundaries[west]) {
          decompressed_data[iv] = decompressed_data[west];
        }
        else {
          var offset = locations[index];
          if (offset == 0) decompressed_data[iv] = decompressed_data[IndicesToIndex(ix - 1, iy, iz)];
          else if (offset == 1) decompressed_data[iv] = decompressed_data[IndicesToIndex(ix + 1, iy, iz)];
          else if (offset == 2) decompressed_data[iv] = decompressed_data[IndicesToIndex(ix, iy - 1, iz)];
          else if (offset == 3) decompressed_data[iv] = decompressed_data[IndicesToIndex(ix, iy + 1, iz)];
          else if (offset == 4) decompressed_data[iv] = decompressed_data[IndicesToIndex(ix, iy, iz - 1)];
          else if (offset == 5) decompressed_data[iv] = decompressed_data[IndicesToIndex(ix, iy, iz + 1)];
          else decompressed_data[iv] = offset - 6;

          index++;
        }
      }
    }
  }  

  return decompressed_data;
};


// Decompression algorithm takes in an Uint32Array
COMPRESSO.Decompress = function(bytes) {
  // create arrays for the header
  const header_size = 10;
  var header_low = new Uint32Array(header_size);
  var header_high = new Uint32Array(header_size);

  // allocate the lower and higher header bits
  for (var iv = 0; iv < header_size; ++iv) {
    header_low[iv] = bytes[2 * iv];
    header_high[iv] = bytes[2 * iv + 1];
  }

  // get the resolution of the original image
  var zres = header_high[0] * Math.pow(2, 32) + header_low[0];
  var yres = header_high[1] * Math.pow(2, 32) + header_low[1];
  var xres = header_high[2] * Math.pow(2, 32) + header_low[2];

  // get the sizes of each array
  var ids_size = header_high[3] * Math.pow(2, 32) + header_low[3];
  var values_size = header_high[4] * Math.pow(2, 32) + header_low[4];
  var byte_size = header_high[5] * Math.pow(2, 32) + header_low[5];
  var locations_size = header_high[6] * Math.pow(2, 32) + header_low[6];

  // get the step size
  var zstep = header_high[7] * Math.pow(2, 32) + header_low[7];
  var ystep = header_high[8] * Math.pow(2, 32) + header_low[8];
  var xstep = header_high[9] * Math.pow(2, 32) + header_low[9];

  // determine the number of blocks in the z, y, and x dimensions
  var nzblocks = Math.trunc(Math.ceil(zres / zstep) + 0.5);
  var nyblocks = Math.trunc(Math.ceil(yres / ystep) + 0.5);
  var nxblocks = Math.trunc(Math.ceil(xres / xstep) + 0.5);

  // get the number of windows in the volume
  var nwindows = nzblocks * nyblocks * nxblocks;

  // update the dimension sizes
  row_size = xres;
  sheet_size = xres * yres;
  grid_size = xres * yres * zres;

  // remove the header from the buffer
  bytes = bytes.slice(2 * header_size);

  // get all of the ids for the connected components
  var ids = new Float64Array(ids_size);
  for (var iv = 0; iv < ids_size; ++iv) {
    ids[iv] = bytes[2 * iv + 1] * Math.pow(2, 32) + bytes[2 * iv];
  }
  // update the bytes array
  bytes = bytes.slice(2 * ids_size);

  // get the non encoded window values
  var values_low = new Uint32Array(values_size);
  var values_high = new Uint32Array(values_size);
  for (var iv = 0; iv < values_size; ++iv) {
    values_low[iv] = bytes[2 * iv];
    values_high[iv] = bytes[2 * iv + 1];
  }
  // update the bytes array
  bytes = bytes.slice(2 * values_size);

  // get all of the locations where indeterminate values occur
  var locations = new Float64Array(locations_size);
  for (var iv = 0; iv < locations_size; ++iv) {
    locations[iv] = bytes[2 * iv + 1] * Math.pow(2, 32) + bytes[2 * iv];
  }
  // update the bytes array
  bytes = bytes.slice(2 * locations_size);

  // get all of the boundary data
  // TODO handle boundary data of various sizes 
  var boundary_data = bytes;

  var zero_counter = 0;
  for (var iv = 0; iv < boundary_data.length; ++iv) {
    if (boundary_data[iv] == 0) zero_counter++;
  }

  // decode the boundaries
  boundaries = COMPRESSO.DecodeBoundaries(boundary_data, values_high, values_low, zres, yres, xres, zstep, ystep, xstep);

  // get the components from a connected components algorithm
  components = COMPRESSO.ConnectedComponents(boundaries, zres, yres, xres);

  // map the components to ids
  decompressed_data = COMPRESSO.IDReverseMapping(components, ids, zres, yres, xres);

  // decode the last pieces of information
  decompressed_data = COMPRESSO.DecodeIndeterminateLocations(boundaries, decompressed_data, locations, zres, yres, xres);

  // return the dimensions and the linear array of data
  return {zres : zres, yres : yres, xres : xres, decompressed_data : decompressed_data};
};
