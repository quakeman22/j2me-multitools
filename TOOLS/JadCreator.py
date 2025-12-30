import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import zipfile
import os
from pathlib import Path

class JadCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JAD Creator")
        self.root.geometry("800x650")
        self.root.configure(bg='#1a1a1a')
        
        # Estilo
        self.setup_styles()
        
        # Variáveis
        self.jar_file_path = None
        self.jad_content = ""
        self.use_custom_url = tk.BooleanVar(value=False)
        self.custom_url = tk.StringVar()
        
        # Criar interface
        self.create_widgets()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cores
        bg_dark = '#1a1a1a'
        bg_medium = '#2d2d2d'
        bg_light = '#3d3d3d'
        fg_color = '#e0e0e0'
        accent = '#4a9eff'
        
        style.configure('Dark.TFrame', background=bg_dark)
        style.configure('Medium.TFrame', background=bg_medium)
        style.configure('Dark.TLabel', background=bg_dark, foreground=fg_color, font=('Arial', 10))
        style.configure('Title.TLabel', background=bg_dark, foreground=fg_color, font=('Arial', 16, 'bold'))
        style.configure('Dark.TButton', background=bg_medium, foreground=fg_color, borderwidth=0, font=('Arial', 10))
        style.map('Dark.TButton', background=[('active', bg_light)])
        style.configure('Dark.TCheckbutton', background=bg_dark, foreground=fg_color, font=('Arial', 10))
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = ttk.Label(title_frame, text="🗃️ JAD Creator", style='Title.TLabel')
        title.pack(anchor=tk.W)
        
        subtitle = ttk.Label(title_frame, 
                            text="Extrai informações de arquivos .jar e cria arquivos .jad para aplicações J2ME",
                            style='Dark.TLabel',
                            foreground='#888888')
        subtitle.pack(anchor=tk.W, pady=(5, 0))
        
        # Área de upload
        upload_frame = ttk.Frame(main_frame, style='Medium.TFrame')
        upload_frame.pack(fill=tk.X, pady=10)
        
        upload_inner = tk.Frame(upload_frame, bg='#2d2d2d', highlightbackground='#4a9eff', 
                               highlightthickness=2, highlightcolor='#4a9eff')
        upload_inner.pack(fill=tk.BOTH, padx=2, pady=2)
        
        upload_label = tk.Label(upload_inner, text="📤 Clique para selecionar um arquivo .jar",
                               bg='#2d2d2d', fg='#e0e0e0', font=('Arial', 12),
                               cursor='hand2', pady=30)
        upload_label.pack(fill=tk.BOTH)
        upload_label.bind('<Button-1>', lambda e: self.select_file())
        
        upload_hint = tk.Label(upload_inner, text="Sem espaços no nome do arquivo",
                              bg='#2d2d2d', fg='#888888', font=('Arial', 9))
        upload_hint.pack(pady=(0, 20))
        
        # Frame de informações do arquivo
        self.info_frame = ttk.Frame(main_frame, style='Medium.TFrame')
        self.info_frame.pack(fill=tk.X, pady=10)
        self.info_frame.pack_forget()  # Esconder inicialmente
        
        info_title = ttk.Label(self.info_frame, text="Arquivo Selecionado", 
                              style='Dark.TLabel', font=('Arial', 12, 'bold'))
        info_title.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.file_name_label = ttk.Label(self.info_frame, text="", style='Dark.TLabel')
        self.file_name_label.pack(anchor=tk.W, padx=10, pady=2)
        
        self.file_size_label = ttk.Label(self.info_frame, text="", style='Dark.TLabel')
        self.file_size_label.pack(anchor=tk.W, padx=10, pady=(2, 10))
        
        # Separador
        separator = ttk.Separator(self.info_frame, orient='horizontal')
        separator.pack(fill=tk.X, padx=10, pady=10)
        
        # Frame de URL customizada
        url_frame = tk.Frame(self.info_frame, bg='#2d2d2d')
        url_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.url_check = tk.Checkbutton(url_frame, 
                                       text="Usar URL customizada",
                                       variable=self.use_custom_url,
                                       command=self.toggle_url_input,
                                       bg='#2d2d2d', fg='#e0e0e0',
                                       selectcolor='#1a1a1a',
                                       font=('Arial', 10),
                                       activebackground='#2d2d2d',
                                       activeforeground='#e0e0e0')
        self.url_check.pack(anchor=tk.W, pady=(0, 10))
        
        # Frame para entrada de URL (inicialmente oculto)
        self.url_input_frame = tk.Frame(url_frame, bg='#2d2d2d')
        
        url_label = tk.Label(self.url_input_frame, text="MIDlet-Jar-URL:",
                           bg='#2d2d2d', fg='#888888', font=('Arial', 9))
        url_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.url_entry = tk.Entry(self.url_input_frame, 
                                 textvariable=self.custom_url,
                                 bg='#1a1a1a', fg='#e0e0e0',
                                 font=('Courier', 10),
                                 relief=tk.FLAT,
                                 highlightthickness=1,
                                 highlightbackground='#3d3d3d',
                                 highlightcolor='#4a9eff',
                                 insertbackground='#e0e0e0')
        self.url_entry.pack(fill=tk.X, pady=(0, 10), ipady=5)
        self.url_entry.insert(0, "http://example.com/app.jar")
        
        self.regenerate_btn = tk.Button(self.url_input_frame, 
                                       text="🔄 Regenerar JAD com nova URL",
                                       bg='#4a9eff', fg='white', 
                                       font=('Arial', 10),
                                       relief=tk.FLAT, 
                                       padx=15, pady=8,
                                       cursor='hand2',
                                       command=self.regenerate_jad)
        self.regenerate_btn.pack(fill=tk.X)
        
        # Frame de status
        self.status_frame = tk.Frame(main_frame, bg='#1a1a1a')
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = tk.Label(self.status_frame, text="", 
                                     bg='#1a1a1a', fg='#4a9eff', 
                                     font=('Arial', 10), anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        
        # Frame do conteúdo JAD
        self.jad_frame = ttk.Frame(main_frame, style='Medium.TFrame')
        self.jad_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.jad_frame.pack_forget()  # Esconder inicialmente
        
        jad_header = tk.Frame(self.jad_frame, bg='#2d2d2d')
        jad_header.pack(fill=tk.X, padx=10, pady=10)
        
        jad_title = tk.Label(jad_header, text="Conteúdo do arquivo .jad",
                            bg='#2d2d2d', fg='#e0e0e0', font=('Arial', 12, 'bold'))
        jad_title.pack(side=tk.LEFT)
        
        self.download_btn = tk.Button(jad_header, text="⬇️ Baixar .jad",
                                      bg='#4a9eff', fg='white', font=('Arial', 10),
                                      relief=tk.FLAT, padx=15, pady=5,
                                      cursor='hand2', command=self.download_jad)
        self.download_btn.pack(side=tk.RIGHT)
        
        # Área de texto com scrollbar
        text_frame = tk.Frame(self.jad_frame, bg='#1a1a1a')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(text_frame, bg='#2d2d2d')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.jad_text = tk.Text(text_frame, bg='#1a1a1a', fg='#e0e0e0',
                               font=('Courier', 10), relief=tk.FLAT,
                               yscrollcommand=scrollbar.set, padx=10, pady=10,
                               highlightthickness=1, highlightbackground='#3d3d3d')
        self.jad_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.jad_text.yview)
        
        # Footer
        footer = ttk.Label(main_frame, 
                          text="Criado por Quakeman",
                          style='Dark.TLabel', foreground='#666666', font=('Arial', 8))
        footer.pack(side=tk.BOTTOM, pady=10)
    
    def toggle_url_input(self):
        if self.use_custom_url.get():
            self.url_input_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            self.url_input_frame.pack_forget()
    
    def regenerate_jad(self):
        if self.jar_file_path:
            self.process_jar_file()
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecione um arquivo JAR",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        
        if file_path:
            # Verificar se tem espaços no nome
            if ' ' in os.path.basename(file_path):
                self.show_error("O nome do arquivo não pode conter espaços")
                return
            
            # Verificar extensão
            if not file_path.endswith('.jar'):
                self.show_error("Por favor, selecione um arquivo .jar válido")
                return
            
            self.jar_file_path = file_path
            self.process_jar_file()
    
    def process_jar_file(self):
        try:
            self.show_status("Processando arquivo JAR...", "#4a9eff")
            
            # Mostrar informações do arquivo
            file_name = os.path.basename(self.jar_file_path)
            file_size = os.path.getsize(self.jar_file_path)
            
            self.info_frame.pack(fill=tk.X, pady=10)
            self.file_name_label.config(text=f"Nome: {file_name}")
            self.file_size_label.config(text=f"Tamanho: {file_size} bytes")
            
            # Extrair MANIFEST.MF
            manifest_content = self.extract_manifest()
            
            if not manifest_content:
                raise Exception("MANIFEST.MF não encontrado no arquivo JAR")
            
            # Criar conteúdo JAD
            self.create_jad_content(file_name, file_size, manifest_content)
            
            # Mostrar resultado
            self.jad_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            self.jad_text.delete(1.0, tk.END)
            self.jad_text.insert(1.0, self.jad_content)
            
            self.show_status("✅ Arquivo JAD criado com sucesso!", "#4ade80")
            
        except Exception as e:
            self.show_error(str(e))
    
    def extract_manifest(self):
        try:
            with zipfile.ZipFile(self.jar_file_path, 'r') as jar:
                # Procurar MANIFEST.MF
                manifest_path = None
                for name in jar.namelist():
                    if 'MANIFEST.MF' in name.upper():
                        manifest_path = name
                        break
                
                if manifest_path:
                    with jar.open(manifest_path) as manifest_file:
                        return manifest_file.read().decode('utf-8', errors='ignore')
            
            return None
            
        except Exception as e:
            raise Exception(f"Erro ao extrair MANIFEST: {str(e)}")
    
    def create_jad_content(self, file_name, file_size, manifest):
        app_name = file_name.replace('.jar', '')
        
        # Extrair informações do manifest
        lines = manifest.split('\n')
        info = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('MIDlet-Name:'):
                info['name'] = line
            elif line.startswith('MIDlet-Version:'):
                info['version'] = line
            elif line.startswith('MIDlet-Vendor:'):
                info['vendor'] = line
            elif line.startswith('Nokia-MIDlet-Category:'):
                info['nokia_category'] = line
        
        # Criar conteúdo JAD
        jad_lines = []
        
        # Usar URL customizada ou padrão
        if self.use_custom_url.get() and self.custom_url.get().strip():
            jad_lines.append(f"MIDlet-Jar-URL: {self.custom_url.get().strip()}")
        else:
            jad_lines.append(f"MIDlet-Jar-URL: {app_name}.jar")
        
        jad_lines.append(f"MIDlet-Jar-Size: {file_size}")
        
        if 'name' in info:
            jad_lines.append(info['name'])
        if 'version' in info:
            jad_lines.append(info['version'])
        if 'vendor' in info:
            jad_lines.append(info['vendor'])
        if 'nokia_category' in info:
            jad_lines.append(info['nokia_category'])
        
        self.jad_content = '\n'.join(jad_lines)
    
    def download_jad(self):
        if not self.jad_content or not self.jar_file_path:
            return
        
        # Nome do arquivo JAD
        jar_dir = os.path.dirname(self.jar_file_path)
        jar_name = os.path.basename(self.jar_file_path)
        jad_name = jar_name.replace('.jar', '.jad')
        
        default_path = os.path.join(jar_dir, jad_name)
        
        # Diálogo para salvar
        save_path = filedialog.asksaveasfilename(
            title="Salvar arquivo JAD",
            initialfile=jad_name,
            initialdir=jar_dir,
            defaultextension=".jad",
            filetypes=[("JAD files", "*.jad"), ("All files", "*.*")]
        )
        
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(self.jad_content)
                
                messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{save_path}")
                self.show_status(f"✅ Arquivo salvo: {os.path.basename(save_path)}", "#4ade80")
                
            except Exception as e:
                self.show_error(f"Erro ao salvar arquivo: {str(e)}")
    
    def show_status(self, message, color):
        self.status_label.config(text=message, fg=color)
    
    def show_error(self, message):
        self.status_label.config(text=f"❌ Erro: {message}", fg="#ef4444")
        messagebox.showerror("Erro", message)


def main():
    root = tk.Tk()
    app = JadCreatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
