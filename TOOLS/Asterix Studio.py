import sys
import struct
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTreeWidget, QTreeWidgetItem, QTextEdit, QLabel, 
                             QFileDialog, QMessageBox, QComboBox)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt

DARK_STYLE = """
    QMainWindow { background-color: #121212; }
    QTreeWidget { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #333; border-radius: 5px; }
    QTreeWidget::item:selected { background-color: #007acc; color: white; }
    QTextEdit { background-color: #1e1e1e; color: #9cdcfe; border: 1px solid #333; border-radius: 5px; font-family: 'Consolas'; padding: 10px; }
    QPushButton { background-color: #333; color: white; border: none; padding: 8px; border-radius: 4px; font-weight: bold; }
    QPushButton:hover { background-color: #444; }
    QPushButton#btn_save { background-color: #0e639c; }
    QComboBox { background-color: #333; color: white; border: 1px solid #444; padding: 5px; border-radius: 4px; }
    QLabel { color: #aaaaaa; }
"""

class AsterixMultiStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asterix Studio - Multi-Game Suite")
        self.resize(1150, 800)
        self.setStyleSheet(DARK_STYLE)
        
        # --- PERFIS DE JOGOS ATUALIZADOS ---
        self.game_profiles = {
            "Asterix e os Vikings": {
                "header_end": 0x278,
                "protecao_inicio": 0x2520,
                "protecao_fim": 0x992C
            },
            "Asterix Resgata Obelix": {
                "header_end": 0x278,
                "protecao_inicio": 0xCD1,
                "protecao_fim": 0x10D33
            }
        }
        
        self.current_profile = "Asterix e os Vikings"
        self.blocks = []
        self.current_idx = -1
        self.current_encoding = "utf-8"
        
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # Painel Esquerdo
        side_layout = QVBoxLayout()
        side_layout.addWidget(QLabel("PERFIL DO JOGO:"))
        self.combo_game = QComboBox()
        self.combo_game.addItems(self.game_profiles.keys())
        self.combo_game.currentTextChanged.connect(self.change_game_profile)
        side_layout.addWidget(self.combo_game)

        self.btn_open = QPushButton("📁 Abrir Arquivo")
        self.btn_open.clicked.connect(self.load_file)
        side_layout.addWidget(self.btn_open)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tipo", "Tamanho"])
        self.tree.itemSelectionChanged.connect(self.on_select)
        side_layout.addWidget(self.tree)
        
        self.btn_save = QPushButton("💾 Salvar Binário Final")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.clicked.connect(self.save_file)
        side_layout.addWidget(self.btn_save)
        main_layout.addLayout(side_layout, 1)

        # Painel Direito
        self.edit_layout = QVBoxLayout()
        self.status_header = QLabel("AGUARDANDO ARQUIVO")
        self.status_header.setStyleSheet("font-weight: bold; color: #569cd6; font-size: 14px;")
        self.edit_layout.addWidget(self.status_header)

        self.img_btns = QWidget()
        img_layout = QHBoxLayout(self.img_btns)
        self.btn_replace_img = QPushButton("🖼️ Substituir")
        self.btn_replace_img.clicked.connect(self.replace_image)
        self.btn_export_img = QPushButton("💾 Exportar PNG")
        self.btn_export_img.clicked.connect(self.export_image)
        img_layout.addWidget(self.btn_replace_img)
        img_layout.addWidget(self.btn_export_img)
        self.img_btns.setVisible(False)
        self.edit_layout.addWidget(self.img_btns)

        self.text_editor = QTextEdit()
        self.text_editor.textChanged.connect(self.auto_save_text)
        self.text_editor.setVisible(False)
        self.edit_layout.addWidget(self.text_editor)

        self.img_viewer = QLabel()
        self.img_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_viewer.setVisible(False)
        self.edit_layout.addWidget(self.img_viewer)
        
        self.edit_layout.addStretch()
        main_layout.addLayout(self.edit_layout, 3)

    def change_game_profile(self, game_name):
        self.current_profile = game_name
        self.status_header.setText(f"PERFIL: {game_name}")

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "Todos os Arquivos (*)")
        if not path: return
        
        prof = self.game_profiles[self.current_profile]
        
        with open(path, 'rb') as f:
            data = f.read()
            self.fixed_header = data[:4]
            self.blocks = []
            self.tree.clear()
            
            pointers = []
            for i in range(4, prof["header_end"], 4):
                ptr = struct.unpack('>I', data[i:i+4])[0]
                if ptr == 0 or ptr > len(data): break
                pointers.append(ptr)

            for i, start in enumerate(pointers):
                end = pointers[i+1] if i+1 < len(pointers) else len(data)
                raw = data[start:end]
                
                # Aplicação da Proteção por Offset
                if prof["protecao_inicio"] <= start <= prof["protecao_fim"]:
                    sub = "SISTEMA"
                elif b"QYP6" in raw[0:12]: sub = "QYP6"
                elif b"PNG" in raw[0:16]: sub = "PNG"
                else: sub = "TXT"
                
                content = raw
                if sub == "PNG": content = raw[4:]
                elif sub == "TXT": content = raw[2:]
                
                self.blocks.append({'type': sub, 'content': content})
                self.tree.addTopLevelItem(QTreeWidgetItem([sub, f"{len(raw)} bytes"]))

    def on_select(self):
        self.auto_save_text()
        items = self.tree.selectedItems()
        if not items: return
        self.current_idx = self.tree.indexOfTopLevelItem(items[0])
        block = self.blocks[self.current_idx]
        
        self.text_editor.setVisible(False)
        self.img_viewer.setVisible(False)
        self.img_btns.setVisible(False)

        if block['type'] == "PNG":
            self.status_header.setText("MODO: IMAGEM")
            self.img_btns.setVisible(True)
            pix = QPixmap()
            pix.loadFromData(block['content'])
            self.img_viewer.setPixmap(pix.scaled(450, 450, Qt.AspectRatioMode.KeepAspectRatio))
            self.img_viewer.setVisible(True)
        elif block['type'] == "TXT":
            self.status_header.setText(f"MODO: TEXTO")
            self.text_editor.setVisible(True)
            self.text_editor.blockSignals(True)
            self.text_editor.setPlainText(block['content'].decode(self.current_encoding, 'replace'))
            self.text_editor.blockSignals(False)
        else:
            self.status_header.setText(f"MODO: {block['type']} (PROTEGIDO)")

    def auto_save_text(self):
        if self.current_idx != -1 and self.blocks[self.current_idx]['type'] == "TXT":
            self.blocks[self.current_idx]['content'] = self.text_editor.toPlainText().encode(self.current_encoding)

    def replace_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Novo PNG", "", "*.png")
        if path:
            with open(path, 'rb') as f:
                self.blocks[self.current_idx]['content'] = f.read()
                self.on_select()

    def export_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar", f"img_{self.current_idx}.png", "PNG (*.png)")
        if path:
            with open(path, 'wb') as f:
                f.write(self.blocks[self.current_idx]['content'])

    def save_file(self):
        self.auto_save_text()
        prof = self.game_profiles[self.current_profile]
        path, _ = QFileDialog.getSaveFileName(self, "Salvar", "", "Todos os Arquivos (*)")
        if not path: return

        pool = bytearray()
        ptrs = []
        curr = prof["header_end"]
        
        for b in self.blocks:
            ptrs.append(curr)
            if b['type'] in ["SISTEMA", "QYP6"]: f = b['content']
            elif b['type'] == "PNG": f = struct.pack('>I', len(b['content'])) + b['content']
            else: f = struct.pack('>H', len(b['content'])) + b['content']
            pool.extend(f); curr += len(f)

        with open(path, 'wb') as f:
            f.write(self.fixed_header)
            for p in ptrs: f.write(struct.pack('>I', p))
            f.write(b'\x00' * (prof["header_end"] - f.tell()))
            f.write(pool)
        QMessageBox.information(self, "Sucesso", "Binário reconstruído!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = AsterixMultiStudio()
    ex.show()
    sys.exit(app.exec())
