/**
 *
 */
RigTForm = function(t, r) {

  this.t_ = vec3.create(0,0,0); // translation component
  this.r_ = quat.create(); // rotation component

  if (typeof t != 'undefined' && t) {

    this.t_ = t;

  }

  if (typeof r != 'undefined' && r) {

    this.r_ = r;

  }
};


RigTForm.prototype.getTranslation = function() {

  return this.t_;

};

RigTForm.prototype.getRotation = function() {

  return this.r_;

};

RigTForm.prototype.setTranslation = function(t) {

  this.t_ = t;

  return this;

};

RigTForm.prototype.setRotation = function(r) {

  this.r_ = r;

  return this;

};

/**
 *
 */
RigTForm.prototype.multiplyByVec4 = function(c) {

  // A.r * c + vec4(A.t, 0)
  var Ar_c = vec4.transformQuat(vec4.create(), this.r_, c);
  var At = [this.t_[0], this.t_[1], this.t_[2], 0];

  return vec4.add(vec4.create(), Ar_c, At);

};

/**
 * Multiply by another RigTForm
 */
RigTForm.prototype.multiply = function(a) {

  // t: t1 + r1t2 
  // r: r1r2

  var t = vec3.create();
  vec3.add(t, this.t_, vec3.transformQuat(t, a.getTranslation(), this.r_));

  var r = quat.create();
  quat.multiply(r, this.r_, a.getRotation());

  return new RigTForm(t, r);

};

var inv = function(tform) {
  // t: -r^-1t 
  // r: r^-1

  var t = vec3.create();
  vec3.transformQuat(t, tform.getTranslation(), quat.invert(quat.create(), tform.getRotation()));
  vec3.scale(t,t,-1);

  var r = quat.create();
  quat.invert(r,tform.getRotation());

  return new RigTForm(t, r);

};

var transFact = function(tform) {

  return new RigTForm(tform.getTranslation(), null);

};

var linFact = function(tform) {

  return new RigTForm(null, tform.getRotation());

};

var rigTFormToMatrix = function(tform) {

  var T = mat4.translate(mat4.create(), mat4.create(), tform.getTranslation());
  var R = mat4.fromQuat(mat4.create(), tform.getRotation());

  return mat4.multiply(mat4.create(), T, R);

};