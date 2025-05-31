class Attribute:
    def __init__(self):
        self.type = ""          # 值类型 int float word tmp_word
        self.place = None       # 存储位置
        self.quad = None        # 下一条四元式位置
        self.truelist = []      # true条件跳转目标
        self.falselist = []     # false条件跳转目标
        self.nextlist = []      # 顺序执行下一目标
        self.queue = []         # 队列（用于函数参数）
        self.has_return = False # 是否有一个一定能执行到的return

    def __repr__(self):
        return f"<Attribute Object (Type:{self.type}, Place:{self.place}, Truelist:{self.truelist}, Falselist:{self.falselist}, Nextlist:{self.nextlist}, Quad:{self.quad})>"


class Word:
    def __init__(self, id=0, name=""):
        self.id = id
        self.name = name
        self.type = ""

    def __repr__(self):
        return f"<Word Object (ID:{self.id}, Name:{self.name}, Type:{self.type})>"


class Quaternion:
    def __init__(self, op="", src1="", src2="", tar=""):
        self.op = op
        self.src1 = src1
        self.src2 = src2
        self.tar = tar

    def __repr__(self):
        return f"({self.op}, {self.src1}, {self.src2}, {self.tar})"


class Process:
    def __init__(self, start_address):
        self.name = ""
        self.return_type = ""
        self.actual_returns = []
        self.start_address = start_address
        self.words_table = [Word()]
        self.param = []

    def __repr__(self):
        return f"<Process Object (Name:{self.name}, Return Type:{self.return_type}, Start Address:{self.start_address}, Params:{self.param})>"


class Semantic:
    def __init__(
        self, productions, non_terminal_symbols, terminal_symbols, start_address=100
    ):
        self.words_table = [Word()]  # 全局变量
        self.tmp_words_table = []  # 所有的临时变量
        self.process_table = []
        self.quaternion_table = []
        self.productions = productions
        self.non_terminal_symbols = non_terminal_symbols
        self.terminal_symbols = terminal_symbols
        self.epsilon_id = len(terminal_symbols)
        self.start_address = start_address
        self.error_occur = False
        self.error_msg = []

    def get_str_by_id(self, cnt: int) -> str:
        if 0 <= cnt < self.epsilon_id:
            return self.terminal_symbols[cnt]
        elif cnt < self.epsilon_id + len(self.non_terminal_symbols):
            return self.non_terminal_symbols[cnt - self.epsilon_id]
        else:
            assert Exception("Invalid terminal cnt!")

    def get_str_by_production_id(self, production_id: int) -> str:
        return self.non_terminal_symbols[
            self.productions[production_id].from_id - len(self.terminal_symbols)
            ]

    def create_process(self, start_address):
        self.process_table.append(Process(start_address))

    def checkup_word(self, word_name):
        words_table = self.process_table[-1].words_table
        # 在作用域内找到
        for i, word in enumerate(words_table):
            if word.name == word_name:
                return i
        # 全局变量
        for i, word in enumerate(self.words_table):
            if word.name == word_name:
                return -i
        return 0

    def checkup_word_type(self, word_name):
        words_table = self.process_table[-1].words_table
        word_type = next(
            (word.type for word in words_table if word.name == word_name), None
        )
        # 低层屏蔽高层，再去全局变量找
        if word_type is None:
            word_type = next(
                (word.type for word in self.words_table if word.name == word_name), None
            )
        return word_type

    def get_word(self, place):
        if place > 0:
            return self.process_table[-1].words_table[place]
        else:
            return self.words_table[-place]

    def create_word(self, word):
        words_table = self.process_table[-1].words_table
        word.id = len(words_table)
        words_table.append(word)

    def raise_error(self, type, loc, msg):
        if type == "Error":
            self.error_occur = True
        self.error_msg.append(f"{type} at ({loc['row']},{loc['col']}): {msg}")

    def analyse(self, production_id, loc, item, tmp_symbol_stack):
        prod_str = self.get_str_by_production_id(production_id)
        to_ids = self.productions[production_id].to_ids
        to_strs = [self.get_str_by_id(i) for i in to_ids]

        if prod_str == "Program":
            # Program -> DeclList | None
            if to_strs[0] == "DeclList":
                # Program包含声明列表，递归处理
                pass
            elif to_strs[0] == "None":
                # 空程序，不产生中间代码
                pass

        elif prod_str == "DeclList":
            # DeclList -> Decl DeclList | Decl
            if len(to_strs) == 2:
                # Decl DeclList
                pass
            else:
                # 单个 Decl
                pass

        elif prod_str == "Decl":
            # Decl -> FunctionDecl
            pass

        elif prod_str == "FunctionDecl":
            # FunctionDecl -> FunctionHeader Block
            pass

        elif prod_str == "FunctionHeader":
            # FunctionHeader -> fn identifier ( ParamList )
            #                 | fn identifier ( ParamList ) -> Type
            func_name = tmp_symbol_stack[1].value  # 假设 identifier 存入栈时保留了名称
            # 开始函数定义
            if len(to_strs) == 5:
                # 没有返回值
                pass
            elif len(to_strs) == 7:
                # 有返回值类型
                return_type = tmp_symbol_stack[6].value
                pass

        elif prod_str == "ParamList":
            # ParamList -> Param ParamListTail | None
            if to_strs[0] == "Param":
                pass
            elif to_strs[0] == "None":
                pass

        elif prod_str == "ParamListTail":
            # ParamListTail -> , Param ParamListTail | None
            if to_strs[0] == ",":
                pass
            elif to_strs[0] == "None":
                pass

        elif prod_str == "Param":
            # Param -> VarDeclInner : Type
            var_name = tmp_symbol_stack[0].value
            var_type = tmp_symbol_stack[2].value
            pass

        elif prod_str == "VarDeclInner":
            # VarDeclInner -> mut identifier
            var_name = tmp_symbol_stack[1].value
            pass

        elif prod_str == "Block":
            # Block -> { StmtList }
            pass

        elif prod_str == "StmtList":
            # StmtList -> Stmt StmtList | None
            if len(to_strs) == 2:
                pass
            else:
                pass

        elif prod_str == "Stmt":
            # Stmt -> LoopStmt | IfStmt | DeclOnly | DeclAssign | AssignStmt | ExprStmt | ReturnStmt | BreakStmt | ContinueStmt | ;
            pass

        elif prod_str == "LoopStmt":
            # LoopStmt -> WhileStmt | ForStmt | LoopBlock
            pass

        elif prod_str == "WhileStmt":
            # WhileStmt -> while Expr Block
            pass

        elif prod_str == "ForStmt":
            # ForStmt -> for VarDeclInner in Iterable Block
            pass

        elif prod_str == "Iterable":
            # Iterable -> Expr .. Expr
            pass

        elif prod_str == "LoopBlock":
            # LoopBlock -> loop Block
            pass

        elif prod_str == "IfStmt":
            # IfStmt -> if Expr Block ElsePart
            pass

        elif prod_str == "ElsePart":
            # ElsePart -> else IfStmt | else Block | None
            pass

        elif prod_str == "DeclOnly":
            # DeclOnly -> let VarDeclInner : Type ; | let VarDeclInner ;
            pass

        elif prod_str == "DeclAssign":
            # DeclAssign -> let VarDeclInner : Type = Expr ; | let VarDeclInner = Expr ;
            pass

        elif prod_str == "AssignStmt":
            # AssignStmt -> Lvalue = Expr ;
            pass

        elif prod_str == "ExprStmt":
            # ExprStmt -> Expr ;
            pass

        elif prod_str == "ReturnStmt":
            # ReturnStmt -> return ; | return Expr ;
            pass

        elif prod_str == "BreakStmt":
            # BreakStmt -> break ;
            pass

        elif prod_str == "ContinueStmt":
            # ContinueStmt -> continue ;
            pass

        elif prod_str == "Lvalue":
            # Lvalue -> identifier
            pass

        elif prod_str == "Expr":
            # Expr -> Expr CmpOp AddExpr | AddExpr
            pass

        elif prod_str == "AddExpr":
            # AddExpr -> AddExpr AddOp Term | Term
            pass

        elif prod_str == "Term":
            # Term -> Term MulOp Factor | Factor
            pass

        elif prod_str == "Factor":
            # Factor -> Element
            pass

        elif prod_str == "Element":
            # Element -> integer_constant | identifier | ( Expr ) | identifier ( ArgList )
            pass

        elif prod_str == "ArgList":
            # ArgList -> Expr ArgListTail | None
            pass

        elif prod_str == "ArgListTail":
            # ArgListTail -> , Expr ArgListTail | None
            pass

        elif prod_str == "CmpOp":
            # CmpOp -> < | <= | > | >= | == | !=
            pass

        elif prod_str == "AddOp":
            # AddOp -> + | -
            pass

        elif prod_str == "MulOp":
            # MulOp -> * | /
            pass

        elif prod_str == "Type":
            # Type -> i32
            pass

        elif prod_str == "None":
            # None -> epsilon
            pass

    def getQuaternationTable(self):
        ret = [["地址", "四元式"]]
        for i, instr in enumerate(self.quaternion_table):
            ret.append([str(i + self.start_address), str(instr)])
        return ret
