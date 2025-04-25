import json
import re
from tokenType import tokenType_to_terminal, tokenType

ACTION_ACC = 0
ACTION_S = 1
ACTION_R = 2
ActionType = ["acc", "s", "r"]


class Production:
    def __init__(self):
        self.id = 0
        self.non_terminal_symbol_id = 0
        self.to_ids = []

    def __lt__(self, other):
        return self.id < other.id


class LR1Item:
    def __init__(self, production_id, dot_pos, terminal_id):
        # 表示该项目使用的产生式编号（索引到某个产生式列表中）
        self.production_id = production_id
        # 表示点（•）在产生式右侧的位置
        # 例如：A → α • β，dot_pos 就是 α 的长度
        self.dot_pos = dot_pos
        # 表示该 LR(1) 项目的展望符（lookahead terminal）的符号ID
        self.terminal_id = terminal_id

    def __lt__(self, other):
        # 定义“小于”操作符，用于集合排序、去重等操作
        # 先按产生式编号，再按点位置，最后按展望符比较
        return (self.production_id, self.dot_pos, self.terminal_id) < (
            other.production_id,
            other.dot_pos,
            other.terminal_id,
        )

    def __eq__(self, other):
        # 定义相等操作符，用于判断两个项目是否完全相同
        return (self.production_id, self.dot_pos, self.terminal_id) == (
            other.production_id,
            other.dot_pos,
            other.terminal_id,
        )


class Closure:
    def __init__(self):
        # 项目集的编号（可用于标识状态）
        self.id = 0
        # 项目集，包含若干 LR(1) 项（LR1Item 实例）
        self.items = []

    def __lt__(self, other):
        # 定义“小于”操作符，根据 id 比较
        # 主要用于集合排序或组织状态编号
        return self.id < other.id

    def __eq__(self, other):
        # 判断两个项目集是否相等（即状态是否等价）
        # 通过将各自的项目排序后逐项比较实现
        t1 = sorted(self.items)
        t2 = sorted(other.items)

        # 若项目数量不同，直接返回不相等
        if len(t1) != len(t2):
            return False

        # 逐项比较每个 LR1Item 是否完全一致
        for i in range(len(t1)):
            if t1[i] != t2[i]:
                return False

        return True


class Parser:
    terminal_symbols = [
        "i32",
        "let",
        "if",
        "else",
        "while",
        "return",
        "mut",
        "fn",
        "for",
        "in",
        "loop",
        "break",
        "continue",

        "identifier",
        "integer_constant",
        "floating_point_constant",

        "=",
        "+",
        "-",
        "*",
        "/",
        "%",
        "+=",
        "-=",
        "*=",
        "/=",
        "%=",

        ">>",
        ">>=",
        "<<",
        "<<=",

        "==",
        ">",
        ">=",
        "<",
        "<=",
        "!=",

        "(",
        ")",
        "[",
        "]",
        "{",
        "}",

        ",",
        ":",
        ";",

        "->",
        ".",
        "..",
        "#",
    ]

    def __init__(self, filename="mytest.cfg"):
        self.epsilon_id = len(self.terminal_symbols)
        self.non_terminal_symbols = ["epsilon"]
        self.firsts = []
        self.productions = []
        self.closures = []
        self.gos = []
        self.goto_table = []
        self.action_table = []
        self.lr1_analysis_table = []

        self.read_productions(filename=filename)
        self.find_firsts()
        self.find_gos()
        self.find_gotos_and_actions()

    def get_id_by_str(self, symbol: str) -> int:
        # 根据symbol获取对应的id，先是终结符，再是非终结符
        try:
            return self.terminal_symbols.index(symbol)
        except BaseException:
            try:
                return self.non_terminal_symbols.index(symbol) + self.epsilon_id
            except BaseException:
                assert Exception("Invalid symbol!")

    def get_str_by_id(self, cnt: int) -> str:
        if 0 <= cnt < self.epsilon_id:
            return self.terminal_symbols[cnt]
        elif cnt < self.epsilon_id + len(self.non_terminal_symbols):
            return self.non_terminal_symbols[cnt - self.epsilon_id]
        else:
            assert Exception("Invalid terminal cnt!")

    def read_productions(self, filename="production.cfg"):
        # 读取产生式配置文件
        """
        从产生式配置文件中读取产生式规则。
        参数：
        - filename: 产生式配置文件的路径，默认为"production.cfg"。
        返回：
        - success: 如果成功读取配置文件并处理产生式规则，则返回True；如果文件不存在，返回False。
        """
        try:
            with open(filename, "r") as fin:  # 打开配置文件进行读取
                for line in fin.readlines():  # 逐行读取文件内容
                    line = line.split("#")[0].strip()  # 去除注释部分
                    if line == "":
                        continue  # 如果行为空，跳过
                    # 用正则表达式匹配产生式规则的格式
                    match = re.match(r"\s*([^->]+)\s*->\s*(.*)", line)
                    if match:
                        left_side = match.group(1).strip()  # 获取产生式左侧（非终结符）并去除空格
                        right_side = match.group(2).strip()  # 获取产生式右侧（可能包含多个替代项）并去除空格
                        alternatives = [alt.strip() for alt in right_side.split("|")]  # 将右侧的替代项分割成列表

                        # 处理非终结符
                        if left_side not in self.non_terminal_symbols:
                            self.non_terminal_symbols.append(left_side)
                        # 计算产生式左侧非终结符的索引，加上终结符的数量
                        from_id = self.non_terminal_symbols.index(left_side) + self.epsilon_id

                        # 处理每个替代项（产生式右部）
                        for alt in alternatives:
                            if alt.strip() == "":
                                print("Empty alternative found in production rule:", line)
                                continue
                            tmp = Production()
                            tmp.id = len(self.productions)
                            tmp.non_terminal_symbol_id = from_id
                            # 处理替代项中的每个符号，忽略空格
                            alt_split = [x for x in alt.split()]

                            for symbol in alt_split:
                                if symbol in self.terminal_symbols:
                                    to_id = self.terminal_symbols.index(symbol)
                                elif symbol in self.non_terminal_symbols:
                                    to_id = self.non_terminal_symbols.index(symbol) + self.epsilon_id
                                else:
                                    # 如果符号不是终结符也不是非终结符，将其添加到非终结符列表中
                                    self.non_terminal_symbols.append(symbol)
                                    to_id = self.non_terminal_symbols.index(symbol) + self.epsilon_id
                                # 将产生式右侧每个符号的索引添加到产生式对象的to_ids列表中
                                tmp.to_ids.append(to_id)
                            self.productions.append(tmp)  # 将产生式对象添加到产生式列表中
                    else:
                        print("Invalid production rule format:", line)
        except FileNotFoundError:
            return False  # 如果文件不存在，返回False
        return True  # 如果成功读取配置文件并处理产生式规则，返回True

    def find_firsts(self):
        # 找first集的实现
        """
        计算文法的First集合。
        First集合是文法中每个非终结符的一个集合，包含其能推导出的所有可能的首终结符（终结符或epsilon）。
        返回：无，直接更新self.firsts列表。
        注意：
        - self.terminal_symbols: 终结符列表
        - self.non_terminal_symbols: 非终结符列表
        - self.productions: 产生式规则列表
        - self.firsts: 存储First集合的列表，每个元素是一个集合，对应一个非终结符的First集合。
        """
        # 初始化终结符：FIRST(x) = {x} 和 FIRST(epsilon) = {epsilon}
        for i in range(self.epsilon_id + 1):
            self.firsts.append({i})
        # 初始化非终结符：FIRST(X) = ∅
        for i in range(len(self.non_terminal_symbols) - 1):
            self.firsts.append(set())

        # 反复迭代直到收敛
        while self._update_first_sets():
            continue
        return

    def _update_first_sets(self):
        """
        尝试更新所有非终结符的 FIRST 集合。
        如果本轮有任何一个 FIRST 集合发生变化，则返回 True。
        否则返回 False，说明已收敛。
        """
        updated = False
        for production in self.productions:
            A = production.non_terminal_symbol_id  # 左部编号
            rhs = production.to_ids  # 右部符号列表

            for i, symbol in enumerate(rhs):
                if symbol <= self.epsilon_id:
                    # 是终结符或者epsilon：FIRST(A) += symbol
                    if symbol not in self.firsts[A]:
                        self.firsts[A].add(symbol)
                        updated = True
                    break
                else:
                    # 是非终结符：FIRST(A) += FIRST(symbol) - {ε}
                    for sym in self.firsts[symbol]:
                        if sym != self.epsilon_id and sym not in self.firsts[A]:
                            self.firsts[A].add(sym)
                            updated = True
                    # 如果该非终结符不能推出 ε，停止处理当前产生式
                    if self.epsilon_id not in self.firsts[symbol]:
                        break
                    # 如果所有符号都能推出 ε，最后也要加入 ε
                    if i == len(rhs) - 1 and self.epsilon_id not in self.firsts[A]:
                        self.firsts[A].add(self.epsilon_id)
                        updated = True
        return updated

    def find_firsts_alpha(self, alpha, firsts):
        """
        找句子的First集合。
        参数：
        - alpha: 包含整数的列表，表示句子中的符号序列。
        - firsts: 用于存储句子First集合的集合，该集合将被清空并更新。
        注意：
        - self.firsts: 存储文法非终结符First集合的列表。
        - self.terminal_symbols: 终结符列表。
        """
        firsts.clear()  # 清空传入的firsts集合
        for i in range(len(alpha)):
            for cnt in self.firsts[alpha[i]]:
                if cnt != self.epsilon_id:
                    firsts.add(cnt)  # 将文法非终结符的First集合添加到句子First集合中
            if self.epsilon_id not in self.firsts[alpha[i]]:
                break  # 如果epsilon不在当前符号的First集合中，终止循环
            if (
                    i == len(alpha) - 1
                    and self.epsilon_id in self.firsts[alpha[i]]
            ):
                # 如果是句子的最后一个符号，并且epsilon在其First集合中，添加epsilon到句子First集合中
                firsts.add(self.epsilon_id)

    def find_closures(self, closure):
        """
        找闭包的实现，若有项目[A→α·Bβ,b]属于CLOSURE(I)，B→γ是文法中的产生式，β∈V*，c∈FIRST(βb)，则[B→·γ,c]也属于CLOSURE(I)中。
        参数：
        - closure: 闭包对象，其中包含项目的集合。
        注意：
        - self.productions: 存储文法产生式的列表。
        - self.terminal_symbols: 存储终结符的列表。
        """
        # 对于给定闭包中的每个项目
        i = 0
        while i < len(closure.items):
            lr1_item = closure.items[i]
            production = self.productions[lr1_item.production_id]
            i += 1

            # 如果项目的点位置已经到达产生式右侧的末尾，跳过
            if lr1_item.dot_pos >= len(production.to_ids):
                continue
            # 获取项目点后的符号的 ID
            symbol_id = production.to_ids[lr1_item.dot_pos]
            # 如果该符号是终结符或epsilon，跳过
            if symbol_id <= self.epsilon_id:
                continue
            # 对于每个产生式
            for j in range(len(self.productions)):
                # 如果产生式的左侧是当前符号 ID
                if self.productions[j].non_terminal_symbol_id == symbol_id:
                    # 创建新的项目
                    alpha = []
                    # 从当前产生式符号的下一个开始遍历，如果不是epsilon
                    for k in range(lr1_item.dot_pos + 1, len(production.to_ids), ):
                        if production.to_ids[k] != self.epsilon_id:
                            alpha.append(production.to_ids[k])
                    alpha.append(lr1_item.terminal_id)
                    # 计算后继符号的first集
                    firsts = set()
                    self.find_firsts_alpha(alpha, firsts)
                    # 对于每个first集合中的符号，创建新的项目并加入闭包
                    for first in firsts:
                        item = LR1Item(j, 0, first)
                        if item not in closure.items:
                            closure.items.append(item)

    def find_gos(self):
        """
        找Go表的实现。
        注意：
        - self.productions: 存储文法产生式的列表。
        - self.terminal_symbols: 存储终结符的列表。
        - self.non_terminal_symbols: 存储非终结符的列表。
        - self.closures: 存储闭包的列表。
        - self.gos: 存储Go表的列表，每个元素是一个字典{symbol_id: closure_id}，表示一个闭包的后继闭包及其映射。
        """
        # 创建新的产生式 S'->Program，并将其添加到产生式列表中
        new_production = Production()
        new_production.id = len(self.productions)
        new_production.non_terminal_symbol_id = self.epsilon_id + len(self.non_terminal_symbols)  # S
        new_production.to_ids.append(self.get_id_by_str("Program"))  # Program
        self.productions.append(new_production)  # S -> Program作为最后一个产生式
        # 创建初始项，表示S->.Program,#
        new_item = LR1Item(len(self.productions) - 1, 0, self.get_id_by_str("#"))

        # 创建初始闭包，包含初始项
        start_closure = Closure()
        start_closure.id = 0
        start_closure.items.append(new_item)

        # 找初始闭包的闭包
        self.find_closures(start_closure)

        # 将初始闭包及其映射加入闭包列表和映射列表
        self.closures.append(start_closure)
        self.gos.append({})

        # 初始化当前闭包标识
        now_closure_id = 0

        # 遍历闭包列表，构建闭包的后继闭包及其映射
        while now_closure_id < len(self.closures):
            # 遍历所有终结符和非终结符的编号
            for i in range(self.epsilon_id + len(self.non_terminal_symbols) + 1):
                if i == self.epsilon_id:  # epsilon
                    continue
                # 创建新的闭包
                tmp = Closure()
                # 遍历当前闭包中的每个项
                for item in self.closures[now_closure_id].items:
                    production = self.productions[item.production_id]
                    # 如果项的点位置已经到达产生式右侧的末尾，跳过
                    if len(production.to_ids) == item.dot_pos:
                        continue
                    # 如果产生式右侧的下一位符号的编号是当前遍历的编号
                    if production.to_ids[item.dot_pos] == i:
                        # 创建新的项，表示将点向后移动一位
                        new_item = LR1Item(
                            item.production_id, item.dot_pos + 1, item.terminal_id
                        )
                        tmp.items.append(new_item)
                # 如果新的闭包中有项
                if tmp.items:
                    # 找新闭包的闭包
                    self.find_closures(tmp)
                    # 如果找到相同的闭包，更新映射
                    if tmp in self.closures:
                        if i in self.gos[now_closure_id].keys():
                            print("Error: Go table error")
                        self.gos[now_closure_id][i] = self.closures.index(tmp)
                    # 如果未找到相同的闭包，添加新的闭包及其映射
                    else:
                        tmp.id = len(self.closures)
                        self.closures.append(tmp)
                        self.gos.append({})
                        if i in self.gos[now_closure_id].keys():
                            print("Error: Go table error")
                        self.gos[now_closure_id][i] = tmp.id

            now_closure_id += 1

    def find_gotos_and_actions(self):
        """
        goto和action表的实现
        注意：
        - self.terminal_symbols: 存储终结符的列表
        - self.non_terminal_symbols: 存储非终结符的列表
        - self.closures: 存储闭包的列表
        - self.gos: 存储Go表的列表，每个元素是一个字典{symbol_id: closure_id}，表示一个闭包的后继闭包及其映射
        - self.productions: 存储文法产生式的列表
        - self.goto_table: 存储Goto表的列表，每个元素是一个字典{non_terminal_symbol_id: closure_id}，表示一个闭包的后继闭包及其映射
        - self.action_table: 存储Action表的列表，每个元素是一个字典，表示一个闭包的后继闭包及其映射
        """
        for i in range(len(self.closures)):
            self.goto_table.append({})
            self.action_table.append({})

            # 处理Goto表
            for tmp in self.gos[i].items():
                # 如果是非终结符
                if tmp[0] > self.epsilon_id:
                    if tmp[0] in self.goto_table[i].keys():
                        print("Error: Goto table error")
                    self.goto_table[i][tmp[0]] = tmp[1]

            # 处理Action表
            for item in self.closures[i].items:
                production = self.productions[item.production_id]
                flag_to_reduce = (len(production.to_ids) == item.dot_pos)
                flag_to_reduce |= (production.to_ids == [self.epsilon_id])
                # 如果·在末尾或产生式右侧是epsilon
                if flag_to_reduce:
                    if production.non_terminal_symbol_id != self.epsilon_id + len(self.non_terminal_symbols):
                        # 如果[A->α· , a]在Ii中，且A≠S，那么置action[i, a]为reduce j
                        action = (ACTION_R, item.production_id)
                        if item.terminal_id in self.action_table[i].keys():
                            action_list = self.action_table[i][item.terminal_id]
                            if action in action_list:
                                continue
                            print("Error: Action table error2")
                        else:
                            self.action_table[i][item.terminal_id] = []
                        self.action_table[i][item.terminal_id].append(action)
                    else:
                        # 如果[S->Program·, #]在Ii中，那么置action[i, #] = acc
                        if item.terminal_id == self.epsilon_id - 1:
                            action = (ACTION_ACC, 0)
                            if item.terminal_id in self.action_table[i].keys():
                                action_list = self.action_table[i][item.terminal_id]
                                if action in action_list:
                                    continue
                                print("Error: Action table error1")
                            else:
                                self.action_table[i][item.terminal_id] = []
                            self.action_table[i][item.terminal_id].append(action)
                else:
                    # 获取项目点后的符号的 ID
                    symbol_id = production.to_ids[item.dot_pos]
                    if symbol_id < self.epsilon_id:
                        # 如果[A->α·aß, b]在Ii中，且GO(Ii, a) = Ij ，那么置action[i, a]为shift j
                        if symbol_id in self.gos[i]:
                            action = (ACTION_S, self.gos[i][symbol_id])
                            if symbol_id in self.action_table[i].keys():
                                action_list = self.action_table[i][symbol_id]
                                if action in action_list:
                                    continue
                                print("Error: Action table error3")
                            else:
                                self.action_table[i][symbol_id] = []
                            self.action_table[i][symbol_id].append(action)

        for i in range(len(self.closures)):
            flag = False
            for key, value in self.action_table[i].items():
                if len(value) > 1:
                    flag = True
                    terminal_symbol = self.get_str_by_id(key)
                    print(f"Error: {terminal_symbol} has multiple actions in closure {i}")
                    for action in value:
                        action_type = action[0]
                        if action_type == ACTION_ACC:
                            action_type = "acc"
                            print(f"acc")
                        elif action_type == ACTION_R:
                            action_type = "r"
                            production = self.productions[action[1]]
                            production_literal = self.get_str_by_id(production.non_terminal_symbol_id) + '->'
                            for id in production.to_ids:
                                production_literal += self.get_str_by_id(id) + ' '
                            production_literal = production_literal[:-1]  # 去除末尾多的空格
                            print(f"r {production_literal}")
                        elif action_type == ACTION_S:
                            action_type = "s"
                            next_state_id = action[1]
                            print(f"s {next_state_id}")
                        else:
                            action_type = "error"
                            print(f"error")
            if flag:
                print(f"Error: closure {i} has multiple actions" + "*" * 20)

    def getParse(self, lex):
        """
        执行语法分析
        参数：
        - lex: 词法分析的输出结果，包含词法单元的信息
        返回：
        - 树形结构，表示语法分析的结果
        """
        stack = []
        item = {"state": 0, "tree": {"root": '#'}}
        stack.append(item)
        self.parse_process_display = []
        self.parse_process_display.append(['步骤', '状态栈', '符号栈', '待规约串', '动作说明'])
        pending_string = [cur['prop'].value for cur in lex]
        pending_string = ', '.join(pending_string)
        self.parse_process_display.append(['0', '0', '#', pending_string, '初始状态'])

        index = 0
        cnt = 0
        while index < len(lex):
            cnt += 1
            cur = lex[index]
            if cur["prop"] == tokenType.UNKNOWN:
                print(f"Error: {token} at {cur['loc']}")
                return {"root": "词法解析失败", "err": cur["loc"]}
            token = tokenType_to_terminal(cur["prop"])
            token_id = self.get_id_by_str(token)
            if token_id >= self.epsilon_id:
                print(f"Error: {token} at {cur['loc']}")
                return {"root": "语法错误/代码不完整，无法解析1", "err": cur["loc"]}

            # 用于展示
            new_display_item = [None] * 5
            new_display_item[0] = str(cnt)

            current_state = self.action_table[stack[-1]["state"]]
            # if stack[-1]["state"] == 0:
            #     print(self.action_table[0], "-------------")
            if token_id not in current_state:
                print(f"Error: {token} at {cur['loc']}")
                return {"root": "语法错误/代码不完整，无法解析2", "err": cur["loc"]}

            current_action_list = current_state[token_id]

            first_action = current_action_list[0]

            if first_action[0] == ACTION_S:
                next_state_id = first_action[1]
                item = {"state": next_state_id, "tree": {"root": token, "children": []}}
                stack.append(item)
                index += 1  # 当前输入串移动到下一个字符

                new_display_item[4] = f'移进“{token}”, 状态{next_state_id}压栈'

            elif first_action[0] == ACTION_R:
                production = self.productions[first_action[1]]
                production_literal = self.get_str_by_id(production.non_terminal_symbol_id) + '->'
                children = []
                if production.to_ids == [self.epsilon_id]:
                    production_literal += self.get_str_by_id(self.epsilon_id) + ' '
                    children.append({"root": self.get_str_by_id(self.epsilon_id), "children": []})
                else:
                    for id in production.to_ids:
                        child = stack.pop()["tree"]
                        children.insert(0, child)
                        production_literal += self.get_str_by_id(id) + ' '

                current_state = self.goto_table[stack[-1]["state"]]
                next_state_id = current_state[production.non_terminal_symbol_id]
                item = {
                    "state": next_state_id,
                    "tree": {
                        "root": self.get_str_by_id(production.non_terminal_symbol_id),
                        "children": children,
                    },
                }
                stack.append(item)
                new_display_item[4] = f'使用产生式({production_literal[:-1]})进行规约'  # 去除末尾多的空格
            elif first_action[0] == ACTION_ACC:
                print("Accept")
                ret = stack[-1]["tree"]
                with open("parser_out.json", "w", encoding="utf-8") as f:
                    json.dump(ret, f, indent=4, ensure_ascii=False)
                return ret
            else:
                print(f"Error: {token} at {cur['loc']}")
                return {"root": "语法错误/代码不完整，无法解析3", "err": "parser_error"}

            state_stack = [str(item['state']) for item in stack]
            state_stack = ' '.join(state_stack)

            symbol_stack = [str(item['tree']['root']) for item in stack]
            symbol_stack = ' '.join(symbol_stack)

            pending_string = [cur['prop'].value for cur in lex[index:]]
            pending_string = ', '.join(pending_string)

            new_display_item[1] = state_stack
            new_display_item[2] = symbol_stack
            new_display_item[3] = pending_string
            self.parse_process_display.append(new_display_item)

    def get_goto_table(self):
        print("Get goto table")
        goto_table = []
        # 去除epsilon
        goto_table.append(["Status"] + self.non_terminal_symbols[1:])
        length = len(self.non_terminal_symbols) - 1
        for i in range(len(self.closures)):
            goto_table.append([str(i)] + [""] * length)
            for j in range(length):
                # 注意非终结符的id从self.epsilon_id开始
                t = self.epsilon_id + 1 + j
                if t in self.goto_table[i].keys():
                    goto_table[i + 1][j + 1] = str(self.goto_table[i][t])
        print("End get goto table")
        return goto_table

    def get_action_table(self):
        print("Get action table")
        action_table = []
        action_table.append(["Status"] + self.terminal_symbols)
        for i in range(len(self.closures)):
            action_table.append([str(i)] + [""] * self.epsilon_id)
            for j in range(self.epsilon_id):
                if j in self.action_table[i].keys():
                    tmp = self.action_table[i][j][0]
                    action_table[i + 1][j + 1] = ActionType[tmp[0]] + (
                        str(tmp[1]) if tmp[0] != ACTION_ACC else ""
                    )
        print("End get action table")
        return action_table
