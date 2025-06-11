import json
from PyQt5.QtCore import QObject, pyqtSlot, QThread, Qt, QRectF
from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QFontMetrics, QPen, QBrush
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QLabel, QTextEdit, QPushButton, QMessageBox,
    QAbstractScrollArea, QStyleFactory, QHeaderView, QGraphicsScene, QGraphicsView, QGraphicsSimpleTextItem,
    QGraphicsItem, QGraphicsRectItem, QFileDialog
)
from myLexer import Lexer
from myParser import Parser
from tokenType import tokenKeywords, tokenSymbols


def beautify_table_widget(table: QTableWidget):
    """设置 QTableWidget 的美观显示属性"""
    table.resizeColumnsToContents()
    table.resizeRowsToContents()
    # table.horizontalHeader().setStretchLastSection(True)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止编辑（可选）


def setModernStyle(app):
    app.setStyle(QStyleFactory.create("Fusion"))

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 245, 245))  # 背景
    palette.setColor(QPalette.Base, QColor(255, 255, 255))  # 编辑框背景
    palette.setColor(QPalette.Text, QColor(30, 30, 30))  # 文本颜色
    palette.setColor(QPalette.Button, QColor(200, 200, 200))
    app.setPalette(palette)


def get_color(root):
    if root in tokenKeywords:
        return QColor("#007acc")  # 蓝色
    elif root in tokenSymbols:
        return QColor("#2ecc71")  # 绿色
    elif root in ["identifier", "integer_constant"]:
        return QColor("#e74c3c")  # 红色
    else:
        return QColor("#e67e22")  # 橙色


class AstNodeItem(QGraphicsRectItem):
    def __init__(self, node_id, text, x, y, w, h, color, font, node_data, parent=None):
        super().__init__(x, y, w, h, parent)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black))
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.node_id = node_id
        self.node_data = node_data
        self.children_lines = []
        self.children_items = []
        self.collapsed = False

        self.text_item = QGraphicsSimpleTextItem(text, self)
        self.text_item.setFont(font)
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(x + (w - text_rect.width()) / 2, y + (h - text_rect.height()) / 2)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(Qt.yellow))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(get_color(self.node_data["root"])))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            QMessageBox.information(None, "节点信息", str(self.node_data), QMessageBox.Ok)
        elif event.button() == Qt.RightButton:
            self.toggleCollapse()
        super().mousePressEvent(event)

    def toggleCollapse(self):
        self.collapsed = not self.collapsed
        for child_item, line in zip(self.children_items, self.children_lines):
            child_item.setVisible(not self.collapsed)
            line.setVisible(not self.collapsed)
            if hasattr(child_item, "collapse_all"):
                child_item.collapse_all(self.collapsed)

    def collapse_all(self, collapsed):
        self.setVisible(not collapsed)
        for child_item, line in zip(self.children_items, self.children_lines):
            child_item.setVisible(not collapsed)
            line.setVisible(not collapsed)
            if hasattr(child_item, "collapse_all"):
                child_item.collapse_all(collapsed)


class Compiler(QObject):
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.lexer = Lexer()
        self.parser = Parser(filename)
        self.goto_table = self.parser.get_goto_table()
        self.action_table = self.parser.get_action_table()

    def process(self, code_str):
        token_list, lexer_success = self.getLex(code_str)
        try:
            parse_result = self.getParse(token_list)
        except Exception as e:
            parse_result = {
                "ast": {"root": str(e), "err": "parse_error"},
                "goto": [["Error"]],
                "action": [["Error"]],
                "process": [["Error"]],
                "semantic_quaternation": [["Error"]],
            }
            lexer_success = False
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
                "semantic_quaternation": self.parser.semantic_quaternation,
                "semantic_error_occur": self.parser.semantic_error_occur,
                "semantic_error_message": self.parser.semantic_error_message,
            }
        else:
            launching = "Parser 正在启动，请稍等。"
            return {
                "ast": {"root": launching, "err": "parser_not_ready"},
                "goto": [[launching]],
                "action": [[launching]],
                "process": [[launching]],
                "semantic_quaternation": [[launching]],
                "semantic_error_occur": False,
                "semantic_error_message": [],
            }

    def getLex(self, code_str: str):
        return self.lexer.getLex(code_str.splitlines())


class CompilerGUI(QMainWindow):
    def __init__(self, compiler, filename="mytest.c"):
        super().__init__()
        self.compiler = compiler
        self.setWindowTitle("编译器可视化分析工具")
        self.setGeometry(200, 100, 1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.editor_tab = QWidget()
        self.lex_tab = QWidget()
        self.ast_tab = QWidget()
        self.ast_graph_tab = QWidget()
        self.table_tab = QWidget()
        self.process_tab = QWidget()
        self.quad_tab = QWidget()

        self.tabs.addTab(self.editor_tab, "源代码编辑")
        self.tabs.addTab(self.lex_tab, "词法分析")
        self.tabs.addTab(self.ast_tab, "语法树")
        self.tabs.addTab(self.ast_graph_tab, "语法树图示")
        self.tabs.addTab(self.table_tab, "分析表")
        self.tabs.addTab(self.process_tab, "规约过程")
        self.tabs.addTab(self.quad_tab, "中间代码")

        self.initEditorTab()
        self.initLexTab()
        self.initAstTab()
        self.initAstGraphTab()
        self.initTableTab()
        self.initProcessTab()
        self.initQuadTab()

        self.loadFile(filename)

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

    def initAstGraphTab(self):
        class ZoomableGraphicsView(QGraphicsView):
            def __init__(self, scene):
                super().__init__(scene)
                self.setDragMode(QGraphicsView.ScrollHandDrag)

            def wheelEvent(self, event):
                factor = 1.2 if event.angleDelta().y() > 0 else 0.8
                self.scale(factor, factor)

        layout = QVBoxLayout()
        self.scene = QGraphicsScene()
        self.ast_view = ZoomableGraphicsView(self.scene)
        layout.addWidget(self.ast_view)
        self.ast_graph_tab.setLayout(layout)

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

    def initQuadTab(self):
        layout = QVBoxLayout()
        self.quad_table = QTableWidget()
        layout.addWidget(self.quad_table)
        self.quad_tab.setLayout(layout)

    def updateAll(self, data):
        self.showLexResult(data["lexer"])
        self.showAstTree(data["ast"])
        self.showAstGraphTree(data["ast"])
        self.showTables(data["action"], data["goto"])
        self.showProcess(data["process"])
        self.showQuad(data["semantic_quaternation"])

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

        self.lex_table.verticalHeader().setVisible(False)
        beautify_table_widget(self.lex_table)

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

    def showAstGraphTree(self, ast):
        def get_node_size(text, font):
            metrics = QFontMetrics(font)
            width = metrics.horizontalAdvance(text) + 20
            height = metrics.height() + 10
            return width, height

        # 分配唯一 ID 给每个节点以便索引
        def assign_ids(node):
            node["id"] = id(node)
            for child in node.get("children", []):
                assign_ids(child)

        def calculate_layout(node, depth=0):
            text = node["root"]
            width, height = get_node_size(text, font)
            sizes[node["id"]] = (width, height)

            children = node.get("children", [])
            child_xs = []

            if children:
                for child in children:
                    child_node_x = calculate_layout(child, depth + 1)
                    child_xs.append(child_node_x)
                node_x = (min(child_xs) + max(child_xs)) / 2
            else:
                node_x = calculate_layout.offset + width / 2
                calculate_layout.offset += width + x_spacing

            center_positions[node["id"]] = (node_x, depth * (height + y_spacing) + height / 2)
            return node_x

        def draw_node(node):
            text = node["root"]
            x, y = center_positions[node["id"]]
            w, h = sizes[node["id"]]
            x = x - w / 2
            y = y - h / 2
            item = AstNodeItem(node["id"], text, x, y, w, h, get_color(text), font, node, parent=None)
            self.scene.addItem(item)
            node_items[node["id"]] = item

            for child in node.get("children", []):
                draw_node(child)
                child_x, child_y = center_positions[child["id"]]
                child_w, child_h = sizes[child["id"]]
                child_y = child_y - child_h / 2
                line = self.scene.addLine(
                    x + w / 2, y + h,
                    child_x, child_y,
                    QPen(Qt.black)
                )
                item.children_lines.append(line)
                item.children_items.append(node_items[child["id"]])

        center_positions = {}  # 存储每个节点的实际中心位置
        sizes = {}  # 存储每个节点的宽高
        node_items = {}
        font = QFont("Arial", 10)
        x_spacing, y_spacing = 40, 80

        assign_ids(ast)
        calculate_layout.offset = 0
        calculate_layout(ast)

        self.scene.clear()
        draw_node(ast)

        # 缩放和平移设置
        self.ast_view.setRenderHint(QPainter.Antialiasing)
        self.ast_view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        bounding_rect = self.scene.itemsBoundingRect()
        expanded_rect = QRectF(
            bounding_rect.x() - 100,
            bounding_rect.y() - 100,
            bounding_rect.width() + 200,
            bounding_rect.height() + 200
        )
        self.ast_view.setSceneRect(expanded_rect)  # 增加一些边距

    def showTables(self, action, goto):
        def fill_table(widget, data):
            headers = data[0]
            widget.setColumnCount(len(headers))
            widget.setHorizontalHeaderLabels(headers)
            widget.setRowCount(len(data) - 1)
            for i, row in enumerate(data[1:]):
                for j, cell in enumerate(row):
                    widget.setItem(i, j, QTableWidgetItem(cell))

            beautify_table_widget(widget)

        fill_table(self.action_table, action)
        fill_table(self.goto_table, goto)

    def showProcess(self, process):
        headers = process[0]
        self.proc_table.setColumnCount(len(headers))
        self.proc_table.setHorizontalHeaderLabels(headers)
        self.proc_table.setRowCount(len(process) - 1)
        for i, row in enumerate(process[1:]):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                item.setToolTip(str(val))
                self.proc_table.setItem(i, j, item)

        beautify_table_widget(self.proc_table)

    def showQuad(self, quad_data):
        headers = ["地址", "四元式", "op", "arg1", "arg2", "result"]
        self.quad_table.setColumnCount(len(headers))
        self.quad_table.setHorizontalHeaderLabels(headers)
        self.quad_table.setRowCount(len(quad_data) - 1)

        for i, row in enumerate(quad_data[1:]):
            address = row[0]
            quad_str = row[1]

            # 尝试解析四元式字符串
            try:
                # 去除括号并分割
                quad_content = quad_str.strip()[1:-1].split(',')
                op = quad_content[0].strip()
                arg1 = quad_content[1].strip()
                arg2 = quad_content[2].strip()
                result = quad_content[3].strip()
            except Exception:
                op = arg1 = arg2 = result = "解析错误"

            display_row = [address, quad_str, op, arg1, arg2, result]

            for j, val in enumerate(display_row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                item.setToolTip(str(val))
                self.quad_table.setItem(i, j, item)

        beautify_table_widget(self.quad_table)


if __name__ == "__main__":
    # Initialize the application and the compiler
    import sys

    app = QApplication(sys.argv)
    setModernStyle(app)
    # 默认文件名
    default_cfg_filename = "mytest.cfg"
    default_code_filename = "mytest.c"

    if 0:
        cfg_filename = default_cfg_filename
        code_filename = default_code_filename
    else:
        # 选择配置文件
        cfg_filename, _ = QFileDialog.getOpenFileName(
            None, "选择文法配置文件", default_cfg_filename, "Config Files (*.cfg);;All Files (*)"
        )
        if not cfg_filename:
            cfg_filename = default_cfg_filename

        # 选择代码文件
        code_filename, _ = QFileDialog.getOpenFileName(
            None, "选择代码文件", default_code_filename, "C Files (*.c);;All Files (*)"
        )
        if not code_filename:
            code_filename = default_code_filename

    # 启动编译器和GUI
    compiler = Compiler(cfg_filename)
    gui = CompilerGUI(compiler, code_filename)
    gui.show()
    sys.exit(app.exec_())
