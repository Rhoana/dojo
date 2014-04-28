var IMG = null;
var SEG = null;
var DS = null;

function init() {

  DS = new J.datasocket(on_message);

  // Add drop handling
  document.getElementById("body").addEventListener("dragenter", noop_handler, false);
  document.getElementById("body").addEventListener("dragleave", noop_handler, false);
  document.getElementById("body").addEventListener("dragover", noop_handler, false);  
  document.getElementById("image_dropzone").addEventListener("drop", on_drop_img, false);
  document.getElementById("segmentation_dropzone").addEventListener("drop", on_drop_seg, false);

};

function noop_handler(evt) {

  evt.stopPropagation();
  evt.preventDefault();
};

function on_drop_img(evt) {

  // Consume the event.
  noop_handler(evt);

  // Get the dropped files.
  var files = evt.dataTransfer.files;

  // If anything is wrong with the dropped files, exit.
  if (typeof files == "undefined" || files.length == 0) {
    return;
  }

  var list = document.getElementById('img_files');
  for (var i=0; i<files.length;i++) {

    list.innerHTML += files[i].name+'<br>'

  }

  IMG = files;

  upload();

};

function on_drop_seg(evt) {

  // Consume the event.
  noop_handler(evt);

  // Get the dropped files.
  var files = evt.dataTransfer.files;

  // If anything is wrong with the dropped files, exit.
  if (typeof files == "undefined" || files.length == 0) {
    return;
  }

 var list = document.getElementById('seg_files');
  for (var i=0; i<files.length;i++) {

    list.innerHTML += files[i].name+'<br>'

  }

  SEG = files;

  upload();

};

function upload() {

  if (!IMG || !SEG) return;

  console.log('uploading...');

  var images = new FormData();
  var segs = new FormData();

  for (var i=0; i<IMG.length;i++) {
    images.append('file',IMG[i]);
  }  
 
  for (var i=0; i<SEG.length;i++) {
    segs.append('file',SEG[i]);
  }  

  var setup = document.getElementById('setup');
  var loading = document.getElementById('loading');
  loading.style.display = 'block';
  setup.style.display = 'none';

  DS.send(IMG[0]);

};

function on_message(m) {
  console.log(m);
}


