import json
from PyQt5.QtCore import QObject, pyqtSlot, QThread, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QLabel, QTextEdit, QPushButton, QMessageBox
)
from myLexer import Lexer
from myParser import Parser

class Compiler(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lexer = Lexer()
        self.parser = Parser()
        self.goto_table = self.parser.get_goto_table()
        self.action_table = self.parser.get_action_table()

    @pyqtSlot(str, result=str)
    def process(self, code_str):
        token_list, lexer_success = self.getLex(code_str)
        parse_result = self.getParse(token_list)
        return json.dumps(
            {
                "lexer": self.dumpTokenList(token_list),
                "lexer_success": lexer_success,
                **parse_result,
            }
        )

    def dumpTokenList(self, token_list):
        def dumpToken(r):
            r["prop"] = r["prop"].value
            return r

        return list(map(dumpToken, token_list))

    def getParse(self, token_list):
        if self.parser is not None:
            parsed_result = self.parser.getParse(token_list)
            return {
                "ast": parsed_result,
                "goto": self.goto_table,
                "action": self.action_table,
                "process": self.parser.parse_process_display,
            }
        else:
            launching = "Parser 正在启动，请稍等。"
            return {
                "ast": {"root": launching, "err": "parser_not_ready"},
                "goto": [[launching]],
                "action": [[launching]],
                "process": [[launching]],
            }

    def getLex(self, code_str: str):
        return self.lexer.getLex(code_str.splitlines())

class CompilerGUI(QMainWindow):
    def __init__(self, compiler):
        super().__init__()
        self.compiler = compiler
        self.setWindowTitle("编译器可视化分析工具")
        self.setGeometry(200, 100, 1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.editor_tab = QWidget()
        self.lex_tab = QWidget()
        self.ast_tab = QWidget()
        self.table_tab = QWidget()
        self.process_tab = QWidget()

        self.tabs.addTab(self.editor_tab, "源代码编辑")
        self.tabs.addTab(self.lex_tab, "词法分析")
        self.tabs.addTab(self.ast_tab, "语法树")
        self.tabs.addTab(self.table_tab, "分析表")
        self.tabs.addTab(self.process_tab, "规约过程")

        self.initEditorTab()
        self.initLexTab()
        self.initAstTab()
        self.initTableTab()
        self.initProcessTab()

        self.loadFile("mytest.c")

    def initEditorTab(self):
        layout = QVBoxLayout()
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 12))
        layout.addWidget(self.code_editor)

        self.analyze_button = QPushButton("重新分析")
        self.analyze_button.clicked.connect(self.analyzeCurrentCode)
        layout.addWidget(self.analyze_button)

        self.editor_tab.setLayout(layout)

    def analyzeCurrentCode(self):
        code = self.code_editor.toPlainText()
        result_json = self.compiler.process(code)
        result = json.loads(result_json)
        self.updateAll(result)

    def loadFile(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
                self.code_editor.setPlainText(code)
                self.analyzeCurrentCode()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载文件 {filepath}：{e}")

    def initLexTab(self):
        layout = QVBoxLayout()
        self.lex_table = QTableWidget()
        layout.addWidget(self.lex_table)
        self.lex_tab.setLayout(layout)

    def initAstTab(self):
        layout = QVBoxLayout()
        self.ast_tree = QTreeWidget()
        self.ast_tree.setHeaderLabel("语法树结构")
        layout.addWidget(self.ast_tree)
        self.ast_tab.setLayout(layout)

    def initTableTab(self):
        layout = QVBoxLayout()
        self.action_label = QLabel("ACTION 表")
        self.action_table = QTableWidget()
        layout.addWidget(self.action_label)
        layout.addWidget(self.action_table)

        self.goto_label = QLabel("GOTO 表")
        self.goto_table = QTableWidget()
        layout.addWidget(self.goto_label)
        layout.addWidget(self.goto_table)

        self.table_tab.setLayout(layout)

    def initProcessTab(self):
        layout = QVBoxLayout()
        self.proc_table = QTableWidget()
        layout.addWidget(self.proc_table)
        self.process_tab.setLayout(layout)

    def updateAll(self, data):
        self.showLexResult(data["lexer"])
        self.showAstTree(data["ast"])
        self.showTables(data["action"], data["goto"])
        self.showProcess(data["process"])

    def showLexResult(self, lexer):
        headers = ["id", "content", "prop", "row", "col"]
        self.lex_table.setColumnCount(len(headers))
        self.lex_table.setHorizontalHeaderLabels(headers)
        self.lex_table.setRowCount(len(lexer))

        for row, token in enumerate(lexer):
            self.lex_table.setItem(row, 0, QTableWidgetItem(str(token["id"])))
            self.lex_table.setItem(row, 1, QTableWidgetItem(token["content"]))
            self.lex_table.setItem(row, 2, QTableWidgetItem(token["prop"]))
            self.lex_table.setItem(row, 3, QTableWidgetItem(str(token["loc"]["row"])))
            self.lex_table.setItem(row, 4, QTableWidgetItem(str(token["loc"]["col"])))

    def showAstTree(self, ast):
        self.ast_tree.clear()
        def addNode(node, parent=None):
            item = QTreeWidgetItem([node["root"]])
            if parent is None:
                self.ast_tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
            for child in node.get("children", []):
                addNode(child, item)

        addNode(ast)

    def showTables(self, action, goto):
        def fill_table(widget, data):
            widget.setColumnCount(len(data[0]))
            widget.setRowCount(len(data))
            for i, row in enumerate(data):
                for j, cell in enumerate(row):
                    widget.setItem(i, j, QTableWidgetItem(cell))

        fill_table(self.action_table, action)
        fill_table(self.goto_table, goto)

    def showProcess(self, process):
        headers = ["状态栈", "状态", "符号栈", "输入串", "动作"]
        self.proc_table.setColumnCount(len(headers))
        self.proc_table.setHorizontalHeaderLabels(headers)
        self.proc_table.setRowCount(len(process))
        for i, row in enumerate(process):
            for j, val in enumerate(row):
                self.proc_table.setItem(i, j, QTableWidgetItem(val))

if __name__ == "__main__":
    # Initialize the application and the compiler
    import sys
    app = QApplication(sys.argv)
    compiler = Compiler()
    gui = CompilerGUI(compiler)
    gui.show()
    sys.exit(app.exec_())
