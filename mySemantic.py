class Attribute:
    def __init__(self):
        self.identifier = ""  # 标识符
        self.type = ""  # 值类型 int word tmp_word
        self.place = None  # 存储位置
        self.quad = None  # 下一条四元式位置
        self.truelist = []  # true条件跳转目标
        self.falselist = []  # false条件跳转目标
        self.nextlist = []  # 顺序执行下一目标
        self.param_list = []  # 队列（用于函数参数）
        self.has_return = False  # 是否有一个一定能执行到的return

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
    def __init__(self, start_address = None):
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
            self.productions[production_id].non_terminal_symbol_id - len(self.terminal_symbols)
            ]

    def create_process(self, start_address = None):
        self.process_table.append(Process(start_address))

    def checkup_process(self, name):
        return any(p.name == name for p in self.process_table)

    def get_process(self, name):
        for p in self.process_table:
            if p.name == name:
                return p
        raise Exception(f"Process {name} not found")

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

    def emit(self, op, arg1, arg2, result):
        self.quaternion_table.append(Quaternion(op, arg1, arg2, result))

    def backpatch(self, nextlist, target):
        for index in nextlist:
            quad = list(self.quaternion_table[index])
            quad[3] = str(target)  # 修改 result 字段为目标地址
            self.quaternion_table[index] = tuple(quad)

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
            pass
        elif prod_str == "S":
            # S -> None
            self.emit("j", "-", "-", "-")
        elif prod_str == "P":
            # P → None
            new_proc = Process(start_address=len(self.quaternion_table) + self.start_address)  # 当前中间代码地址
            self.process_table.append(new_proc)

            attr = Attribute()
            attr.quad = len(self.quaternion_table)  # 保存函数入口四元式索引（用于后续设置 main）
            attr.place = len(self.process_table) - 1  # 在 process_table 中的下标
            item["attribute"] = attr
        elif prod_str == "FunctionHeader":
            # FunctionHeader -> fn identifier ( ParamList ) | fn identifier ( ParamList ) -> Type
            func_name = tmp_symbol_stack[1]["tree"]["content"]
            ret_type = tmp_symbol_stack[-1]["tree"]["content"] if to_strs[-2] == "->" else "void"
            # 一定要在函数定义前创建一个 Process 对象
            func_obj = self.process_table[-1]

            if self.checkup_process(func_name):
                self.raise_error("Error", loc, f"函数 {func_name} 重定义")
                return

            func_obj.name = func_name
            func_obj.return_type = ret_type

            attr = Attribute()
            attr.place = len(self.process_table) - 1  # 在 process_table 中的下标
            attr.type = ret_type
            item["attribute"] = attr
        elif prod_str == "FunctionDecl":
            # FunctionDecl -> P FunctionHeader Block
            func_attr = tmp_symbol_stack[1]["attribute"]
            proc_index = func_attr.place
            func_obj = self.process_table[proc_index]
            try:
                block_attr = tmp_symbol_stack[2]["attribute"]
                block_nextlist = block_attr.nextlist
                self.backpatch(block_nextlist, len(self.quaternion_table))  # 回填 block 结尾跳转地址
            except KeyError:
                pass
            if func_obj.return_type == "void":
                self.emit("ret", "-", "-", "-")

            # 设置程序入口
            if func_obj.name == "main":
                # 保证四元式表第一个为 j main
                self.quaternion_table[0].tar = str(func_obj.start_address)
        elif prod_str == "DeclOnly":
            # let VarDeclInner : Type ;
            var_name = tmp_symbol_stack[1]["attribute"].identifier
            var_type = tmp_symbol_stack[-2]["tree"]["content"] if len(to_strs) == 5 else "i32"

            if self.checkup_word(var_name):
                self.raise_error("Error", loc, f"变量{var_name}重定义")
            new_word = Word(name=var_name)
            new_word.type = var_type
            self.create_word(new_word)
        elif prod_str == "VarDeclInner":
            # VarDeclInner -> mut identifier
            var_name = tmp_symbol_stack[1]["tree"]["content"]
            attr = Attribute()
            attr.identifier = var_name  # 暂存参数名
            item["attribute"] = attr
        elif prod_str == "Param":
            # Param -> VarDeclInner : Type
            var_attr = tmp_symbol_stack[0]["attribute"]
            param_name = var_attr.identifier
            param_type = tmp_symbol_stack[-1]["tree"]["content"]

            word = Word(name=param_name)
            word.type = param_type
            self.create_word(word) # 在函数中的变量表中增加一项

            attr = Attribute()
            attr.word = word  # 暂存 Word 对象
            item["attribute"] = attr
        elif prod_str == "ParamList":
            # ParamList -> Param ParamListTail | None
            if to_strs[0] == "Param":
                param_word = tmp_symbol_stack[0]["attribute"].word
                param_list_tail = tmp_symbol_stack[1]["attribute"].param_list \
                    if "attribute" in tmp_symbol_stack[1] else []

                full_param_list = [param_word] + param_list_tail

                attr = Attribute()
                attr.param_list = full_param_list
                item["attribute"] = attr
                # 填入当前函数（Process）表
                self.process_table[-1].param = full_param_list
                self.process_table[-1].words_table.extend(full_param_list)
            elif to_strs[0] == "None":
                attr = Attribute()
                attr.param_list = []
                item["attribute"] = attr
        elif prod_str == "ParamListTail":
            # ParamListTail -> , Param ParamListTail | None
            if to_strs[0] == ",":
                param_word = tmp_symbol_stack[1]["attribute"].word
                param_list_tail = tmp_symbol_stack[2]["attribute"].param_list \
                    if "attribute" in tmp_symbol_stack[2] else []

                full_param_list = [param_word] + param_list_tail
                attr = Attribute()
                attr.param_list = full_param_list
                item["attribute"] = attr
            elif to_strs[0] == "None":
                attr = Attribute()
                attr.param_list = []
                item["attribute"] = attr
        elif prod_str == "M":
            # M -> None
            tmp = Attribute()
            tmp.quad = len(self.quaternion_table)
            item["attribute"] = tmp

    def analyse1(self, production_id, loc, item, tmp_symbol_stack):
        prod_str = self.get_str_by_production_id(production_id)
        to_ids = self.productions[production_id].to_ids
        to_strs = [self.get_str_by_id(i) for i in to_ids]

        if prod_str == "Program":
            # Program -> DeclList | None
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
            # FunctionDecl -> P FunctionHeader Block
            pass

        elif prod_str == "FunctionHeader":
            # FunctionHeader -> fn identifier ( ParamList )
            #                 | fn identifier ( ParamList ) -> Type
            # 开始函数定义
            if len(to_strs) == 5:
                # 没有返回值
                pass
            elif len(to_strs) == 7:
                # 有返回值类型
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
            pass

        elif prod_str == "VarDeclInner":
            # VarDeclInner -> mut identifier
            pass
        # ------------------------------------------------------------------------------------------
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
            # LoopStmt -> WhileStmt
            pass

        elif prod_str == "WhileStmt":
            # WhileStmt -> while Expr Block
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
        elif prod_str == "M":
            # M -> None
            pass
        elif prod_str == "N":
            # N -> None
            pass
        elif prod_str == "None":
            # None -> epsilon
            pass

    def getQuaternationTable(self):
        ret = [["地址", "四元式"]]
        for i, instr in enumerate(self.quaternion_table):
            ret.append([str(i + self.start_address), str(instr)])
        return ret
