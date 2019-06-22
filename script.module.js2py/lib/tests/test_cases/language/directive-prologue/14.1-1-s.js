// Copyright (c) 2012 Ecma International.  All rights reserved.
// Ecma International makes this code available under the terms and conditions set
// forth on http://hg.ecmascript.org/tests/test262/raw-file/tip/LICENSE (the
// "Use Terms").   Any redistribution of this code must retain the above
// copyright and this notice and otherwise comply with the Use Terms.

/*---
es5id: 14.1-1-s
description: "'use strict' directive - correct usage"
flags: [noStrict]
includes: [runTestCase.js]
---*/

function testcase() {

  function foo()
  {
    'use strict';
     return(this === undefined);
  }

  return foo.call(undefined);
 }
runTestCase(testcase);
