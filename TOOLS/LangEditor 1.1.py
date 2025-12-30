import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import struct
import io
from PIL import Image, ImageTk
import os


class LangEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("LangEditor v1.1")
        self.root.geometry("800x600")

        self.current_path = Path.home()
        self.current_file = None
        self.file_data = []

        self.setup_ui()

    def setup_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Abrir Pasta", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ferramentas", menu=tools_menu)
        tools_menu.add_command(label="Cifrar/Decifrar NetLizard", command=self.netlizard_cipher)
        tools_menu.add_command(label="Cifrar/Decifrar Fishlabs", command=self.fishlabs_cipher)
        tools_menu.add_command(label="Alterar Tamanho", command=self.change_file_size)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)
        help_menu.add_command(label="Ajuda", command=self.show_help)

        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Caminho atual
        ttk.Label(main_frame, text="Caminho:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.path_label = ttk.Label(main_frame, text=str(self.current_path),
                                    relief=tk.SUNKEN, anchor=tk.W)
        self.path_label.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Lista de arquivos
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        self.file_listbox.bind('<Double-Button-1>', self.on_file_double_click)

        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Abrir", command=self.open_selected_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Editar", command=self.edit_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Atualizar", command=self.refresh_file_list).pack(side=tk.LEFT, padx=5)

        # Configurar redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Carregar lista inicial
        self.refresh_file_list()

    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        self.path_label.config(text=str(self.current_path))

        if self.current_path != self.current_path.parent:
            self.file_listbox.insert(tk.END, "..")

        try:
            items = sorted(self.current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if item.is_dir():
                    self.file_listbox.insert(tk.END, f"📁 {item.name}")
                else:
                    ext = item.suffix.lower()
                    icon = self.get_file_icon(ext)
                    self.file_listbox.insert(tk.END, f"{icon} {item.name}")
        except PermissionError:
            messagebox.showerror("Erro", "Sem permissão para acessar esta pasta")

    def get_file_icon(self, ext):
        icons = {
            '.lang': '📝', '.lng': '📝', '.class': '☕',
            '.bin': '⚙️', '.txt': '📄',
            '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️',
            '.gif': '🖼️', '.bmp': '🖼️'
        }
        return icons.get(ext, '📄')

    def on_file_double_click(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return

        item_text = self.file_listbox.get(selection[0])
        item_name = item_text.split(' ', 1)[1] if ' ' in item_text else item_text

        if item_name == "..":
            self.current_path = self.current_path.parent
            self.refresh_file_list()
        else:
            item_path = self.current_path / item_name
            if item_path.is_dir():
                self.current_path = item_path
                self.refresh_file_list()
            else:
                self.open_file(item_path)

    def open_folder(self):
        folder = filedialog.askdirectory(initialdir=self.current_path)
        if folder:
            self.current_path = Path(folder)
            self.refresh_file_list()

    def open_selected_file(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um arquivo")
            return

        item_text = self.file_listbox.get(selection[0])
        item_name = item_text.split(' ', 1)[1] if ' ' in item_text else item_text

        if item_name != "..":
            item_path = self.current_path / item_name
            if item_path.is_file():
                self.open_file(item_path)

    def open_file(self, file_path):
        ext = file_path.suffix.lower()

        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            self.show_image(file_path)
        elif ext == '.lang':
            self.edit_lang_file(file_path)
        elif ext == '.lng':
            self.edit_lng_file(file_path)
        elif ext == '.class':
            self.edit_class_file(file_path)
        elif ext in ['.txt', '.bin']:
            self.edit_text_file(file_path)
        else:
            messagebox.showinfo("Info", f"Tipo de arquivo não suportado: {ext}")

    def show_image(self, file_path):
        try:
            img_window = tk.Toplevel(self.root)
            img_window.title(file_path.name)

            img = Image.open(file_path)
            # Redimensionar se muito grande
            max_size = (800, 600)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            label = tk.Label(img_window, image=photo)
            label.image = photo  # Manter referência
            label.pack()

            info_label = tk.Label(img_window, text=f"Tamanho: {img.size[0]}x{img.size[1]}")
            info_label.pack()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir imagem: {str(e)}")

    def edit_file(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um arquivo")
            return

        item_text = self.file_listbox.get(selection[0])
        item_name = item_text.split(' ', 1)[1] if ' ' in item_text else item_text

        if item_name != "..":
            item_path = self.current_path / item_name
            if item_path.is_file():
                ext = item_path.suffix.lower()
                if ext in ['.lang', '.lng', '.class', '.txt']:
                    self.open_file(item_path)
                else:
                    messagebox.showinfo("Info", "Este tipo de arquivo não pode ser editado")

    def edit_lang_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                self.file_data = []
                while True:
                    try:
                        line = self.read_utf(f)
                        self.file_data.append(line)
                    except:
                        break

            self.show_editor_window(file_path, "Arquivo .lang")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir .lang: {str(e)}")

    def edit_lng_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                # Ler cabeçalho
                file_size = self.read_int16_le(f)
                version = f.read(1)[0]

                if version > 2:
                    messagebox.showerror("Erro", "Arquivo .lng inválido")
                    return

                count = self.read_int16_le(f)
                offsets = [self.read_int16_le(f) for _ in range(count + 1)]

                self.file_data = []
                for i in range(count):
                    size = offsets[i + 1] - offsets[i]
                    data = f.read(size)
                    self.file_data.append(data.decode('utf-8', errors='ignore'))

            self.show_editor_window(file_path, "Arquivo .lng")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir .lng: {str(e)}")

    def edit_class_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                f.read(8)  # Pular cabeçalho
                count = self.read_int16_be(f)

                self.file_data = [None] * count
                string_indices = []

                for i in range(1, count):
                    tag = f.read(1)[0]
                    if tag == 1:  # UTF-8 String
                        string = self.read_utf(f)
                        self.file_data[i] = string
                    elif tag == 8:  # String reference
                        idx = self.read_int16_be(f)
                        string_indices.append(idx)
                    elif tag in [3, 4, 9, 10, 11, 12]:
                        f.read(4)
                    elif tag in [5, 6]:
                        f.read(8)
                    elif tag == 7:
                        f.read(2)

            # Filtrar apenas strings
            self.file_data = [s for s in self.file_data if s is not None]
            self.show_editor_window(file_path, "Arquivo .class")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir .class: {str(e)}")

    def edit_text_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            editor = tk.Toplevel(self.root)
            editor.title(f"Editar: {file_path.name}")
            editor.geometry("700x500")

            text_area = scrolledtext.ScrolledText(editor, wrap=tk.WORD)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert('1.0', content)

            def save_text():
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text_area.get('1.0', tk.END))
                    messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
                    editor.destroy()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")

            btn_frame = ttk.Frame(editor)
            btn_frame.pack(pady=5)
            ttk.Button(btn_frame, text="Salvar", command=save_text).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancelar", command=editor.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir arquivo: {str(e)}")

    def show_editor_window(self, file_path, title):
        editor = tk.Toplevel(self.root)
        editor.title(f"{title}: {file_path.name}")
        editor.geometry("700x500")

        # Lista de strings
        list_frame = ttk.Frame(editor)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        string_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        string_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=string_list.yview)

        for i, item in enumerate(self.file_data):
            string_list.insert(tk.END, f"{i + 1}: {item[:50]}...")

        def edit_string():
            sel = string_list.curselection()
            if not sel:
                return

            idx = sel[0]
            edit_win = tk.Toplevel(editor)
            edit_win.title(f"Editar String {idx + 1}")
            edit_win.geometry("500x200")

            text_area = scrolledtext.ScrolledText(edit_win, wrap=tk.WORD, height=6)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert('1.0', self.file_data[idx])

            def save_string():
                self.file_data[idx] = text_area.get('1.0', tk.END).strip()
                string_list.delete(idx)
                string_list.insert(idx, f"{idx + 1}: {self.file_data[idx][:50]}...")
                edit_win.destroy()

            ttk.Button(edit_win, text="Salvar", command=save_string).pack(pady=5)

        def save_all():
            try:
                ext = file_path.suffix.lower()
                if ext == '.lang':
                    self.save_lang_file(file_path)
                elif ext == '.lng':
                    self.save_lng_file(file_path)
                elif ext == '.class':
                    messagebox.showinfo("Info", "Salvamento de .class requer implementação complexa")

                messagebox.showinfo("Sucesso", "Arquivo salvo!")
                editor.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")

        string_list.bind('<Double-Button-1>', lambda e: edit_string())

        btn_frame = ttk.Frame(editor)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Editar", command=edit_string).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Salvar", command=save_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=editor.destroy).pack(side=tk.LEFT, padx=5)

    def save_lang_file(self, file_path):
        with open(file_path, 'wb') as f:
            for line in self.file_data:
                self.write_utf(f, line)

    def save_lng_file(self, file_path):
        with open(file_path, 'wb') as f:
            # Calcular offsets
            count = len(self.file_data)
            offsets = [(count + 1) * 2 + 3]

            for line in self.file_data:
                line_bytes = line.encode('utf-8')
                offsets.append(offsets[-1] + len(line_bytes))

            total_size = offsets[-1]

            # Escrever cabeçalho
            self.write_int16_le(f, total_size + 2)
            f.write(bytes([2]))  # versão
            self.write_int16_le(f, count)

            for offset in offsets:
                self.write_int16_le(f, offset)

            for line in self.file_data:
                f.write(line.encode('utf-8'))

    def netlizard_cipher(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um arquivo")
            return

        item_text = self.file_listbox.get(selection[0])
        item_name = item_text.split(' ', 1)[1] if ' ' in item_text else item_text
        file_path = self.current_path / item_name

        if not file_path.is_file():
            return

        try:
            with open(file_path, 'rb') as f:
                data = bytearray(f.read())

            key = 100
            for i in range(len(data)):
                data[i] ^= key
                key = (key + 1) % 256

            with open(file_path, 'wb') as f:
                f.write(data)

            messagebox.showinfo("Sucesso", "Arquivo cifrado/decifrado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {str(e)}")

    def fishlabs_cipher(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um arquivo")
            return

        item_text = self.file_listbox.get(selection[0])
        item_name = item_text.split(' ', 1)[1] if ' ' in item_text else item_text
        file_path = self.current_path / item_name

        if not file_path.is_file():
            return

        try:
            with open(file_path, 'rb') as f:
                data = bytearray(f.read())

            size = len(data)
            if size < 100:
                swap_count = 10 + size % 10
            elif size < 200:
                swap_count = 50 + size % 20
            elif size < 300:
                swap_count = 80 + size % 20
            else:
                swap_count = 100 + size % 50

            for i in range(swap_count):
                data[i], data[size - i - 1] = data[size - i - 1], data[i]

            with open(file_path, 'wb') as f:
                f.write(data)

            messagebox.showinfo("Sucesso", "Arquivo cifrado/decifrado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {str(e)}")

    def change_file_size(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um arquivo")
            return

        item_text = self.file_listbox.get(selection[0])
        item_name = item_text.split(' ', 1)[1] if ' ' in item_text else item_text
        file_path = self.current_path / item_name

        if not file_path.is_file():
            return

        current_size = file_path.stat().st_size

        dialog = tk.Toplevel(self.root)
        dialog.title("Alterar Tamanho")
        dialog.geometry("300x150")

        ttk.Label(dialog, text=f"Tamanho atual: {current_size} bytes").pack(pady=10)
        ttk.Label(dialog, text="Novo tamanho (bytes):").pack()

        size_entry = ttk.Entry(dialog)
        size_entry.insert(0, str(current_size))
        size_entry.pack(pady=5)

        def apply_size():
            try:
                new_size = int(size_entry.get())
                with open(file_path, 'r+b') as f:
                    if new_size < current_size:
                        f.truncate(new_size)
                    else:
                        f.seek(0, 2)
                        f.write(b'\x00' * (new_size - current_size))

                messagebox.showinfo("Sucesso", "Tamanho alterado!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {str(e)}")

        ttk.Button(dialog, text="Aplicar", command=apply_size).pack(pady=10)

    def show_about(self):
        messagebox.showinfo("Sobre",
                            "LangEditor v1.1\n\n"
                            "Portado por Quakeman\n"
                            "Original Java ME por Kron\n"
                            "Suporta edição de arquivos criptografados\n"
                            "Criptografia NetLizard e Fishlabs\n\n"
                            "(c) 2025 - Versão Python")

    def show_help(self):
        help_text = """Este programa é destinado para editar alguns arquivos de jogos Java.

Recursos:
- Cifrador/decifrador NetLizard (XOR com chave incremental)
- Cifrador/decifrador Fishlabs (inversão de bytes)
- Editor de arquivos .lang (Fishlabs)
- Editor de arquivos .lng (Handy-Games)
- Editor de strings em arquivos .class
- Visualizador de imagens
- Alteração de tamanho de arquivos

Uso:
1. Navegue pelas pastas na lista
2. Dê duplo clique para abrir arquivos
3. Use o menu Ferramentas para cifrar/decifrar
4. Edite strings diretamente nas janelas de edição"""

        messagebox.showinfo("Ajuda", help_text)

    # Funções auxiliares para leitura/escrita
    def read_utf(self, f):
        length = struct.unpack('>H', f.read(2))[0]
        return f.read(length).decode('utf-8', errors='ignore')

    def write_utf(self, f, string):
        data = string.encode('utf-8')
        f.write(struct.pack('>H', len(data)))
        f.write(data)

    def read_int16_le(self, f):
        return struct.unpack('<H', f.read(2))[0]

    def write_int16_le(self, f, value):
        f.write(struct.pack('<H', value))

    def read_int16_be(self, f):
        return struct.unpack('>H', f.read(2))[0]


if __name__ == "__main__":
    root = tk.Tk()
    app = LangEditor(root)
    root.mainloop()
