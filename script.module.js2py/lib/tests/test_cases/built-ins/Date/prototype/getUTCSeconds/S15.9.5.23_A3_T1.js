// Copyright 2009 the Sputnik authors.  All rights reserved.
// This code is governed by the BSD license found in the LICENSE file.

/*---
info: >
    The Date.prototype.getUTCSeconds property "length" has { ReadOnly,
    DontDelete, DontEnum } attributes
es5id: 15.9.5.23_A3_T1
description: Checking ReadOnly attribute
---*/

x = Date.prototype.getUTCSeconds.length;
Date.prototype.getUTCSeconds.length = 1;
if (Date.prototype.getUTCSeconds.length !== x) {
  $ERROR('#1: The Date.prototype.getUTCSeconds.length has the attribute ReadOnly');
}
