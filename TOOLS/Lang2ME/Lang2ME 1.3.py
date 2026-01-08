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
        
        self.langs = {
            "PT": {
                "title": "Lang2ME 1.3 - Endian Support",
                "open": "Abrir Arquivo",
                "save": "Salvar Arquivo",
                "import": "Importar JSON",
                "export": "Exportar JSON",
                "credits": "Créditos",
                "search": "🔍 Localizar:",
                "status_idle": "Aguardando arquivo...",
                "status_open": "Entradas: ",
                "size": "Tamanho: ",
                "modified": "Modificado: ",
                "msg_save": "Arquivo salvo com sucesso!",
                "about": "Desenvolvido por Quakeman\nSuporte a Big/Little Endian adicionado."
            }
        }
        self.curr_lang = "PT"
        self.encoding = "utf-8"
        self.endian = ">" # Padrão: Big Endian (00 04)
        
        self.file_structure = []
        self.all_texts = []
        self.original_texts = []
        
        self.init_ui()
        self.create_menu()
        self.update_ui_text()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        
        # Filtro de busca
        self.search_label = QLabel("Localizar:")
        top_layout.addWidget(self.search_label)
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_list)
        top_layout.addWidget(self.search_input)
        
        top_layout.addStretch()

        # NOVO: SELETOR DE ENDIANNESS
        top_layout.addWidget(QLabel("Byte Order:"))
        self.endian_combo = QComboBox()
        self.endian_combo.addItems(["Big Endian", "Little Endian"])
        self.endian_combo.currentIndexChanged.connect(self.change_endian)
        top_layout.addWidget(self.endian_combo)

        # Seletor de Encoding
        top_layout.addWidget(QLabel("Encoding:"))
        self.enc_combo = QComboBox()
        self.enc_combo.addItems(["UTF-8", "ISO-8859-1"])
        self.enc_combo.currentIndexChanged.connect(lambda: setattr(self, 'encoding', self.enc_combo.currentText().lower()))
        top_layout.addWidget(self.enc_combo)

        main_layout.addLayout(top_layout)

        # Divisor de tela
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.load_selected_text)
        self.splitter.addWidget(self.list_widget)

        # Área de Edição
        editor_container = QWidget()
        editor_layout = QVBoxLayout()
        self.status_label = QLabel("")
        editor_layout.addWidget(self.status_label)
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Consolas", 12))
        self.text_editor.textChanged.connect(self.update_text_in_memory)
        editor_layout.addWidget(self.text_editor)

        # Rodapé
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

    def change_endian(self, index):
        # > é Big Endian (00 04), < é Little Endian (04 00)
        self.endian = ">" if index == 0 else "<"
        QMessageBox.information(self, "Aviso", "Ordem de bytes alterada. Abra o arquivo novamente para re-escanear corretamente.")

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Arquivo')
        
        self.open_act = QAction('Abrir Binário', self)
        self.open_act.triggered.connect(self.auto_scan_file)
        file_menu.addAction(self.open_act)

        self.save_act = QAction('Salvar Binário', self)
        self.save_act.triggered.connect(self.save_file)
        file_menu.addAction(self.save_act)
        
        file_menu.addSeparator()
        
        self.import_act = QAction('Importar JSON', self)
        self.import_act.triggered.connect(self.import_json)
        file_menu.addAction(self.import_act)

        self.export_act = QAction('Exportar JSON', self)
        self.export_act.triggered.connect(self.export_json)
        file_menu.addAction(self.export_act)

    def is_printable(self, b_arr):
        try:
            text = b_arr.decode(self.encoding)
            return all(32 <= ord(c) <= 255 or c in '\n\r\t' for c in text)
        except: return False

    def auto_scan_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "Todos (*.*)")
        if not path: return
        try:
            with open(path, "rb") as f: data = f.read()
            self.file_structure, self.all_texts = [], []
            cursor = 0
            while cursor < len(data):
                found = False
                if cursor + 2 < len(data):
                    # USA O ENDIAN SELECIONADO ( >H ou <H )
                    fmt = f"{self.endian}H"
                    length = struct.unpack(fmt, data[cursor:cursor+2])[0]
                    start, end = cursor + 2, cursor + 2 + length
                    if end <= len(data) and length > 0:
                        potential = data[start:end]
                        if self.is_printable(potential):
                            txt = potential.decode(self.encoding)
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
        except Exception as e: QMessageBox.critical(self, "Erro", str(e))

    def save_file(self):
        if not self.file_structure: return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar", "MODIFIED.bin", "Todos (*.*)")
        if not path: return
        try:
            text_counter, final_data = 0, bytearray()
            fmt = f"{self.endian}H"
            for t, val in self.file_structure:
                if t == 'data': final_data.extend(val)
                else:
                    b = self.all_texts[text_counter].encode(self.encoding)
                    # GRAVA NO ENDIAN SELECIONADO
                    final_data.extend(struct.pack(fmt, len(b)))
                    final_data.extend(b)
                    text_counter += 1
            with open(path, "wb") as f: f.write(final_data)
            QMessageBox.information(self, "OK", self.langs[self.curr_lang]["msg_save"])
        except Exception as e: QMessageBox.critical(self, "Erro", str(e))

    # --- Métodos de UI repetidos do anterior para manter funcionalidade ---
    def update_ui_text(self):
        L = self.langs[self.curr_lang]
        self.setWindowTitle(L["title"])
        self.status_label.setText(L["status_open"] + str(len(self.all_texts)) if self.all_texts else L["status_idle"])

    def refresh_list(self, filter_text=""):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for i, text in enumerate(self.all_texts):
            if filter_text.lower() in text.lower():
                item = QListWidgetItem(f"[{i:03d}] {text.replace('\n', ' ')[:50]}")
                item.setData(Qt.ItemDataRole.UserRole, i)
                if i < len(self.original_texts) and text != self.original_texts[i]:
                    item.setBackground(QColor("#d4edda"))
                self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

    def filter_list(self): self.refresh_list(self.search_input.text())
    
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
        self.all_texts[idx] = self.text_editor.toPlainText()
        self.update_info(idx)

    def update_info(self, idx):
        size = len(self.all_texts[idx].encode(self.encoding))
        self.size_label.setText(f"Tamanho: {size} bytes")

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "JSON", "", "JSON (*.json)")
        if path:
            with open(path, "r", encoding="utf-8") as f: self.all_texts = json.load(f)
            self.refresh_list()

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "JSON", "export.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f: json.dump(self.all_texts, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = EditorMultiLang()
    win.show()
    sys.exit(app.exec())
