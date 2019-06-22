// Copyright (c) 2012 Ecma International.  All rights reserved.
// Ecma International makes this code available under the terms and conditions set
// forth on http://hg.ecmascript.org/tests/test262/raw-file/tip/LICENSE (the
// "Use Terms").   Any redistribution of this code must retain the above
// copyright and this notice and otherwise comply with the Use Terms.

/*---
es5id: 15.2.3.8-2-a-4
description: Object.seal - 'P' is own accessor property
includes: [runTestCase.js]
---*/

function testcase() {
        var obj = {};

        Object.defineProperty(obj, "foo", {
            get: function () {
                return 10;
            },
            configurable: true
        });
        var preCheck = Object.isExtensible(obj);
        Object.seal(obj);

        delete obj.foo;
        return preCheck && obj.foo === 10;
    }
runTestCase(testcase);
