import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import struct
import os

class GloftLOSTReader:
    def __init__(self):
        self.byteSS_b = [None, None]
        self.shortSS_b = [None, None]
    
    def read_pak(self, filename):
        """Lê um arquivo PAK e retorna a lista de strings"""
        try:
            with open(filename, 'rb') as f:
                return self._read_pak_stream(f)
        except Exception as e:
            raise Exception(f"Erro ao ler arquivo: {str(e)}")
    
    def _read_pak_stream(self, stream):
        num = struct.unpack('B', stream.read(1))[0]
        num += struct.unpack('B', stream.read(1))[0] << 8
        
        len1_bytes = stream.read(4)
        len1 = struct.unpack('<I', len1_bytes)[0]
        
        len2_bytes = stream.read(4)
        len2 = struct.unpack('<I', len2_bytes)[0]
        
        len3_bytes = stream.read(4)
        len3 = struct.unpack('<I', len3_bytes)[0]
        
        strs = stream.read(len2)
        offs = stream.read(len3 - len2)
        
        self._void_a_int_byteS_byteS(0, strs, offs)
        
        strings = []
        for i in range(len(self.shortSS_b[0])):
            s = ""
            byte_data = self._byteS_a_int(i)
            if byte_data:
                try:
                    # Remove o byte nulo do final e decodifica
                    if byte_data.endswith(b'\x00'):
                        byte_data = byte_data[:-1]
                    s = byte_data.decode('ISO-8859-1')
                except UnicodeDecodeError:
                    # Fallback para latin-1 se UTF-8 falhar
                    try:
                        s = byte_data.decode('latin-1')
                    except:
                        s = str(byte_data)
            strings.append(s)
        
        return strings
    
    def _byteS_a_int(self, i):
        if (self.byteSS_b[0] is not None and i >= 0 and 
            i < len(self.shortSS_b[0])):
            
            j = self.shortSS_b[0][i - 1] if i != 0 else 0
            k = (self.shortSS_b[0][i] - j - 1)
            
            if k == 0:
                return None
            
            # Extrai os bytes diretamente do array
            start_pos = j
            end_pos = j + k
            if end_pos <= len(self.byteSS_b[0]):
                return self.byteSS_b[0][start_pos:end_pos]
            else:
                return None
        else:
            return b' '
    
    def _void_a_int_byteS_byteS(self, i, abyte0, abyte1):
        self.byteSS_b[i] = abyte0
        if abyte1:
            j = struct.unpack('<H', abyte1[0:2])[0]
            self.shortSS_b[i] = [0] * j
            
            for k in range(j):
                start_idx = k * 2 + 2
                if start_idx + 1 < len(abyte1):
                    self.shortSS_b[i][k] = struct.unpack('<H', 
                        abyte1[start_idx:start_idx+2])[0]


class GloftLOSTWriter:
    def write_pak(self, strings, filename):
        """Escreve uma lista de strings em um arquivo PAK"""
        try:
            with open(filename, 'wb') as f:
                self._write_pak_stream(strings, f)
        except Exception as e:
            raise Exception(f"Erro ao escrever arquivo: {str(e)}")
    
    def _write_pak_stream(self, strings, stream):
        str_baos = bytearray()
        off_baos = bytearray()
        
        off_baos.extend(struct.pack('<H', len(strings)))
        
        count = 0
        for s in strings:
            if s != "":
                try:
                    # Codifica para UTF-8 e adiciona byte nulo
                    bytes_data = s.encode('ISO-8859-1')
                    data = bytes_data + b'\x00'
                    str_baos.extend(data)
                    count += len(data)
                except UnicodeEncodeError:
                    # Fallback para latin-1
                    bytes_data = s.encode('latin-1')
                    data = bytes_data + b'\x00'
                    str_baos.extend(data)
                    count += len(data)
            else:
                str_baos.extend(b'\x00')
                count += 1
            
            off_baos.extend(struct.pack('<H', count))
        
        # Escreve o cabeçalho
        stream.write(struct.pack('<H', 3))  # num
        stream.write(struct.pack('<I', 0))  # len1
        stream.write(struct.pack('<I', len(str_baos)))  # len2
        stream.write(struct.pack('<I', len(str_baos) + len(off_baos)))  # len3
        stream.write(str_baos)
        stream.write(off_baos)


class GloftLOSTTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Gloft LOST PAK Tool - Corrigido")
        self.root.geometry("800x600")
        
        self.reader = GloftLOSTReader()
        self.writer = GloftLOSTWriter()
        self.current_file = None
        self.strings = []
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Frame de controles
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botões
        ttk.Button(control_frame, text="Abrir PAK", command=self.open_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Salvar PAK", command=self.save_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Salvar como...", command=self.save_as_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Adicionar String", command=self.add_string).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Remover String", command=self.remove_string).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Exportar TXT", command=self.export_txt).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Importar TXT", command=self.import_txt).pack(side=tk.LEFT)
        
        # Label do arquivo atual
        self.file_label = ttk.Label(main_frame, text="Nenhum arquivo aberto")
        self.file_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Frame da lista de strings
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Lista de strings
        columns = ("#", "String")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        # Configurar colunas
        self.tree.heading("#", text="#")
        self.tree.heading("String", text="String")
        self.tree.column("#", width=50)
        self.tree.column("String", width=700)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Frame de edição
        edit_frame = ttk.Frame(main_frame)
        edit_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        edit_frame.columnconfigure(1, weight=1)
        
        ttk.Label(edit_frame, text="Editar String:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.edit_var = tk.StringVar()
        self.edit_entry = ttk.Entry(edit_frame, textvariable=self.edit_var, width=50)
        self.edit_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(edit_frame, text="Atualizar", command=self.update_string).grid(row=0, column=2)
        
        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.edit_entry.bind('<Return>', lambda e: self.update_string())
    
    def open_file(self):
        filename = filedialog.askopenfilename(
            title="Abrir arquivo PAK",
            filetypes=[("PAK files", "*.pak"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.status_var.set("Lendo arquivo...")
                self.root.update()
                
                self.strings = self.reader.read_pak(filename)
                self.current_file = filename
                self.file_label.config(text=f"Arquivo: {os.path.basename(filename)}")
                self.update_treeview()
                self.status_var.set(f"Carregado: {len(self.strings)} strings")
                messagebox.showinfo("Sucesso", f"Arquivo carregado com {len(self.strings)} strings")
            except Exception as e:
                self.status_var.set("Erro ao carregar arquivo")
                messagebox.showerror("Erro", f"Erro ao abrir arquivo: {str(e)}")
    
    def save_file(self):
        if not self.current_file:
            self.save_as_file()
            return
        
        try:
            self.status_var.set("Salvando arquivo...")
            self.root.update()
            
            self.writer.write_pak(self.strings, self.current_file)
            self.status_var.set("Arquivo salvo com sucesso!")
            messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
        except Exception as e:
            self.status_var.set("Erro ao salvar arquivo")
            messagebox.showerror("Erro", f"Erro ao salvar arquivo: {str(e)}")
    
    def save_as_file(self):
        filename = filedialog.asksaveasfilename(
            title="Salvar arquivo PAK",
            defaultextension=".pak",
            filetypes=[("PAK files", "*.pak"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.status_var.set("Salvando arquivo...")
                self.root.update()
                
                self.writer.write_pak(self.strings, filename)
                self.current_file = filename
                self.file_label.config(text=f"Arquivo: {os.path.basename(filename)}")
                self.status_var.set("Arquivo salvo com sucesso!")
                messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
            except Exception as e:
                self.status_var.set("Erro ao salvar arquivo")
                messagebox.showerror("Erro", f"Erro ao salvar arquivo: {str(e)}")
    
    def export_txt(self):
        if not self.strings:
            messagebox.showwarning("Aviso", "Nenhuma string para exportar")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Exportar para TXT",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='ISO-8859-1') as f:
                    for i, string in enumerate(self.strings):
                        f.write(f"{i}: {string}\n")
                messagebox.showinfo("Sucesso", "Strings exportadas com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
    
    def import_txt(self):
        filename = filedialog.askopenfilename(
            title="Importar do TXT",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='ISO-8859-1') as f:
                    lines = f.readlines()
                
                new_strings = []
                for line in lines:
                    # Remove o número da linha se existir
                    if ': ' in line:
                        string = line.split(': ', 1)[1].strip()
                    else:
                        string = line.strip()
                    new_strings.append(string)
                
                self.strings = new_strings
                self.update_treeview()
                messagebox.showinfo("Sucesso", f"{len(new_strings)} strings importadas!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao importar: {str(e)}")
    
    def add_string(self):
        new_string = simpledialog.askstring("Nova String", "Digite a nova string:")
        if new_string is not None:
            self.strings.append(new_string)
            self.update_treeview()
            self.tree.selection_set(len(self.strings) - 1)
            self.tree.see(len(self.strings) - 1)
    
    def remove_string(self):
        selection = self.tree.selection()
        if selection:
            index = int(selection[0])
            self.strings.pop(index)
            self.update_treeview()
    
    def update_string(self):
        selection = self.tree.selection()
        if selection and self.edit_var.get() is not None:
            index = int(selection[0])
            self.strings[index] = self.edit_var.get()
            self.update_treeview()
    
    def on_select(self, event):
        selection = self.tree.selection()
        if selection:
            index = int(selection[0])
            self.edit_var.set(self.strings[index])
    
    def update_treeview(self):
        self.tree.delete(*self.tree.get_children())
        for i, string in enumerate(self.strings):
            # Mostra caracteres especiais corretamente
            display_string = string
            if len(display_string) > 100:
                display_string = display_string[:100] + "..."
            self.tree.insert("", "end", iid=str(i), values=(i, display_string))


if __name__ == "__main__":
    root = tk.Tk()
    app = GloftLOSTTool(root)
    root.mainloop()
