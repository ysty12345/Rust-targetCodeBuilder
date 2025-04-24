from enum import Enum


class tokenType(Enum):
    # 关键字
    KW_I32 = "kw_i32"
    KW_LET = "kw_let"
    KW_IF = "kw_if"
    KW_ELSE = "kw_else"
    KW_WHILE = "kw_while"
    KW_RETURN = "kw_return"
    KW_MUT = "kw_mut"
    KW_FN = "kw_fn"
    KW_FOR = "kw_for"
    KW_IN = "kw_in"
    KW_LOOP = "kw_loop"
    KW_BREAK = "kw_break"
    KW_CONTINUE = "kw_continue"
    UNKNOWN = "unknown"

    IDENTIFIER = "identifier"
    INTEGER_CONSTANT = "integer_constant"
    FLOATING_POINT_CONSTANT = "floating_point_constant"

    # 符号
    EQUAL = "equal"
    PLUS = "plus"
    MINUS = "minus"
    STAR = "star"
    SLASH = "slash"
    PERCENT = "percent"
    PLUS_EQUAL = "plusequal"
    MINUS_EQUAL = "minusequal"
    STAR_EQUAL = "starequal"
    SLASH_EQUAL = "slashequal"
    PERCENT_EQUAL = "percentequal"

    EQUAL_EQUAL = "equalequal"
    GREATER = "greater"
    GREATER_EQUAL = "greaterequal"
    LESS = "less"
    LESS_EQUAL = "lessequal"
    EXCLAMATION_EQUAL = "exclaimequal"

    GREATER_GREATER = "greatergreater"
    GREATER_GREATER_EQUAL = "greatergreaterequal"
    LESS_LESS = "lessless"
    LESS_LESS_EQUAL = "lesslessequal"

    L_PAREN = "l_paren"
    R_PAREN = "r_paren"
    L_BRACKET = "l_bracket"
    R_BRACKET = "r_bracket"
    L_BRACE = "l_brace"
    R_BRACE = "r_brace"

    COMMA = "comma"
    COLON = "colon"
    SEMI = "semi"

    ARROW = "->"
    DOT = "dot"
    DOTDOT = "dotdot"

    S_COMMENT = "s_comment"
    LM_COMMENT = "lm_comment"
    RM_COMMENT = "rm_comment"

    EOF = "eof"

tokenKeywords = {
    "i32": tokenType.KW_I32,
    "let": tokenType.KW_LET,
    "if": tokenType.KW_IF,
    "else": tokenType.KW_ELSE,
    "while": tokenType.KW_WHILE,
    "return": tokenType.KW_RETURN,
    "mut": tokenType.KW_MUT,
    "fn": tokenType.KW_FN,
    "for": tokenType.KW_FOR,
    "in": tokenType.KW_IN,
    "loop": tokenType.KW_LOOP,
    "break": tokenType.KW_BREAK,
    "continue": tokenType.KW_CONTINUE,
}

tokenSymbols = {
    "=": tokenType.EQUAL,
    "+": tokenType.PLUS,
    "-": tokenType.MINUS,
    "*": tokenType.STAR,
    "/": tokenType.SLASH,
    "%": tokenType.PERCENT,
    "+=": tokenType.PLUS_EQUAL,
    "-=": tokenType.MINUS_EQUAL,
    "*=": tokenType.STAR_EQUAL,
    "/=": tokenType.SLASH_EQUAL,
    "%=": tokenType.PERCENT_EQUAL,

    "==": tokenType.EQUAL_EQUAL,
    ">": tokenType.GREATER,
    ">=": tokenType.GREATER_EQUAL,
    "<": tokenType.LESS,
    "<=": tokenType.LESS_EQUAL,
    "!=": tokenType.EXCLAMATION_EQUAL,

    ">>": tokenType.GREATER_GREATER,
    ">>=": tokenType.GREATER_GREATER_EQUAL,
    "<<": tokenType.LESS_LESS,
    "<<=": tokenType.LESS_LESS_EQUAL,

    "(": tokenType.L_PAREN,
    ")": tokenType.R_PAREN,
    "[": tokenType.L_BRACKET,
    "]": tokenType.R_BRACKET,
    "{": tokenType.L_BRACE,
    "}": tokenType.R_BRACE,

    ",": tokenType.COMMA,
    ":": tokenType.COLON,
    ";": tokenType.SEMI,

    "->": tokenType.ARROW,
    ".": tokenType.DOT,
    "..": tokenType.DOTDOT,

    "//": tokenType.S_COMMENT,
    "/*": tokenType.LM_COMMENT,
    "*/": tokenType.RM_COMMENT,

    "#": tokenType.EOF,

}

def tokenType_to_terminal(tokenType: tokenType) -> str:
    for key, value in tokenKeywords.items():
        if value == tokenType:
            return key
    for key, value in tokenSymbols.items():
        if value == tokenType:
            return key
    # 如identifier、numeric_constant并非固定的terminal，直接返回对应的字符串名
    return tokenType.value
