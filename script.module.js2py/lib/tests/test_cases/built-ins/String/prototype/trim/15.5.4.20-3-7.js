// Copyright (c) 2012 Ecma International.  All rights reserved.
// Ecma International makes this code available under the terms and conditions set
// forth on http://hg.ecmascript.org/tests/test262/raw-file/tip/LICENSE (the
// "Use Terms").   Any redistribution of this code must retain the above
// copyright and this notice and otherwise comply with the Use Terms.

/*---
es5id: 15.5.4.20-3-7
description: >
    String.prototype.trim - 'S' is a string that union of
    LineTerminator and WhiteSpace in the middle
includes: [runTestCase.js]
---*/

function testcase() {
        var lineTerminatorsStr = "\u000A\u000D\u2028\u2029";
        var whiteSpacesStr = "\u0009\u000A\u000B\u000C\u000D\u0020\u00A0\u1680\u180E\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF";
        var str = "ab" + whiteSpacesStr + lineTerminatorsStr + "cd";

        return (str.trim() === str);
    }
runTestCase(testcase);
