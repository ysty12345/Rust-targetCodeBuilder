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
        self.start_address = start_address
        self.error_occur = False
        self.error_msg = []

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
        pass

    def getQuaternationTable(self):
        ret = [["地址", "四元式"]]
        for i, instr in enumerate(self.quaternion_table):
            ret.append([str(i + self.start_address), str(instr)])
        return ret
