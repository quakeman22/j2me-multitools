import sys
import struct
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QFileDialog, QLabel, QTextEdit, 
                             QListWidget, QListWidgetItem, QMessageBox, QSplitter, QLineEdit)
from PyQt6.QtGui import QAction, QFont, QColor
from PyQt6.QtCore import Qt

class SupremoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lang2Me 1.0")
        self.setMinimumSize(1100, 700)
        
        # Memória de dados
        self.file_structure = []  # Lista: ['data', bytes] ou ['text', string]
        self.all_texts = []       # Textos atuais (editáveis)
        self.original_texts = []  # Cópia fiel para comparação
        
        self.init_ui()
        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&Arquivo')
        
        open_action = QAction('Abrir Arquivo', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.auto_scan_bin)
        file_menu.addAction(open_action)

        save_action = QAction('Salvar', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_bin)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        import_json = QAction('Importar JSON', self)
        import_json.triggered.connect(self.import_json)
        file_menu.addAction(import_json)

        export_json = QAction('Exportar JSON', self)
        export_json.triggered.connect(self.export_json)
        file_menu.addAction(export_json)

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Barra de Busca e Filtro
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Localizar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filtrar textos...")
        self.search_input.textChanged.connect(self.filter_list)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Divisor Principal
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Esquerda: Lista de Textos
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.load_selected_text)
        self.splitter.addWidget(self.list_widget)

        # Direita: Área de Edição
        editor_container = QWidget()
        editor_layout = QVBoxLayout()
        
        self.status_label = QLabel("Aguardando arquivo...")
        self.status_label.setStyleSheet("font-weight: bold; color: #34495e;")
        editor_layout.addWidget(self.status_label)

        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Consolas", 12))
        self.text_editor.textChanged.connect(self.update_text_in_memory)
        editor_layout.addWidget(self.text_editor)

        # Rodapé de Info
        info_layout = QHBoxLayout()
        self.size_label = QLabel("Tamanho: 0 bytes")
        self.modified_label = QLabel("Modificado: Não")
        info_layout.addWidget(self.size_label)
        info_layout.addStretch()
        info_layout.addWidget(self.modified_label)
        editor_layout.addLayout(info_layout)

        editor_container.setLayout(editor_layout)
        self.splitter.addWidget(editor_container)

        self.splitter.setStretchFactor(1, 2)
        main_layout.addWidget(self.splitter)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def is_printable(self, b_arr):
        """Para identificar se os bytes são texto válido do jogo."""
        if not b_arr: return False
        try:
            text = b_arr.decode('utf-8')
            # Filtro rigoroso: aceita caracteres latinos, números, pontuação e tags do jogo (^, #, *, ~)
            return all(32 <= ord(c) <= 255 or c in '\n\r\t' for c in text)
        except:
            return False

    def auto_scan_bin(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "Arquivo BIN (*)")
        if not path: return
        
        try:
            with open(path, "rb") as f:
                data = f.read()

            self.file_structure = []
            self.all_texts = []
            cursor = 0
            
            while cursor < len(data):
                found_text = False
                # Padrão J2ME Gameloft: [2 bytes tamanho BIG ENDIAN][Texto]
                if cursor + 2 < len(data):
                    length = struct.unpack(">H", data[cursor:cursor+2])[0]
                    start, end = cursor + 2, cursor + 2 + length
                    
                    if end <= len(data) and length > 0:
                        potential_bytes = data[start:end]
                        if self.is_printable(potential_bytes):
                            text_str = potential_bytes.decode('utf-8')
                            self.file_structure.append(['text', text_str])
                            self.all_texts.append(text_str)
                            cursor = end
                            found_text = True
                
                if not found_text:
                    byte = data[cursor:cursor+1]
                    if self.file_structure and self.file_structure[-1][0] == 'data':
                        self.file_structure[-1][1] += byte
                    else:
                        self.file_structure.append(['data', bytearray(byte)])
                    cursor += 1

            self.original_texts = list(self.all_texts) # Salva estado original
            self.refresh_list()
            self.status_label.setText(f"Arquivo Aberto. Encontradas {len(self.all_texts)} entradas.")
            QMessageBox.information(self, "Scanner", f"Sucesso! Encontrados {len(self.all_texts)} blocos de texto.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha no scan: {e}")

    def refresh_list(self, filter_text=""):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        
        for i, text in enumerate(self.all_texts):
            if filter_text.lower() in text.lower():
                # Limpa tags para o preview
                clean_preview = text.replace("^", " ").replace("\n", " ")[:50]
                display_name = f"[{i:03d}] {clean_preview}"
                
                item = QListWidgetItem(display_name)
                item.setData(Qt.ItemDataRole.UserRole, i)
                
                # DESTRIQUE VISUAL: Se modificado, muda cor e põe check
                if i < len(self.original_texts) and text != self.original_texts[i]:
                    item.setBackground(QColor("#9b9c3a")) # Verde Suave
                    item.setForeground(QColor("#913838")) # Verde Escuro
                    item.setText(f"✅ {display_name}")
                
                self.list_widget.addItem(item)
        
        self.list_widget.blockSignals(False)

    def filter_list(self):
        self.refresh_list(self.search_input.text())

    def load_selected_text(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        real_idx = item.data(Qt.ItemDataRole.UserRole)
        self.status_label.setText(f"Editando Bloco #{real_idx}")
        
        self.text_editor.blockSignals(True)
        self.text_editor.setPlainText(self.all_texts[real_idx])
        self.text_editor.blockSignals(False)
        self.update_info_panel(real_idx)

    def update_text_in_memory(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        real_idx = item.data(Qt.ItemDataRole.UserRole)
        new_text = self.text_editor.toPlainText()
        self.all_texts[real_idx] = new_text
        
        # Atualização dinâmica do estilo na lista
        is_modified = new_text != self.original_texts[real_idx]
        
        # Atualiza o item da lista visualmente sem dar refresh em tudo
        clean_preview = new_text.replace("^", " ").replace("\n", " ")[:50]
        base_text = f"[{real_idx:03d}] {clean_preview}"
        
        if is_modified:
            item.setBackground(QColor("#d4edda"))
            item.setForeground(QColor("#155724"))
            item.setText(f"✅ {base_text}")
        else:
            item.setBackground(QColor("white"))
            item.setForeground(QColor("black"))
            item.setText(base_text)
            
        self.update_info_panel(real_idx)

    def update_info_panel(self, idx):
        size = len(self.all_texts[idx].encode('utf-8'))
        self.size_label.setText(f"Tamanho: {size} bytes")
        mod = "Sim" if self.all_texts[idx] != self.original_texts[idx] else "Não"
        self.modified_label.setText(f"Modificado: {mod}")

    def export_json(self):
        if not self.all_texts: return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar JSON", "traducao_br.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.all_texts, f, indent=4, ensure_ascii=False)

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar JSON", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                imported_data = json.load(f)
            
            if len(imported_data) != len(self.all_texts):
                QMessageBox.warning(self, "Aviso", "O JSON tem um número de frases diferente do BIN!")
            
            self.all_texts = imported_data
            self.refresh_list()
            QMessageBox.information(self, "Sucesso", "Tradução importada e destacada na lista!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar JSON: {e}")

    def save_bin(self):
        if not self.all_texts: return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar BIN", "TRADUZIDO.bin", "BIN (*)")
        if not path: return
        
        try:
            text_counter = 0
            final_data = bytearray()
            
            for type_part, val in self.file_structure:
                if type_part == 'data':
                    final_data.extend(val)
                else:
                    txt_bytes = self.all_texts[text_counter].encode('utf-8')
                    # Grava novo tamanho e novo texto
                    final_data.extend(struct.pack(">H", len(txt_bytes)))
                    final_data.extend(txt_bytes)
                    text_counter += 1
            
            with open(path, "wb") as f:
                f.write(final_data)
            QMessageBox.information(self, "Sucesso", "Arquivo BIN reconstruído com perfeição!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Estilo moderno
    window = SupremoEditor()
    window.show()
    sys.exit(app.exec())
