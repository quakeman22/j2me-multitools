import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
from pathlib import Path

# Mapeamento de caracteres
CHAR_MAP = {
    0x00: " ", 0x01: "A", 0x02: "B", 0x03: "C", 0x04: "D", 0x05: "E",
    0x06: "F", 0x07: "G", 0x08: "H", 0x09: "I", 0x0A: "J", 0x0B: "K",
    0x0C: "L", 0x0D: "M", 0x0E: "N", 0x0F: "O", 0x10: "P", 0x11: "Q",
    0x12: "R", 0x13: "S", 0x14: "T", 0x15: "U", 0x16: "V", 0x17: "W",
    0x18: "X", 0x19: "Y", 0x1A: "Z", 0x1B: "a", 0x1C: "b", 0x1D: "c",
    0x1E: "d", 0x1F: "e", 0x20: "f", 0x21: "g", 0x22: "h", 0x23: "i",
    0x24: "j", 0x25: "k", 0x26: "l", 0x27: "m", 0x28: "n", 0x29: "o",
    0x2A: "p", 0x2B: "q", 0x2C: "r", 0x2D: "s", 0x2E: "t", 0x2F: "u",
    0x30: "v", 0x31: "w", 0x32: "x", 0x33: "y", 0x34: "z", 0x35: ".",
    0x36: ",", 0x37: "?", 0x38: "!", 0x39: "-", 0x3A: "+", 0x3B: ":",
    0x3C: "/", 0x3D: "1", 0x3E: "2", 0x3F: "3", 0x40: "4", 0x41: "5",
    0x42: "6", 0x43: "7", 0x44: "8", 0x45: "9", 0x46: "0", 0x47: "#",
    0x48: "*", 0x49: "<", 0x4A: ">", 0x4B: "(", 0x4C: ")", 0x4D: "\"",
    0x4E: "=", 0x4F: "%", 0x50: "'", 0x51: "^", 0x52: "_", 0x53: "&",
    0x54: "$", 0x55: "@", 0x56: "~", 0x57: "{", 0x58: "}", 0x59: "[",
    0x5A: "]", 0x5B: "|", 0x5C: ";"
}

REVERSE_CHAR_MAP = {v: k for k, v in CHAR_MAP.items()}

class TextEntry:
    def __init__(self, position, text_bytes, text):
        self.position = position
        self.text_bytes = text_bytes
        self.text = text
        self.original_length = len(text_bytes)

class GameTextEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Editor de Textos StolenIn60Secs")
        self.geometry("1000x700")
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.file_header = None
        self.raw_file_bytes = None
        self.text_entries = []
        self.original_filename = None
        self.text_widgets = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # Painel de configurações
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(fill="x", padx=10, pady=10)
        
        # Linha 1: Arquivo e Formato
        row1 = ctk.CTkFrame(config_frame)
        row1.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(row1, text="Carregar Arquivo", command=self.load_file, width=150).pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Formato:").pack(side="left", padx=(20, 5))
        self.format_var = ctk.StringVar(value="2-be")
        format_menu = ctk.CTkOptionMenu(row1, variable=self.format_var, 
                                        values=["1", "2-be", "2-le"], width=150)
        format_menu.pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Offset:").pack(side="left", padx=(20, 5))
        self.offset_var = ctk.StringVar(value="96")
        ctk.CTkEntry(row1, textvariable=self.offset_var, width=80).pack(side="left", padx=5)
        
        self.preserve_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(row1, text="Preservar header", variable=self.preserve_var).pack(side="left", padx=20)
        
        # Linha 2: Botões de ação
        row2 = ctk.CTkFrame(config_frame)
        row2.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(row2, text="Analisar", command=self.parse_texts, width=120).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Exportar Arquivo", command=self.export_file, width=120).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Exportar JSON", command=self.export_json, width=120).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Importar JSON", command=self.import_json, width=120).pack(side="left", padx=5)
        
        # Status
        self.status_label = ctk.CTkLabel(config_frame, text="Pronto", text_color="gray")
        self.status_label.pack(pady=5)
        
        # Busca
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(search_frame, text="Buscar:").pack(side="left", padx=10)
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_texts())
        ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300).pack(side="left", padx=5)
        
        self.count_label = ctk.CTkLabel(search_frame, text="0 textos")
        self.count_label.pack(side="left", padx=20)
        
        # Área de textos com scroll
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Textos")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def load_file(self):
        filename = filedialog.askopenfilename(title="Selecione o arquivo")
        if not filename:
            return
        
        try:
            with open(filename, 'rb') as f:
                self.raw_file_bytes = bytearray(f.read())
            
            self.original_filename = Path(filename).name
            offset = int(self.offset_var.get())
            
            if offset > 0 and offset <= len(self.raw_file_bytes):
                self.file_header = self.raw_file_bytes[:offset]
            
            self.status_label.configure(text=f"Arquivo carregado ({len(self.raw_file_bytes)} bytes)", 
                                       text_color="green")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar arquivo: {str(e)}")
    
    def parse_texts(self):
        if not self.raw_file_bytes:
            messagebox.showwarning("Aviso", "Carregue um arquivo primeiro")
            return
        
        try:
            self.text_entries = []
            offset = int(self.offset_var.get())
            format_type = self.format_var.get()
            pos = offset
            bytes_data = self.raw_file_bytes
            
            while pos < len(bytes_data):
                if format_type == "1":
                    if pos >= len(bytes_data):
                        break
                    text_length = bytes_data[pos]
                    header_size = 1
                elif format_type == "2-be":
                    if pos + 1 >= len(bytes_data):
                        break
                    text_length = (bytes_data[pos] << 8) | bytes_data[pos + 1]
                    header_size = 2
                else:  # 2-le
                    if pos + 1 >= len(bytes_data):
                        break
                    text_length = (bytes_data[pos + 1] << 8) | bytes_data[pos]
                    header_size = 2
                
                if text_length == 0 or text_length > 10000:
                    pos += 1
                    continue
                
                text_start = pos + header_size
                text_end = text_start + text_length
                
                if text_end > len(bytes_data):
                    break
                
                text_bytes = list(bytes_data[text_start:text_end])
                text = ''.join([CHAR_MAP.get(b, f'[{b:02X}]') for b in text_bytes])
                
                self.text_entries.append(TextEntry(pos, text_bytes, text))
                pos = text_end
            
            self.render_texts()
            self.status_label.configure(text=f"{len(self.text_entries)} textos encontrados", 
                                       text_color="green")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao analisar: {str(e)}")
    
    def render_texts(self):
        # Limpa widgets anteriores
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.text_widgets = []
        
        search_term = self.search_var.get().lower()
        filtered = [e for e in self.text_entries if search_term in e.text.lower()]
        
        self.count_label.configure(text=f"{len(filtered)} de {len(self.text_entries)} textos")
        
        if not filtered:
            ctk.CTkLabel(self.scroll_frame, text="Nenhum texto encontrado").pack(pady=20)
            return
        
        for entry in filtered:
            index = self.text_entries.index(entry)
            
            # Frame para cada texto
            text_frame = ctk.CTkFrame(self.scroll_frame)
            text_frame.pack(fill="x", padx=5, pady=5)
            
            # Header
            header = ctk.CTkFrame(text_frame)
            header.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(header, text=f"#{index + 1}", font=("Arial", 12, "bold")).pack(side="left")
            ctk.CTkLabel(header, text=f"Posição: {entry.position} | Tamanho: {len(entry.text_bytes)}", 
                        text_color="gray", font=("Arial", 10)).pack(side="right")
            
            # Campo de texto
            text_widget = ctk.CTkTextbox(text_frame, height=60, wrap="word")
            text_widget.pack(fill="x", padx=10, pady=(0, 10))
            text_widget.insert("1.0", entry.text)
            
            # Vincula evento de mudança
            text_widget.bind("<KeyRelease>", lambda e, idx=index, tw=text_widget: self.update_text(idx, tw))
            
            self.text_widgets.append((index, text_widget))
    
    def update_text(self, index, text_widget):
        new_text = text_widget.get("1.0", "end-1c")
        entry = self.text_entries[index]
        
        # Converte texto para bytes
        new_bytes = []
        for char in new_text:
            byte_val = REVERSE_CHAR_MAP.get(char, 0x00)
            new_bytes.append(byte_val)
        
        entry.text = new_text
        entry.text_bytes = new_bytes
    
    def filter_texts(self):
        self.render_texts()
    
    def export_file(self):
        if not self.text_entries:
            messagebox.showwarning("Aviso", "Nenhum texto para exportar")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".bin",
                initialfile=f"edited_{self.original_filename}" if self.original_filename else "edited_file.bin",
                filetypes=[("Arquivos binários", "*.bin"), ("Todos os arquivos", "*.*")]
            )
            
            if not filename:
                return
            
            final_bytes = bytearray()
            
            # Header
            if self.preserve_var.get() and self.file_header:
                final_bytes.extend(self.file_header)
            
            # Textos
            format_type = self.format_var.get()
            for entry in self.text_entries:
                text_length = len(entry.text_bytes)
                
                if format_type == "1":
                    final_bytes.append(text_length & 0xFF)
                elif format_type == "2-be":
                    final_bytes.append((text_length >> 8) & 0xFF)
                    final_bytes.append(text_length & 0xFF)
                else:  # 2-le
                    final_bytes.append(text_length & 0xFF)
                    final_bytes.append((text_length >> 8) & 0xFF)
                
                final_bytes.extend(entry.text_bytes)
            
            with open(filename, 'wb') as f:
                f.write(final_bytes)
            
            self.status_label.configure(text=f"Arquivo exportado ({len(final_bytes)} bytes)", 
                                       text_color="green")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
    
    def export_json(self):
        if not self.text_entries:
            messagebox.showwarning("Aviso", "Nenhum texto para exportar")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialfile=f"{Path(self.original_filename).stem}_texts.json" if self.original_filename else "texts.json",
                filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
            )
            
            if not filename:
                return
            
            json_data = [entry.text for entry in self.text_entries]
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            self.status_label.configure(text=f"JSON exportado ({len(self.text_entries)} textos)", 
                                       text_color="green")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar JSON: {str(e)}")
    
    def import_json(self):
        if not self.text_entries:
            messagebox.showwarning("Aviso", "Analise um arquivo primeiro")
            return
        
        try:
            filename = filedialog.askopenfilename(
                title="Selecione o arquivo JSON",
                filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
            )
            
            if not filename:
                return
            
            with open(filename, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            if not isinstance(json_data, list):
                raise ValueError("JSON deve ser um array")
            
            max_len = min(len(json_data), len(self.text_entries))
            
            for i in range(max_len):
                entry = self.text_entries[i]
                new_text = json_data[i]
                new_bytes = [REVERSE_CHAR_MAP.get(c, 0x00) for c in new_text]
                entry.text = new_text
                entry.text_bytes = new_bytes
            
            self.render_texts()
            self.status_label.configure(text=f"JSON importado ({max_len} textos)", 
                                       text_color="green")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao importar JSON: {str(e)}")

if __name__ == "__main__":
    app = GameTextEditor()
    app.mainloop()