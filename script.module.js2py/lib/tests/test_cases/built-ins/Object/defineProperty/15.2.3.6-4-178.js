// Copyright (c) 2012 Ecma International.  All rights reserved.
// Ecma International makes this code available under the terms and conditions set
// forth on http://hg.ecmascript.org/tests/test262/raw-file/tip/LICENSE (the
// "Use Terms").   Any redistribution of this code must retain the above
// copyright and this notice and otherwise comply with the Use Terms.

/*---
es5id: 15.2.3.6-4-178
description: >
    Object.defineProperty - 'O' is an Array, 'name' is the length
    property of 'O', the [[Value]] field of 'desc' is less than value
    of  the length property, test the configurable large index named
    property of 'O' is deleted (15.4.5.1 step 3.l.ii)
includes: [runTestCase.js]
---*/

function testcase() {

        var arrObj = [0, 1];

        Object.defineProperty(arrObj, "length", {
            value: 1
        });

        return !arrObj.hasOwnProperty("1");
    }
runTestCase(testcase);
