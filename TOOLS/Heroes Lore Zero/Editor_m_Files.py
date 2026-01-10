import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QScrollArea, QFileDialog, QMessageBox, QFrame)
from PyQt6.QtCore import Qt

class TextBlock(QFrame):
    def __init__(self, index, content, size):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.original_content = content.lower()
        self.index = index
        self.setStyleSheet("background-color: #ffffff; border-radius: 5px; margin: 2px; border: 1px solid #ddd;")
        
        layout = QHBoxLayout()
        
        # ID e Tamanho
        self.lbl_info = QLabel(f"ID: {index:03} | {size} bytes")
        self.lbl_info.setFixedWidth(120)
        self.lbl_info.setStyleSheet("font-weight: bold; color: #555; border: none;")
        
        # Campo de edição
        self.edit = QLineEdit(content)
        self.edit.setStyleSheet("padding: 8px; border: 1px solid #ccc; background: #f9f9f9;")
        
        layout.addWidget(self.lbl_info)
        layout.addWidget(self.edit)
        self.setLayout(layout)

class J2MEPyQtEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemini J2ME Editor PRO - Barra de Busca")
        self.resize(1100, 850)
        self.setStyleSheet("QMainWindow { background-color: #f5f5f5; }")

        self.raw_data = bytearray()
        self.table_offset = 0
        self.text_start_offset = 0
        self.blocks = []

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Barra de Ferramentas Principal ---
        toolbar = QHBoxLayout()
        btn_open = QPushButton("📂 Abrir Binário")
        btn_open.clicked.connect(self.load_and_scan)
        
        btn_export = QPushButton("📤 Exportar JSON")
        btn_export.clicked.connect(self.export_json)
        
        btn_import = QPushButton("📥 Importar JSON")
        btn_import.clicked.connect(self.import_json)
        
        btn_save = QPushButton("💾 Salvar Novo .bin")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.save_bin)

        for btn in [btn_open, btn_export, btn_import, btn_save]:
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toolbar.addWidget(btn)
        
        main_layout.addLayout(toolbar)

        # --- BARRA DE PROCURA ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Procurar texto ou ID...")
        self.search_input.setFixedHeight(35)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding-left: 10px;
                border: 2px solid #3498db;
                border-radius: 15px;
                background: white;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_texts)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Status
        self.status_lbl = QLabel("Aguardando ficheiro...")
        self.status_lbl.setStyleSheet("color: #7f8c8d; font-style: italic;")
        main_layout.addWidget(self.status_lbl)

        # Área de Rolagem
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        
        main_layout.addWidget(self.scroll)

    def filter_texts(self):
        """Lógica de procura em tempo real"""
        query = self.search_input.text().lower()
        for block in self.blocks:
            # Verifica se a query está no conteúdo original, no conteúdo atual ou no ID
            text_match = query in block.edit.text().lower()
            id_match = query in str(block.index)
            
            if text_match or id_match:
                block.show()
            else:
                block.hide()

    def load_and_scan(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Binário", "", "Binary Files (*.bin *.dat);;All Files (*)")
        if not file_path: return

        with open(file_path, "rb") as f:
            self.raw_data = bytearray(f.read())

        # Lógica de varredura (Mantida conforme o seu ficheiro J2ME)
        first_text = self.raw_data.find(b'|[')
        if first_text == -1:
            QMessageBox.critical(self, "Erro", "Marcador '|[' não encontrado.")
            return

        found_lens = []
        ptr = first_text
        while ptr < len(self.raw_data) and len(found_lens) < 20:
            end = self.raw_data.find(b'\x00', ptr)
            if end == -1: break
            found_lens.append(end - ptr)
            ptr = end + 1

        for search_ptr in range(0, first_text):
            if list(self.raw_data[search_ptr : search_ptr + len(found_lens)]) == found_lens:
                self.table_offset = search_ptr
                self.text_start_offset = first_text
                self.populate_ui()
                self.status_lbl.setText(f"Estrutura mapeada com sucesso em {hex(search_ptr)}!")
                return
        
        QMessageBox.critical(self, "Erro", "Não foi possível validar a tabela de tamanhos.")

    def populate_ui(self):
        for i in reversed(range(self.scroll_layout.count())): 
            self.scroll_layout.itemAt(i).widget().setParent(None)
        self.blocks = []

        curr_txt = self.text_start_offset
        num_strings = self.text_start_offset - self.table_offset
        if self.raw_data[self.text_start_offset - 1] == 0: num_strings -= 1

        for i in range(num_strings):
            size = self.raw_data[self.table_offset + i]
            if size == 0 and i > 0: break
            
            content = self.raw_data[curr_txt : curr_txt + size].decode('iso-8859-1', errors='replace')
            block = TextBlock(i, content, size)
            self.scroll_layout.addWidget(block)
            self.blocks.append(block)
            curr_txt += size + 1

    def export_json(self):
        if not self.blocks: return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar JSON", "", "JSON Files (*.json)")
        if not path: return
        data = {i: b.edit.text() for i, b in enumerate(self.blocks)}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        QMessageBox.information(self, "Sucesso", "JSON exportado com sucesso!")

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar JSON", "", "JSON Files (*.json)")
        if not path: return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for i, block in enumerate(self.blocks):
            if str(i) in data:
                block.edit.setText(data[str(i)])
        QMessageBox.information(self, "Sucesso", "Textos importados do JSON!")

    def save_bin(self):
        if not self.blocks: return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Binário", "", "Binary Files (*.bin)")
        if not path: return

        new_file = bytearray(self.raw_data[:self.table_offset])
        for b in self.blocks:
            new_file.append(len(b.edit.text().encode('iso-8859-1')))
            
        old_table_end = self.table_offset + len(self.blocks)
        new_file.extend(self.raw_data[old_table_end : self.text_start_offset])

        for b in self.blocks:
            new_file.extend(b.edit.text().encode('iso-8859-1'))
            new_file.append(0)

        with open(path, "wb") as f:
            f.write(new_file)
        QMessageBox.information(self, "Sucesso", "Binário reconstruído e salvo!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = J2MEPyQtEditor()
    window.show()
    sys.exit(app.exec())
