import customtkinter as ctk
from tkinter import filedialog, messagebox
import struct
from typing import List, Optional
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TextEntry:
    def __init__(self, id: int, size_pos: int, position: int, text: str, length: int):
        self.id = id
        self.size_pos = size_pos
        self.position = position
        self.text = text
        self.original_text = text
        self.length = length


class Block:
    def __init__(self, index: int, position: int, header: int, texts: List[TextEntry]):
        self.index = index
        self.position = position
        self.header = header
        self.texts = texts
        self.size = 4 + sum(2 + t.length for t in texts)


class GameTextEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Editor de Textos de Jogos")
        self.geometry("1200x800")
        
        self.file_data: Optional[bytes] = None
        self.blocks: List[Block] = []
        self.current_block: Optional[Block] = None
        self.current_text: Optional[TextEntry] = None
        self.current_encoding = "utf-8"
        self.file_path = ""
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame principal dividido em 3 colunas
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ===== PAINEL ESQUERDO - Configurações =====
        left_frame = ctk.CTkFrame(self, width=300)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_frame.grid_propagate(False)
        
        ctk.CTkLabel(left_frame, text="⚙️ Configurações", font=("Arial", 18, "bold")).pack(pady=10)
        
        # Botão Abrir Arquivo
        self.btn_open = ctk.CTkButton(left_frame, text="📁 Abrir Arquivo", command=self.open_file, height=40)
        self.btn_open.pack(pady=5, padx=20, fill="x")
        
        # Endereço da Tabela
        ctk.CTkLabel(left_frame, text="Endereço da Tabela (hex):").pack(pady=(15,5), padx=20, anchor="w")
        self.entry_table_start = ctk.CTkEntry(left_frame, placeholder_text="0x1000")
        self.entry_table_start.pack(pady=5, padx=20, fill="x")
        self.entry_table_start.insert(0, "0x1000")
        
        # Número de Blocos
        ctk.CTkLabel(left_frame, text="Número de Blocos:").pack(pady=(10,5), padx=20, anchor="w")
        self.entry_num_blocks = ctk.CTkEntry(left_frame, placeholder_text="10")
        self.entry_num_blocks.pack(pady=5, padx=20, fill="x")
        self.entry_num_blocks.insert(0, "10")
        
        # Botão Carregar Textos
        self.btn_load = ctk.CTkButton(left_frame, text="📖 Carregar Textos", command=self.load_texts, 
                                       height=40, fg_color="#2fa572", hover_color="#248a5e")
        self.btn_load.pack(pady=15, padx=20, fill="x")
        
        # Encoding
        ctk.CTkLabel(left_frame, text="Codificação:").pack(pady=(10,5), padx=20, anchor="w")
        self.encoding_var = ctk.StringVar(value="UTF-8")
        self.combo_encoding = ctk.CTkComboBox(
            left_frame, 
            values=["UTF-8", "ASCII", "Shift_JIS", "Latin-1"],
            variable=self.encoding_var,
            command=self.on_encoding_changed
        )
        self.combo_encoding.pack(pady=5, padx=20, fill="x")
        
        # Seleção de Bloco
        ctk.CTkLabel(left_frame, text="Bloco Atual:").pack(pady=(15,5), padx=20, anchor="w")
        self.combo_blocks = ctk.CTkComboBox(left_frame, values=["Nenhum"], command=self.on_block_selected)
        self.combo_blocks.pack(pady=5, padx=20, fill="x")
        
        # Status
        ctk.CTkLabel(left_frame, text="Status:", font=("Arial", 12, "bold")).pack(pady=(20,5), padx=20, anchor="w")
        self.lbl_status = ctk.CTkLabel(left_frame, text="Nenhum arquivo carregado", 
                                        wraplength=260, justify="left")
        self.lbl_status.pack(pady=5, padx=20, anchor="w")
        
        # Botão Salvar
        self.btn_save = ctk.CTkButton(left_frame, text="💾 Salvar Como", command=self.save_file,
                                       height=40, fg_color="#d97706", hover_color="#b45309")
        self.btn_save.pack(side="bottom", pady=20, padx=20, fill="x")
        
        # ===== PAINEL CENTRAL - Lista de Textos =====
        center_frame = ctk.CTkFrame(self)
        center_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        center_frame.grid_rowconfigure(1, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(center_frame, text="📝 Lista de Textos", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=10)
        
        # Lista de textos com scrollbar
        self.text_listbox = ctk.CTkTextbox(center_frame, width=400, font=("Courier", 11))
        self.text_listbox.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.text_listbox.bind("<Button-1>", self.on_text_selected)
        
        # ===== PAINEL DIREITO - Editor =====
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(right_frame, text="✏️ Editor", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=10)
        
        # Contador de bytes
        self.lbl_counter = ctk.CTkLabel(right_frame, text="0 bytes", font=("Arial", 12))
        self.lbl_counter.grid(row=0, column=0, pady=10, padx=10, sticky="e")
        
        # Editor de texto
        self.text_editor = ctk.CTkTextbox(right_frame, width=450, font=("Consolas", 12), wrap="word")
        self.text_editor.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.text_editor.bind("<KeyRelease>", self.update_counter)
        
        # Botões de ação
        action_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        action_frame.grid(row=2, column=0, pady=(0,10), padx=10, sticky="ew")
        action_frame.grid_columnconfigure((0,1), weight=1)
        
        self.btn_apply = ctk.CTkButton(action_frame, text="✅ Aplicar Mudanças", command=self.apply_changes,
                                        height=40, fg_color="#16a34a", hover_color="#15803d")
        self.btn_apply.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.btn_reset = ctk.CTkButton(action_frame, text="↺ Resetar", command=self.reset_text,
                                        height=40, fg_color="#dc2626", hover_color="#b91c1c")
        self.btn_reset.grid(row=0, column=1, padx=5, sticky="ew")
    
    def open_file(self):
        file_path = filedialog.askopenfilename(title="Abrir arquivo do jogo")
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    self.file_data = bytearray(f.read())
                self.file_path = file_path
                self.lbl_status.configure(text=f"Arquivo carregado:\n{os.path.basename(file_path)}")
                messagebox.showinfo("Sucesso", "Arquivo aberto com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao abrir arquivo:\n{str(e)}")
    
    def load_texts(self):
        if self.file_data is None:
            messagebox.showwarning("Aviso", "Abra um arquivo primeiro!")
            return
        
        try:
            table_start = int(self.entry_table_start.get().replace("0x", ""), 16)
            num_blocks = int(self.entry_num_blocks.get())
            self.blocks.clear()
            
            # Ler ponteiros
            pointers = []
            for i in range(num_blocks):
                pos = table_start + i * 2
                if pos + 2 > len(self.file_data):
                    break
                ptr = (self.file_data[pos] << 8) | self.file_data[pos + 1]
                offset = 2 + (2 * i)
                pointers.append(ptr + offset)
            
            # Ler blocos
            for i in range(len(pointers)):
                start = pointers[i]
                end = pointers[i + 1] if i + 1 < len(pointers) else len(self.file_data)
                
                if start + 4 >= len(self.file_data) or end <= start:
                    continue
                
                header = struct.unpack('>I', self.file_data[start:start+4])[0]
                texts = self.read_text_block(start + 4, end)
                
                if texts:
                    self.blocks.append(Block(i, start, header, texts))
            
            # Atualizar UI
            block_names = [f"Bloco {i} ({len(b.texts)} textos)" for i, b in enumerate(self.blocks)]
            self.combo_blocks.configure(values=block_names if block_names else ["Nenhum"])
            if block_names:
                self.combo_blocks.set(block_names[0])
                self.current_block = self.blocks[0]
                self.update_text_list()
            
            self.lbl_status.configure(text=f"{len(self.blocks)} blocos carregados!")
            messagebox.showinfo("Sucesso", f"{len(self.blocks)} blocos carregados com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar textos:\n{str(e)}")
    
    def read_text_block(self, start: int, end: int) -> List[TextEntry]:
        texts = []
        pos = start
        text_id = 0
        
        while pos + 2 < end and pos + 2 < len(self.file_data):
            length = (self.file_data[pos] << 8) | self.file_data[pos + 1]
            if length == 0 or length == 0xFFFF or length > 5000:
                break
            
            text_start = pos + 2
            text_end = text_start + length
            
            if text_end > len(self.file_data) or text_end > end:
                break
            
            text = self.bytes_to_string(self.file_data[text_start:text_end])
            texts.append(TextEntry(text_id, pos, text_start, text, length))
            text_id += 1
            pos = text_end
        
        return texts
    
    def update_text_list(self):
        self.text_listbox.delete("1.0", "end")
        if self.current_block:
            for t in self.current_block.texts:
                preview = t.text.replace("\n", " ").replace("\r", "")
                if len(preview) > 50:
                    preview = preview[:47] + "..."
                self.text_listbox.insert("end", f"#{t.id} ({t.length}b) → {preview}\n")
    
    def on_block_selected(self, choice):
        idx = int(choice.split()[1])
        self.current_block = self.blocks[idx]
        self.update_text_list()
    
    def on_text_selected(self, event):
        if not self.current_block:
            return
        
        try:
            index = self.text_listbox.index("@%s,%s" % (event.x, event.y))
            line = int(index.split('.')[0]) - 1
            
            if 0 <= line < len(self.current_block.texts):
                self.current_text = self.current_block.texts[line]
                self.text_editor.delete("1.0", "end")
                self.text_editor.insert("1.0", self.current_text.text)
                self.update_counter()
        except:
            pass
    
    def apply_changes(self):
        if not self.current_text or not self.current_block:
            messagebox.showwarning("Aviso", "Selecione um texto primeiro!")
            return
        
        new_text = self.text_editor.get("1.0", "end-1c")
        new_bytes = self.string_to_bytes(new_text)
        old_length = self.current_text.length
        new_length = len(new_bytes)
        delta = new_length - old_length
        text_index = self.current_block.texts.index(self.current_text)
        
        if delta != 0:
            start_of_data = self.current_text.position + old_length
            bytes_to_move = len(self.file_data) - start_of_data
            
            if delta > 0:
                # Expandir array
                self.file_data.extend(b'\x00' * delta)
            
            # Mover dados
            self.file_data[start_of_data + delta:start_of_data + delta + bytes_to_move] = \
                self.file_data[start_of_data:start_of_data + bytes_to_move]
            
            # Atualizar posições dos textos seguintes
            for i in range(text_index + 1, len(self.current_block.texts)):
                t = self.current_block.texts[i]
                t.size_pos += delta
                t.position += delta
            
            self.current_block.size += delta
            self.repoint_subsequent_blocks(self.blocks.index(self.current_block), delta)
        
        # Escrever novo tamanho e texto
        self.file_data[self.current_text.size_pos] = (new_length >> 8) & 0xFF
        self.file_data[self.current_text.size_pos + 1] = new_length & 0xFF
        self.file_data[self.current_text.position:self.current_text.position + new_length] = new_bytes
        
        # Atualizar objeto
        self.current_text.text = new_text
        self.current_text.length = new_length
        
        self.update_text_list()
        messagebox.showinfo("Sucesso", f"Aplicado! Delta: {delta:+d} bytes")
    
    def repoint_subsequent_blocks(self, start_idx: int, delta: int):
        if len(self.blocks) <= 1:
            return
        
        try:
            table_start = int(self.entry_table_start.get().replace("0x", ""), 16)
        except:
            messagebox.showerror("Erro", "Endereço da tabela inválido")
            return
        
        # Atualizar posições dos blocos
        for i in range(start_idx + 1, len(self.blocks)):
            self.blocks[i].position += delta
        
        # Reescrever ponteiros
        for i in range(start_idx + 1, len(self.blocks)):
            b = self.blocks[i]
            offset = 2 + (2 * i)
            ptr = b.position - offset
            
            if ptr < 0 or ptr > 0xFFFF:
                messagebox.showerror("Erro", f"Ponteiro fora do limite: {ptr:04X}")
                return
            
            pos = table_start + i * 2
            self.file_data[pos] = (ptr >> 8) & 0xFF
            self.file_data[pos + 1] = ptr & 0xFF
        
        # Truncar arquivo
        if self.blocks:
            last_block = self.blocks[-1]
            required_size = last_block.position + last_block.size
            self.file_data = self.file_data[:required_size]
    
    def reset_text(self):
        if self.current_text:
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", self.current_text.original_text)
            self.update_counter()
    
    def save_file(self):
        if self.file_data is None:
            messagebox.showwarning("Aviso", "Não há dados para salvar!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".bin",
            filetypes=[("Todos os arquivos", "*.*"), ("Arquivos binários", "*.bin")]
        )
        
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(self.file_data)
                messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
                self.lbl_status.configure(text=f"Salvo:\n{os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")
    
    def bytes_to_string(self, data: bytes) -> str:
        encodings = {
            "UTF-8": "utf-8",
            "ASCII": "ascii",
            "Shift_JIS": "shift_jis",
            "Latin-1": "latin-1"
        }
        try:
            return data.decode(encodings.get(self.current_encoding, "utf-8"))
        except:
            return data.decode("utf-8", errors="replace")
    
    def string_to_bytes(self, text: str) -> bytes:
        encodings = {
            "UTF-8": "utf-8",
            "ASCII": "ascii",
            "Shift_JIS": "shift_jis",
            "Latin-1": "latin-1"
        }
        try:
            return text.encode(encodings.get(self.current_encoding, "utf-8"))
        except:
            return text.encode("utf-8", errors="replace")
    
    def on_encoding_changed(self, choice):
        self.current_encoding = choice
    
    def update_counter(self, event=None):
        if self.current_text:
            text = self.text_editor.get("1.0", "end-1c")
            byte_count = len(self.string_to_bytes(text))
            self.lbl_counter.configure(text=f"{byte_count} bytes")


if __name__ == "__main__":
    app = GameTextEditor()
    app.mainloop()