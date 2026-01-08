import sys
import struct
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QFileDialog, QLabel, QTextEdit, 
                             QListWidget, QListWidgetItem, QMessageBox, QSplitter, 
                             QLineEdit, QComboBox)
from PyQt6.QtGui import QAction, QFont, QColor
from PyQt6.QtCore import Qt

class EditorMultiLang(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1280, 800)
        # Dicionário de Idiomas para a Interface
        self.langs = {
            "PT": {
                "title": "Lang2ME 1.1",
                "open": "Abrir Arquivo",
                "save": "Salvar Arquivo",
                "import": "Importar JSON",
                "export": "Exportar JSON",
                "credits": "Créditos",
                "search": "🔍 Localizar:",
                "status_idle": "Aguardando arquivo...",
                "status_open": "Entradas encontradas: ",
                "size": "Tamanho: ",
                "modified": "Modificado: ",
                "msg_scan": "Blocos de texto encontrados!",
                "msg_save": "Arquivo reconstruído com sucesso!",
                "about": "Desenvolvido para tradução de jogos J2ME.\n\nAutor: Quakeman"
            },
            "EN": {
                "title": "Lang2ME 1.1",
                "open": "Open File",
                "save": "Save File",
                "import": "Import JSON",
                "export": "Export JSON",
                "credits": "Credits",
                "search": "🔍 Search:",
                "status_idle": "Waiting for file...",
                "status_open": "Entries found: ",
                "size": "Size: ",
                "modified": "Modified: ",
                "msg_scan": "Text blocks found!",
                "msg_save": "File reconstructed successfully!",
                "about": "Developed for J2ME game translation.\n\nCreator: Quakeman"
            }
        }
        self.curr_lang = "PT"
        
        self.file_structure = []
        self.all_texts = []
        self.original_texts = []
        
        self.init_ui()
        self.create_menu()
        self.update_ui_text()



    def create_menu(self):
        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu('Arquivo' if self.curr_lang == "PT" else 'File')
        
        self.open_act = QAction('Abrir', self)
        self.open_act.triggered.connect(self.auto_scan_file)
        self.file_menu.addAction(self.open_act)

        self.save_act = QAction('Salvar', self)
        self.save_act.triggered.connect(self.save_file)
        self.file_menu.addAction(self.save_act)
        
        self.file_menu.addSeparator()
        
        self.import_act = QAction('Importar JSON', self)
        self.import_act.triggered.connect(self.import_json)
        self.file_menu.addAction(self.import_act)

        self.export_act = QAction('Exportar JSON', self)
        self.export_act.triggered.connect(self.export_json)
        self.file_menu.addAction(self.export_act)

        # Menu Ajuda/Créditos
        self.help_menu = self.menubar.addMenu('Lang2ME' if self.curr_lang == "PT" else 'Sobre')
        self.credits_act = QAction('Créditos' if self.curr_lang == "PT" else 'Credits', self)
        self.credits_act.triggered.connect(self.show_credits)
        self.help_menu.addAction(self.credits_act)

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Top Bar com Busca e Seletor de Idioma
        top_layout = QHBoxLayout()
        
        self.search_label = QLabel("Localizar:")
        top_layout.addWidget(self.search_label)
        
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_list)
        top_layout.addWidget(self.search_input)
        
        top_layout.addStretch()
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Português", "English"])
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        top_layout.addWidget(self.lang_combo)
        
        main_layout.addLayout(top_layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.load_selected_text)
        self.splitter.addWidget(self.list_widget)

        editor_container = QWidget()
        editor_layout = QVBoxLayout()
        self.status_label = QLabel("")
        editor_layout.addWidget(self.status_label)

        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Consolas", 12))
        self.text_editor.textChanged.connect(self.update_text_in_memory)
        editor_layout.addWidget(self.text_editor)

        footer_layout = QHBoxLayout()
        self.size_label = QLabel("Tamanho: 0")
        self.modified_label = QLabel("Modificado: Não")
        footer_layout.addWidget(self.size_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.modified_label)
        editor_layout.addLayout(footer_layout)

        editor_container.setLayout(editor_layout)
        self.splitter.addWidget(editor_container)
        self.splitter.setStretchFactor(1, 2)
        main_layout.addWidget(self.splitter)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def change_language(self, index):
        self.curr_lang = "PT" if index == 0 else "EN"
        self.update_ui_text()

    def update_ui_text(self):
        L = self.langs[self.curr_lang]
        self.setWindowTitle(L["title"])
        self.search_label.setText(L["search"])
        self.status_label.setText(L["status_idle"] if not self.all_texts else L["status_open"] + str(len(self.all_texts)))
        self.file_menu.setTitle('Arquivo' if self.curr_lang == "PT" else 'File')
        self.open_act.setText(L["open"])
        self.save_act.setText(L["save"])
        self.import_act.setText(L["import"])
        self.export_act.setText(L["export"])
        self.credits_act.setText(L["credits"])

    def show_credits(self):
        L = self.langs[self.curr_lang]
        QMessageBox.information(self, L["credits"], f"Editor Supremo v2.0\n\n{L['about']}")

    def is_printable(self, b_arr):
        if not b_arr: return False
        try:
            text = b_arr.decode('utf-8')
            return all(32 <= ord(c) <= 255 or c in '\n\r\t' for c in text)
        except: return False

    def auto_scan_file(self):
        # Removida a obrigação de ser .bin (filtro Todos os Arquivos)
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "Todos os Arquivos (*.*);;Arquivos BIN (*.bin)")
        if not path: return
        
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.file_structure, self.all_texts = [], []
            cursor = 0
            while cursor < len(data):
                found = False
                if cursor + 2 < len(data):
                    length = struct.unpack(">H", data[cursor:cursor+2])[0]
                    start, end = cursor + 2, cursor + 2 + length
                    if end <= len(data) and length > 0:
                        potential = data[start:end]
                        if self.is_printable(potential):
                            txt = potential.decode('utf-8')
                            self.file_structure.append(['text', txt])
                            self.all_texts.append(txt)
                            cursor = end
                            found = True
                if not found:
                    b = data[cursor:cursor+1]
                    if self.file_structure and self.file_structure[-1][0] == 'data':
                        self.file_structure[-1][1] += b
                    else:
                        self.file_structure.append(['data', bytearray(b)])
                    cursor += 1
            self.original_texts = list(self.all_texts)
            self.refresh_list()
            self.update_ui_text()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def refresh_list(self, filter_text=""):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for i, text in enumerate(self.all_texts):
            if filter_text.lower() in text.lower():
                clean = text.replace("^", " ").replace("\n", " ")[:50]
                name = f"[{i:03d}] {clean}"
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, i)
                if i < len(self.original_texts) and text != self.original_texts[i]:
                    item.setBackground(QColor("#d4edda"))
                    item.setForeground(QColor("#155724"))
                    item.setText(f"✅ {name}")
                self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

    def filter_list(self):
        self.refresh_list(self.search_input.text())

    def load_selected_text(self):
        item = self.list_widget.currentItem()
        if not item: return
        idx = item.data(Qt.ItemDataRole.UserRole)
        self.text_editor.blockSignals(True)
        self.text_editor.setPlainText(self.all_texts[idx])
        self.text_editor.blockSignals(False)
        self.update_info(idx)

    def update_text_in_memory(self):
        item = self.list_widget.currentItem()
        if not item: return
        idx = item.data(Qt.ItemDataRole.UserRole)
        new_txt = self.text_editor.toPlainText()
        self.all_texts[idx] = new_txt
        is_mod = new_txt != self.original_texts[idx]
        clean = new_txt.replace("^", " ").replace("\n", " ")[:50]
        base = f"[{idx:03d}] {clean}"
        if is_mod:
            item.setBackground(QColor("#d4edda"))
            item.setForeground(QColor("#155724"))
            item.setText(f"✅ {base}")
        else:
            item.setBackground(QColor("white"))
            item.setForeground(QColor("black"))
            item.setText(base)
        self.update_info(idx)

    def update_info(self, idx):
        L = self.langs[self.curr_lang]
        size = len(self.all_texts[idx].encode('utf-8'))
        self.size_label.setText(f"{L['size']} {size} bytes")
        mod = "Sim" if self.all_texts[idx] != self.original_texts[idx] else "Não"
        self.modified_label.setText(f"{L['modified']} {mod}")

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "JSON", "", "JSON (*.json)")
        if not path: return
        with open(path, "r", encoding="utf-8") as f:
            self.all_texts = json.load(f)
        self.refresh_list()

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "JSON", "export.json", "JSON (*.json)")
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.all_texts, f, indent=4, ensure_ascii=False)

    def save_file(self):
        L = self.langs[self.curr_lang]
        path, _ = QFileDialog.getSaveFileName(self, L["save"], "MODIFIED_FILE", "Todos os Arquivos (*.*)")
        if not path: return
        try:
            text_counter = 0
            final_data = bytearray()
            for t, val in self.file_structure:
                if t == 'data': final_data.extend(val)
                else:
                    b = self.all_texts[text_counter].encode('utf-8')
                    final_data.extend(struct.pack(">H", len(b)))
                    final_data.extend(b)
                    text_counter += 1
            with open(path, "wb") as f: f.write(final_data)
            QMessageBox.information(self, "OK", L["msg_save"])
        except Exception as e: QMessageBox.critical(self, "Erro", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = EditorMultiLang()
    win.show()
    sys.exit(app.exec())
