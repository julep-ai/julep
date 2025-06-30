export declare const enum CharCode {
    Null = 0,
    MaxAscii = 127,
    ByteOrderMark = 65279,
    LineFeed = 10,
    CarriageReturn = 13,
    Space = 32,
    Tab = 9,
    VerticalTab = 11,
    FormFeed = 12,
    NextLine = 133,// not considered a line break
    LeftToRightMark = 8206,
    RightToLeftMark = 8207,
    LineSeparator = 8232,
    ParagraphSeparator = 8233,
    _0 = 48,
    _1 = 49,
    _2 = 50,
    _3 = 51,
    _4 = 52,
    _5 = 53,
    _6 = 54,
    _7 = 55,
    _8 = 56,
    _9 = 57,
    a = 97,
    b = 98,
    c = 99,
    d = 100,
    e = 101,
    f = 102,
    g = 103,
    h = 104,
    i = 105,
    j = 106,
    k = 107,
    l = 108,
    m = 109,
    n = 110,
    o = 111,
    p = 112,
    q = 113,
    r = 114,
    s = 115,
    t = 116,
    u = 117,
    v = 118,
    w = 119,
    x = 120,
    y = 121,
    z = 122,
    A = 65,
    B = 66,
    C = 67,
    D = 68,
    E = 69,
    F = 70,
    G = 71,
    H = 72,
    I = 73,
    J = 74,
    K = 75,
    L = 76,
    M = 77,
    N = 78,
    O = 79,
    P = 80,
    Q = 81,
    R = 82,
    S = 83,
    T = 84,
    U = 85,
    V = 86,
    W = 87,
    X = 88,
    Y = 89,
    Z = 90,
    _ = 95,
    $ = 36,
    Ampersand = 38,
    Asterisk = 42,
    At = 64,
    Backslash = 92,
    Backtick = 96,
    Bar = 124,
    Caret = 94,
    CloseBrace = 125,
    CloseBracket = 93,
    CloseParen = 41,
    Colon = 58,
    Comma = 44,
    Dot = 46,
    DoubleQuote = 34,
    Equals = 61,
    Exclamation = 33,
    GreaterThan = 62,
    Hash = 35,
    LessThan = 60,
    Minus = 45,
    OpenBrace = 123,
    OpenBracket = 91,
    OpenParen = 40,
    Percent = 37,
    Plus = 43,
    Question = 63,
    Semicolon = 59,
    SingleQuote = 39,
    Slash = 47,
    Tilde = 126
}
export declare function utf16CodeUnits(codePoint: number): 1 | 2;
export declare function isHighSurrogate(ch: number): boolean;
export declare function isLowSurrogate(ch: number): boolean;
export declare function isLineBreak(ch: number): ch is CharCode.LineFeed | CharCode.CarriageReturn;
export declare function isAsciiWhiteSpaceSingleLine(ch: number): ch is CharCode.Space | CharCode.Tab | CharCode.VerticalTab | CharCode.FormFeed;
export declare function isNonAsciiWhiteSpaceSingleLine(ch: number): ch is CharCode.NextLine | CharCode.LeftToRightMark | CharCode.RightToLeftMark | CharCode.LineSeparator | CharCode.ParagraphSeparator;
export declare function isWhiteSpace(ch: number): boolean;
export declare function isWhiteSpaceSingleLine(ch: number): boolean;
export declare function trim(str: string): string;
export declare function isDigit(ch: number): boolean;
export declare function isHexDigit(ch: number): boolean;
export declare function isBinaryDigit(ch: number): ch is CharCode._0 | CharCode._1;
export declare function isLowercaseAsciiLetter(ch: number): boolean;
export declare function isAsciiIdentifierStart(ch: number): boolean;
export declare function isAsciiIdentifierContinue(ch: number): boolean;
export declare function isIdentifierStart(codePoint: number): boolean;
export declare function isIdentifierContinue(codePoint: number): boolean;
export declare function isNonAsciiIdentifierCharacter(codePoint: number): boolean;
export declare function codePointBefore(text: string, pos: number): {
    char: number | undefined;
    size: number;
};
//# sourceMappingURL=charcode.d.ts.map