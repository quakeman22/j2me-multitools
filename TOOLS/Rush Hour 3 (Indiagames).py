import tkinter as tk
from tkinter import filedialog, messagebox
import os


class EditorTextosJogo:
    def __init__(self):
        self.data = bytearray()
        self.offsets = []
        self.textos = []
        self.original_textos = []
        self.total_size = 0
        self.control_byte = 0

        self.selected_index = None   

        self.root = tk.Tk()
        self.root.title("Editor de Textos)
        self.root.geometry("1100x700")
        self.root.configure(bg="#0d1117")

        tk.Label(
            self.root,
            text="EDITOR DE TEXTOS RUSH HOUR 3",
            bg="#0d1117",
            fg="#58a6ff",
            font=("Consolas", 20, "bold")
        ).pack(pady=15)

        top = tk.Frame(self.root, bg="#0d1117")
        top.pack()

        tk.Button(top, text="ABRIR ARQUIVO", command=self.abrir,
                  bg="#21262d", fg="white", font=("Consolas", 12)).grid(row=0, column=0, padx=15)

        tk.Button(top, text="SALVAR ARQUIVO", command=self.salvar,
                  bg="#21262d", fg="white", font=("Consolas", 12)).grid(row=0, column=1, padx=15)

        self.lbl_info = tk.Label(
            self.root, text="Nenhum arquivo carregado",
            bg="#0d1117", fg="#ffa657", font=("Consolas", 12)
        )
        self.lbl_info.pack(pady=5)

        main = tk.Frame(self.root, bg="#0d1117")
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        left = tk.Frame(main, bg="#0d1117")
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="Textos", bg="#0d1117", fg="#58a6ff",
                 font=("Consolas", 12, "bold")).pack()

        self.listbox = tk.Listbox(
            left, bg="#161b22", fg="#e6edf3",
            font=("Consolas", 11),
            selectbackground="#1f6feb", width=45
        )
        self.listbox.pack(fill=tk.Y, expand=False, padx=(0, 15))
        self.listbox.bind("<<ListboxSelect>>", self.selecionar_texto)

        right = tk.Frame(main, bg="#0d1117")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right, text="Editar texto selecionado", bg="#0d1117",
                 fg="#58a6ff", font=("Consolas", 12, "bold")).pack(anchor="w")

        self.txt_editor = tk.Text(
            right, wrap=tk.WORD, bg="#161b22", fg="#e6edf3",
            insertbackground="white", font=("Consolas", 12), undo=True
        )
        self.txt_editor.pack(fill=tk.BOTH, expand=True)

        tk.Button(
            right, text="APLICAR TEXTO EDITADO", command=self.aplicar_texto,
            bg="#238636", fg="white", font=("Consolas", 13, "bold")
        ).pack(pady=10)

        self.lbl_mod = tk.Label(
            self.root, text="Modificados: 0",
            bg="#0d1117", fg="#7ee787",
            font=("Consolas", 11)
        )
        self.lbl_mod.pack(pady=10)

        self.root.mainloop()

    # ==================================================================
    def abrir(self):
        caminho = filedialog.askopenfilename(title="Selecione o arquivo .bin")
        if not caminho:
            return

        with open(caminho, "rb") as f:
            self.data = bytearray(f.read())

        self.total_size = int.from_bytes(self.data[0:2], "big")
        self.control_byte = self.data[2]

        self.offsets = []
        pos = 3
        while pos + 1 < len(self.data):
            off = int.from_bytes(self.data[pos:pos+2], "big")
            if off < pos:
                break
            self.offsets.append(off)
            pos += 2

        self.textos = []
        for off in self.offsets:
            size = int.from_bytes(self.data[off:off+2], "big")
            txt = self.data[off+2:off+2+size].decode("ascii", errors="ignore")
            self.textos.append(txt)

        self.original_textos = self.textos.copy()
        self.lbl_info.config(text=f"Carregado: {os.path.basename(caminho)}")

        self.atualizar_lista()
        self.atualizar_modificados()

    # ==================================================================
    def atualizar_lista(self):
        self.listbox.delete(0, tk.END)
        for i, t in enumerate(self.textos):
            prev = t.replace("\n", " ")[:40]
            self.listbox.insert(tk.END, f"[{i:03d}] {prev}")

    # ==================================================================
    def selecionar_texto(self, event):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        self.selected_index = idx  # <<< FIX
        self.txt_editor.delete("1.0", tk.END)
        self.txt_editor.insert("1.0", self.textos[idx])

    # ==================================================================
    def aplicar_texto(self):
        if self.selected_index is None:   # <<< FIX
            messagebox.showwarning("Aviso", "Selecione um texto primeiro.")
            return

        idx = self.selected_index
        novo = self.txt_editor.get("1.0", tk.END).rstrip("\n")

        self.textos[idx] = novo

        prev = novo.replace("\n", " ")[:40]
        self.listbox.delete(idx)
        self.listbox.insert(idx, f"[{idx:03d}] {prev}")
        self.listbox.select_set(idx)
        self.listbox.activate(idx)

        self.atualizar_modificados()

    # ==================================================================
    def atualizar_modificados(self):
        mod = sum(1 for o, n in zip(self.original_textos, self.textos) if o != n)
        self.lbl_mod.config(text=f"Modificados: {mod}")

    # ==================================================================
    def salvar(self):
        caminho = filedialog.asksaveasfilename(defaultextension=".bin")
        if not caminho:
            return

        blocos = []
        for txt in self.textos:
            b = txt.encode("ascii", errors="ignore")
            size = len(b)
            blocos.append(size.to_bytes(2, "big") + b)

        new_offsets = []
        pos = 3 + len(self.offsets) * 2
        for blk in blocos:
            new_offsets.append(pos)
            pos += len(blk)

        novo_total = pos

        novo = bytearray()
        novo.extend(novo_total.to_bytes(2, "big"))
        novo.append(self.control_byte)

        for off in new_offsets:
            novo.extend(off.to_bytes(2, "big"))

        for blk in blocos:
            novo.extend(blk)

        with open(caminho, "wb") as f:
            f.write(novo)

        messagebox.showinfo("Sucesso", f"Arquivo salvo como:\n{caminho}")


if __name__ == "__main__":
    EditorTextosJogo()
