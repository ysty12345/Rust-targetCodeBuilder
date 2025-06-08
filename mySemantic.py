class Attribute:
    def __init__(self):
        self.identifier = ""  # 标识符
        self.type = ""  # 值类型 int word tmp_word
        self.place = None  # 存储位置或临时变量名字
        self.quad = None  # 下一条四元式位置
        self.truelist = []  # true条件跳转目标
        self.falselist = []  # false条件跳转目标
        self.nextlist = []  # 顺序执行下一目标
        self.param_list = []  # 形参列表
        self.arg_list = []  # 实参列表
        self.has_return = False  # 是否有一个一定能执行到的return
        self.op = ""  # 操作符（如加减乘除等）

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
        self.tmp_words_table = []
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

    def new_temp(self):
        """
        生成临时变量并加入当前函数的 tmp_words_table
        """
        tmp_words_table = self.process_table[-1].tmp_words_table
        temp_count = len(tmp_words_table)
        while True:
            temp_name = f"__T{temp_count}"
            temp_count += 1
            # 检查当前函数作用域中的局部变量是否已有此名
            if not self.checkup_word(temp_name):
                break

        temp_word = Word(name=temp_name)
        temp_word.id = len(tmp_words_table)
        temp_word.type = "i32"

        # 加入临时变量表（当前函数）
        self.process_table[-1].tmp_words_table.append(temp_word)
        return temp_name

    def emit(self, op, arg1, arg2, result):
        self.quaternion_table.append(Quaternion(op, arg1, arg2, result))

    def backpatch(self, nextlist, target):
        for index in nextlist:
            quaternion = self.quaternion_table[index]
            # 修改 result 字段为目标地址
            quaternion.tar = self.start_address + target

    def raise_error(self, type, loc, msg):
        if type == "Error":
            self.error_occur = True
        self.error_msg.append(f"{type} at ({loc['row']},{loc['col']}): {msg}")

    def analyse(self, production_id, loc, item, tmp_symbol_stack):
        prod_str = self.get_str_by_production_id(production_id)
        to_ids = self.productions[production_id].to_ids
        to_strs = [self.get_str_by_id(i) for i in to_ids]
        # print(prod_str)
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

            if func_obj.return_type == "void" and not func_attr.has_return:
                self.emit("ret", "-", "-", "-")
            elif func_obj.return_type != "void" and not func_attr.has_return:
                self.raise_error("Error", loc, f"函数 {func_obj.name} 没有返回值")
                return

            # 设置程序入口
            if func_obj.name == "main":
                # 保证四元式表第一个为 j main
                self.quaternion_table[0].tar = str(func_obj.start_address)
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

        elif prod_str == "Lvalue":
            # Lvalue -> identifier
            var_name = tmp_symbol_stack[0]["tree"]["content"]
            attr = Attribute()
            attr.identifier = var_name
            if not self.checkup_word(var_name):
                self.raise_error("Error", loc, f"变量{var_name}未定义")
                return
            item["attribute"] = attr
        elif prod_str == "Expr":
            # Expr -> Expr CmpOp AddExpr | AddExpr
            if len(to_strs) == 1:
                item["attribute"] = tmp_symbol_stack[0]["attribute"]
            else:
                lhs = tmp_symbol_stack[0]["attribute"]
                op = tmp_symbol_stack[1]["attribute"].op
                rhs = tmp_symbol_stack[2]["attribute"]

                temp_var = self.new_temp()
                self.emit(op, lhs.place, rhs.place, temp_var)

                attr = Attribute()
                attr.place = temp_var
                item["attribute"] = attr
        elif prod_str == "AddExpr":
            # AddExpr -> AddExpr AddOp Term | Term
            if len(to_strs) == 1:
                item["attribute"] = tmp_symbol_stack[0]["attribute"]
            else:
                lhs = tmp_symbol_stack[0]["attribute"]
                op = tmp_symbol_stack[1]["attribute"].op
                rhs = tmp_symbol_stack[2]["attribute"]

                temp_var = self.new_temp()
                self.emit(op, lhs.place, rhs.place, temp_var)

                attr = Attribute()
                attr.place = temp_var
                item["attribute"] = attr
        elif prod_str == "Term":
            # Term -> Term MulOp Factor | Factor
            if len(to_strs) == 1:
                item["attribute"] = tmp_symbol_stack[0]["attribute"]
            else:
                lhs = tmp_symbol_stack[0]["attribute"]
                op = tmp_symbol_stack[1]["attribute"].op
                rhs = tmp_symbol_stack[2]["attribute"]

                temp_var = self.new_temp()
                self.emit(op, lhs.place, rhs.place, temp_var)

                attr = Attribute()
                attr.place = temp_var
                item["attribute"] = attr
        elif prod_str == "Factor":
            # Factor -> Element
            item["attribute"] = tmp_symbol_stack[0]["attribute"]
        elif prod_str == "Element":
            # Element -> integer_constant | identifier | ( Expr ) | identifier ( ArgList )
            if len(to_strs) == 1:
                content = tmp_symbol_stack[0]["tree"]["content"]
                attr = Attribute()
                attr.place = content  # 常量或变量名
                item["attribute"] = attr
            elif to_strs[0] == "(":
                # ( Expr )
                item["attribute"] = tmp_symbol_stack[1]["attribute"]
            else:
                # identifier ( ArgList )
                func_name = tmp_symbol_stack[0]["tree"]["content"]
                args_attr = tmp_symbol_stack[2]["attribute"]
                arg_places = args_attr.arg_list

                for i, arg in enumerate(arg_places):
                    self.emit("arg", "-", "-", arg)

                ret_temp = self.new_temp()
                self.emit("call", func_name, len(arg_places), ret_temp)

                attr = Attribute()
                attr.place = ret_temp
                item["attribute"] = attr
        elif prod_str == "ArgList":
            # ArgList -> Expr ArgListTail | None
            if to_strs[0] == "Expr":
                head = tmp_symbol_stack[0]["attribute"].place
                tail = tmp_symbol_stack[1]["attribute"].arg_list if "attribute" in tmp_symbol_stack[1] else []
                attr = Attribute()
                attr.arg_list = [head] + tail
                item["attribute"] = attr
            else:
                attr = Attribute()
                attr.arg_list = []
                item["attribute"] = attr
        elif prod_str == "ArgListTail":
            # ArgListTail -> , Expr ArgListTail | None
            if to_strs[0] == ",":
                head = tmp_symbol_stack[1]["attribute"].place
                tail = tmp_symbol_stack[2]["attribute"].arg_list if "attribute" in tmp_symbol_stack[2] else []
                attr = Attribute()
                attr.arg_list = [head] + tail
                item["attribute"] = attr
            else:
                attr = Attribute()
                attr.arg_list = []
                item["attribute"] = attr
        elif prod_str == "CmpOp":
            # CmpOp -> < | <= | > | >= | == | !=
            attr = Attribute()
            attr.op = tmp_symbol_stack[0]["tree"]["content"]
            item["attribute"] = attr
        elif prod_str == "AddOp":
            # AddOp -> + | -
            attr = Attribute()
            attr.op = tmp_symbol_stack[0]["tree"]["content"]
            item["attribute"] = attr
        elif prod_str == "MulOp":
            # MulOp -> * | /
            attr = Attribute()
            attr.op = tmp_symbol_stack[0]["tree"]["content"]
            item["attribute"] = attr

        elif prod_str == "DeclOnly":
            # DeclOnly -> let VarDeclInner : Type ;
            var_name = tmp_symbol_stack[1]["attribute"].identifier
            var_type = tmp_symbol_stack[-2]["tree"]["content"] if len(to_strs) == 5 else "i32"

            if self.checkup_word(var_name):
                self.raise_error("Error", loc, f"变量{var_name}重定义")
                return

            new_word = Word(name=var_name)
            new_word.type = var_type
            self.create_word(new_word)
            attr = Attribute()
            item["attribute"] = attr
        elif prod_str == "DeclAssign":
            # DeclAssign -> let VarDeclInner : Type = Expr ; | let VarDeclInner = Expr ;
            var_name = tmp_symbol_stack[1]["attribute"].identifier
            var_type = tmp_symbol_stack[3]["tree"]["content"] if to_strs[3] == ":" else "i32"
            expr_attr = tmp_symbol_stack[-2]["attribute"]  # 最后一个Expr

            if self.checkup_word(var_name):
                self.raise_error("Error", loc, f"变量{var_name}重定义")
                return

            new_word = Word(name=var_name)
            new_word.type = var_type
            self.create_word(new_word)

            self.emit("=", expr_attr.place, "-", var_name)
            attr = Attribute()
            item["attribute"] = attr
        elif prod_str == "AssignStmt":
            # AssignStmt -> Lvalue = Expr ;
            var_name = tmp_symbol_stack[0]["attribute"].identifier
            expr_attr = tmp_symbol_stack[2]["attribute"]

            if not self.checkup_word(var_name):
                self.raise_error("Error", loc, f"变量{var_name}未定义")
                return

            self.emit("=", expr_attr.place, "-", var_name)
            attr = Attribute()
            item["attribute"] = attr
        elif prod_str == "ExprStmt":
            # ExprStmt -> Expr ;
            # 表达式语句，结果可能没有用，但仍要求值，故直接继承属性但不生成额外语义
            item["attribute"] = tmp_symbol_stack[0]["attribute"]
        elif prod_str == "ReturnStmt":
            # ReturnStmt -> return ; | return Expr ;
            if len(to_strs) == 3:
                # return Expr ;
                expr_attr = tmp_symbol_stack[1]["attribute"]
                self.emit("ret", "-", "-", expr_attr.place)
            else:
                # return ;
                self.emit("ret", "-", "-", "-")
            attr = Attribute()
            attr.has_return = True  # 标记函数有返回值
            item["attribute"] = attr

        elif prod_str == "Block":
            # Block -> { StmtList }
            item["attribute"] = tmp_symbol_stack[1]["attribute"]
        elif prod_str == "StmtList":
            # StmtList -> Stmt M StmtList | None
            if to_strs[0] == "Stmt":
                # StmtList -> Stmt M StmtList
                stmt_attr = tmp_symbol_stack[0]["attribute"]
                m_attr = tmp_symbol_stack[1]["attribute"]
                rest_attr = tmp_symbol_stack[2]["attribute"]
                # 将 stmt 的 nextlist 回填到 M 的四元式位置
                self.backpatch(stmt_attr.nextlist, m_attr.quad)
                attr = Attribute()
                attr.has_return = stmt_attr.has_return or rest_attr.has_return
                item["attribute"] = attr
            else:
                item["attribute"] = Attribute()
        elif prod_str == "Stmt":
            # Stmt -> LoopStmt | IfStmt | DeclOnly | DeclAssign | AssignStmt | ExprStmt | ReturnStmt | ;
            if to_strs[0] == ";":
                # Stmt -> ;
                attr = Attribute()
                item["attribute"] = attr
            else:
                item["attribute"] = tmp_symbol_stack[0]["attribute"]
        elif prod_str == "BoolExpr":
            # BoolExpr -> Expr
            # 直接继承 Expr 的属性
            attr = tmp_symbol_stack[0]["attribute"]
            attr.truelist = [len(self.quaternion_table)]  # 条件为真跳转目标
            attr.falselist = [len(self.quaternion_table) + 1]  # 条件为假跳转目标
            self.emit("jnz", attr.place, "-", "-")  # 占位跳转
            self.emit("j", "-", "-", "-")
            item["attribute"] = attr
        elif prod_str == "LoopStmt":
            # LoopStmt -> WhileStmt
            item["attribute"] = tmp_symbol_stack[0]["attribute"]
        elif prod_str == "WhileStmt":
            # WhileStmt -> while M BoolExpr M Block
            m1 = tmp_symbol_stack[1]["attribute"]
            expr_attr = tmp_symbol_stack[2]["attribute"]
            m2 = tmp_symbol_stack[3]["attribute"]
            block_attr = tmp_symbol_stack[4]["attribute"]

            self.backpatch(expr_attr.truelist, m2.quad)  # 条件为真跳转到循环体
            self.backpatch(block_attr.nextlist, m1.quad)  # 循环体结束后跳转到判断条件
            self.emit("j", "-", "-", m1.quad + self.start_address)  # 回到判断条件
            attr = Attribute()
            attr.nextlist = expr_attr.falselist
            attr.has_return = block_attr.has_return
            item["attribute"] = attr

        elif prod_str == "IfStmt":
            # IfStmt -> if BoolExpr M Block | if BoolExpr M Block N M ElsePart
            if len(to_strs) == 4:
                # IfStmt -> if BoolExprExpr M Block
                expr_attr = tmp_symbol_stack[1]["attribute"]
                m_attr = tmp_symbol_stack[2]["attribute"]
                block_attr = tmp_symbol_stack[3]["attribute"]

                self.backpatch(expr_attr.truelist, m_attr.quad)
                attr = Attribute()
                attr.nextlist = expr_attr.falselist + block_attr.nextlist
                attr.has_return = block_attr.has_return
                item["attribute"] = attr
            else:
                # IfStmt -> if BoolExpr M Block N M ElsePart
                expr_attr = tmp_symbol_stack[1]["attribute"]
                m1 = tmp_symbol_stack[2]["attribute"]
                block_attr = tmp_symbol_stack[3]["attribute"]
                n = tmp_symbol_stack[4]["attribute"]
                m2 = tmp_symbol_stack[5]["attribute"]
                else_attr = tmp_symbol_stack[6]["attribute"]

                self.backpatch(expr_attr.truelist, m1.quad)
                self.backpatch(expr_attr.falselist, m2.quad)

                attr = Attribute()
                attr.nextlist = block_attr.nextlist + n.nextlist + else_attr.nextlist
                attr.has_return = block_attr.has_return and else_attr.has_return
                item["attribute"] = attr
        elif prod_str == "ElsePart":
            # ElsePart -> else IfStmt | else Block
            item["attribute"] = tmp_symbol_stack[1]["attribute"]
        elif prod_str == "M":
            # M -> None
            tmp = Attribute()
            tmp.quad = len(self.quaternion_table)
            item["attribute"] = tmp
        elif prod_str == "N":
            # N -> None
            attr = Attribute()
            # 当前 then_block 后的位置，即将插入跳转 over-else 的 j 指令
            attr.nextlist = [len(self.quaternion_table)]
            # 插入 j _ _ _ 占位跳转，暂时不知道目标
            self.emit("j", "-", "-", "-")
            item["attribute"] = attr


    def getQuaternationTable(self):
        ret = [["地址", "四元式"]]
        for i, instr in enumerate(self.quaternion_table):
            ret.append([str(i + self.start_address), str(instr)])
        return ret
