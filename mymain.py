import tkinter as tk
from tkinter import ttk
import json

# 假设从 JSON 文件或变量中读取结果
lex_result = [
    {"id": 1, "content": "fn", "prop": "kw_fn", "loc": {"row": 1, "col": 1}},
    # ...其他token
]

parse_tree = {
    "root": "Declaration",
    "children": [
        {"root": "Type", "children": [{"root": "int", "children": []}]},
        {"root": "identifier", "children": []},
        {
            "root": "DeclarationType",
            "children": [
                {"root": "VarDeclaration", "children": [{"root": ";", "children": []}]}
            ]
        }
    ]
}

action_table = [["S5", "", "", "S4", "", ""], ["", "acc", "", "", "", ""]]
goto_table = [["1", "2", "3"], ["", "", ""]]

parse_process = [
    ['0', '0', '#', 'fn int x;', '初始状态'],
    ['1', '1', '#fn', 'int x;', '移入kw_fn'],
    # ...更多步骤
]

# ----------------- 主 GUI 构建函数 -----------------
def build_gui():
    root = tk.Tk()
    root.title("简易语法分析器 GUI")
    root.geometry("1000x600")

    # 分为四个部分的 Notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # --- 1. 词法分析页 ---
    frame_lex = ttk.Frame(notebook)
    notebook.add(frame_lex, text="词法分析")

    tree_lex = ttk.Treeview(frame_lex, columns=('id', 'content', 'prop', 'row', 'col'), show='headings')
    for col in tree_lex["columns"]:
        tree_lex.heading(col, text=col)
    for token in lex_result:
        tree_lex.insert('', tk.END, values=(token['id'], token['content'], token['prop'],
                                             token['loc']['row'], token['loc']['col']))
    tree_lex.pack(fill='both', expand=True)

    # --- 2. 语法树页 ---
    frame_tree = ttk.Frame(notebook)
    notebook.add(frame_tree, text="语法树")

    tree_view = ttk.Treeview(frame_tree)
    tree_view.pack(fill='both', expand=True)

    def insert_tree(node, parent=""):
        item = tree_view.insert(parent, 'end', text=node["root"])
        for child in node.get("children", []):
            insert_tree(child, item)

    insert_tree(parse_tree)

    # --- 3. 表格展示页 ---
    frame_tables = ttk.Frame(notebook)
    notebook.add(frame_tables, text="ACTION/GOTO表")

    label1 = ttk.Label(frame_tables, text="ACTION表")
    label1.pack()
    tree_action = ttk.Treeview(frame_tables, columns=list(range(len(action_table[0]))), show='headings')
    for i in range(len(action_table[0])):
        tree_action.heading(i, text=str(i))
    for row in action_table:
        tree_action.insert('', tk.END, values=row)
    tree_action.pack()

    label2 = ttk.Label(frame_tables, text="GOTO表")
    label2.pack()
    tree_goto = ttk.Treeview(frame_tables, columns=list(range(len(goto_table[0]))), show='headings')
    for i in range(len(goto_table[0])):
        tree_goto.heading(i, text=str(i))
    for row in goto_table:
        tree_goto.insert('', tk.END, values=row)
    tree_goto.pack()

    # --- 4. 规约过程页 ---
    frame_proc = ttk.Frame(notebook)
    notebook.add(frame_proc, text="规约过程")

    tree_proc = ttk.Treeview(frame_proc, columns=('栈', '状态', '符号栈', '输入串', '动作'), show='headings')
    for col in tree_proc["columns"]:
        tree_proc.heading(col, text=col)
    for row in parse_process:
        tree_proc.insert('', tk.END, values=row)
    tree_proc.pack(fill='both', expand=True)

    root.mainloop()

# 运行 GUI
build_gui()
