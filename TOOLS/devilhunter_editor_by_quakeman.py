#!/usr/bin/env python3
"""
Devil Hunter X — String Editor (Python/Tkinter)
Lê e escreve o arquivo 5529.dat (LZMA + tabela de offsets big-endian)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import struct, lzma, json, copy, os

# ─── Constantes ───────────────────────────────────────────────────────────────
TEXT_BLOCKS = [14, 15, 16, 17, 18, 19, 20, 21, 22]
BLOCK_NAMES = {
    14: 'Menu / Diálogos / Tips',
    15: 'Tutorial / Boss 1',
    16: 'Boss 2',
    17: 'Boss 3',
    18: 'Boss 4',
    19: 'Boss 5',
    20: 'Boss 6',
    21: '(bloco vazio)',
    22: 'Boss Final',
}
HEADER_SIZE = 101  # 1 byte count + 25×4 bytes offsets
N_BLOCKS    = 25

# ─── Parse / Build ────────────────────────────────────────────────────────────
def read_offsets(dec: bytes) -> list[int]:
    offs = []
    for i in range(N_BLOCKS):
        o = 1 + i * 4
        offs.append(struct.unpack('>I', dec[o:o+4])[0])
    return offs

def parse_block(data: bytes) -> list[str]:
    if len(data) < 2:
        return []
    n = struct.unpack('<H', data[:2])[0]
    strings, p = [], 2
    for _ in range(n):
        if p + 2 > len(data):
            break
        slen = struct.unpack('<H', data[p:p+2])[0]
        p += 2
        strings.append(data[p:p+slen].decode('latin-1'))
        p += slen
    return strings

def build_block(strings: list[str]) -> bytes:
    parts = []
    parts.append(struct.pack('<H', len(strings)))
    for s in strings:
        b = s.encode('latin-1', errors='replace')
        parts.append(struct.pack('<H', len(b)))
        parts.append(b)
    return b''.join(parts)

def rebuild(raw_dec: bytes, offsets: list[int], text_blocks: dict) -> bytes:
    gap = offsets[0] - HEADER_SIZE

    raw_parts = []
    for i in range(N_BLOCKS - 1):
        end = offsets[i+1] if i+1 < N_BLOCKS else len(raw_dec)
        if i in text_blocks:
            raw_parts.append(build_block(text_blocks[i]))
        else:
            raw_parts.append(raw_dec[offsets[i]:end])

    # Calcular novos offsets
    new_offs = []
    cur = HEADER_SIZE + gap
    for blk in raw_parts:
        new_offs.append(cur)
        cur += len(blk)
    new_offs.append(cur)  # end marker

    # Montar buffer final
    result = bytearray(cur)
    result[0] = raw_dec[0]  # 0x19

    for i in range(N_BLOCKS):
        o = 1 + i * 4
        result[o:o+4] = struct.pack('>I', new_offs[i])

    # Gap preservado
    result[HEADER_SIZE:HEADER_SIZE+gap] = raw_dec[HEADER_SIZE:HEADER_SIZE+gap]

    wp = HEADER_SIZE + gap
    for blk in raw_parts:
        result[wp:wp+len(blk)] = blk
        wp += len(blk)

    return bytes(result)

# ─── Janela principal ─────────────────────────────────────────────────────────
class DevilHunterEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("☠ Devil Hunter X — String Editor")
        self.geometry("1100x700")
        self.minsize(800, 500)
        self.configure(bg='#1a1a1a')

        # Estado
        self.raw_dec     = None
        self.offsets     = []
        self.text_blocks = {}
        self.orig_blocks = {}
        self.cur_block   = None
        self.dat_path    = None
        self.row_widgets = []   # lista de (orig_str, StringVar, label_bytes)

        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.',            background='#1a1a1a', foreground='#d4d4d4', font=('Consolas', 10))
        style.configure('TFrame',       background='#1a1a1a')
        style.configure('TLabel',       background='#1a1a1a', foreground='#d4d4d4')
        style.configure('TButton',      background='#222222', foreground='#bbbbbb',
                        relief='flat', padding=(8, 3))
        style.map('TButton',
                  background=[('active', '#2e2e2e')],
                  foreground=[('active', '#ffffff')])
        style.configure('Accent.TButton', foreground='#e8a020', background='#2a1c00')
        style.map('Accent.TButton',
                  background=[('active', '#3a2800')],
                  foreground=[('active', '#e8a020')])
        style.configure('Danger.TButton', foreground='#e06060', background='#222222')
        style.map('Danger.TButton',
                  background=[('active', '#2a1010')],
                  foreground=[('active', '#e06060')])
        style.configure('Sidebar.TFrame', background='#111111')
        style.configure('Sidebar.TLabel', background='#111111', foreground='#777777', font=('Consolas', 9))
        style.configure('Active.TLabel',  background='#221800', foreground='#e8a020', font=('Consolas', 9, 'bold'))
        style.configure('Header.TFrame',  background='#111111')
        style.configure('Header.TLabel',  background='#111111', foreground='#e8a020',
                        font=('Consolas', 11, 'bold'))

        # ── Header ──────────────────────────────────────────────────────────
        hdr = ttk.Frame(self, style='Header.TFrame', padding=(8, 5))
        hdr.pack(fill='x')

        ttk.Label(hdr, text='☠ DEVIL HUNTER X · STRING EDITOR',
                  style='Header.TLabel').pack(side='left', padx=(0, 12))

        self.btn_open  = ttk.Button(hdr, text='Abrir .dat',    command=self.open_dat)
        self.btn_save  = ttk.Button(hdr, text='Salvar .dat',   command=self.save_dat,
                                    style='Accent.TButton', state='disabled')
        self.btn_exp   = ttk.Button(hdr, text='Export JSON',   command=self.export_json, state='disabled')
        self.btn_imp   = ttk.Button(hdr, text='Import JSON',   command=self.import_json, state='disabled')
        self.btn_rst   = ttk.Button(hdr, text='Resetar',       command=self.reset_all,
                                    style='Danger.TButton', state='disabled')

        for btn in (self.btn_open, self.btn_save, self.btn_exp, self.btn_imp, self.btn_rst):
            btn.pack(side='left', padx=2)

        self.lbl_status = ttk.Label(hdr, text='Aguardando arquivo...',
                                    foreground='#555555', background='#111111',
                                    font=('Consolas', 9))
        self.lbl_status.pack(side='right', padx=4)

        ttk.Separator(self, orient='horizontal').pack(fill='x')

        # ── Workspace ───────────────────────────────────────────────────────
        self.workspace = ttk.Frame(self)
        self.workspace.pack(fill='both', expand=True)

        # Sidebar
        self.sidebar_frame = ttk.Frame(self.workspace, style='Sidebar.TFrame', width=200)
        self.sidebar_frame.pack(side='left', fill='y')
        self.sidebar_frame.pack_propagate(False)

        sb_title = tk.Label(self.sidebar_frame, text='BLOCOS DE TEXTO',
                            bg='#111111', fg='#444444', font=('Consolas', 8),
                            pady=6)
        sb_title.pack(fill='x')
        tk.Frame(self.sidebar_frame, bg='#2a2a2a', height=1).pack(fill='x')

        self.sidebar_canvas = tk.Canvas(self.sidebar_frame, bg='#111111',
                                        highlightthickness=0, width=200)
        sb_scroll = ttk.Scrollbar(self.sidebar_frame, orient='vertical',
                                  command=self.sidebar_canvas.yview)
        self.sidebar_canvas.configure(yscrollcommand=sb_scroll.set)
        sb_scroll.pack(side='right', fill='y')
        self.sidebar_canvas.pack(fill='both', expand=True)
        self.sidebar_inner = tk.Frame(self.sidebar_canvas, bg='#111111')
        self.sidebar_canvas.create_window((0, 0), window=self.sidebar_inner, anchor='nw')
        self.sidebar_inner.bind('<Configure>',
            lambda e: self.sidebar_canvas.configure(
                scrollregion=self.sidebar_canvas.bbox('all')))
        self._sb_buttons = {}

        # Panel (toolbar + strings)
        panel = ttk.Frame(self.workspace)
        panel.pack(side='left', fill='both', expand=True)

        toolbar2 = ttk.Frame(panel, padding=(8, 4))
        toolbar2.configure(style='Header.TFrame')
        toolbar2.pack(fill='x')

        ttk.Label(toolbar2, text='Buscar:', style='Sidebar.TLabel',
                  background='#111111').pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *_: self.render_strings())
        search_entry = tk.Entry(toolbar2, textvariable=self.search_var,
                                bg='#1a1a1a', fg='#cccccc', insertbackground='#e8a020',
                                relief='flat', font=('Consolas', 10), width=24,
                                highlightthickness=1, highlightcolor='#e8a020',
                                highlightbackground='#333333')
        search_entry.pack(side='left', padx=(4, 10))

        self.only_mod = tk.BooleanVar()
        chk = tk.Checkbutton(toolbar2, text='só modificadas', variable=self.only_mod,
                             command=self.render_strings,
                             bg='#111111', fg='#666666', selectcolor='#222222',
                             activebackground='#111111', activeforeground='#aaaaaa',
                             font=('Consolas', 9))
        chk.pack(side='left')

        self.lbl_count = tk.Label(toolbar2, text='', bg='#111111',
                                  fg='#444444', font=('Consolas', 9))
        self.lbl_count.pack(side='right', padx=6)

        tk.Frame(panel, bg='#2a2a2a', height=1).pack(fill='x')

        # Strings list
        self.strings_canvas = tk.Canvas(panel, bg='#1a1a1a', highlightthickness=0)
        str_scroll = ttk.Scrollbar(panel, orient='vertical',
                                   command=self.strings_canvas.yview)
        self.strings_canvas.configure(yscrollcommand=str_scroll.set)
        str_scroll.pack(side='right', fill='y')
        self.strings_canvas.pack(fill='both', expand=True)

        self.strings_frame = tk.Frame(self.strings_canvas, bg='#1a1a1a')
        self._str_win = self.strings_canvas.create_window(
            (0, 0), window=self.strings_frame, anchor='nw')
        self.strings_frame.bind('<Configure>', self._on_strings_frame_resize)
        self.strings_canvas.bind('<Configure>', self._on_canvas_resize)

        # Mouse wheel
        self.strings_canvas.bind('<MouseWheel>',
            lambda e: self.strings_canvas.yview_scroll(-1*(e.delta//120), 'units'))
        self.strings_canvas.bind('<Button-4>',
            lambda e: self.strings_canvas.yview_scroll(-1, 'units'))
        self.strings_canvas.bind('<Button-5>',
            lambda e: self.strings_canvas.yview_scroll(1, 'units'))

        # Drop zone (antes do workspace)
        self.drop_frame = tk.Frame(self, bg='#1a1a1a')
        self.drop_frame.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(self.drop_frame,
                 text='☠  DEVIL HUNTER X · STRING EDITOR',
                 bg='#1a1a1a', fg='#e8a020', font=('Consolas', 14, 'bold')).pack(pady=(0, 16))
        tk.Label(self.drop_frame,
                 text='Clique em  [Abrir .dat]  ou arraste 5529.dat para esta janela',
                 bg='#1a1a1a', fg='#666666', font=('Consolas', 10)).pack()
        tk.Label(self.drop_frame,
                 text='Devil Hunter X — arquivo de strings comprimido com LZMA',
                 bg='#1a1a1a', fg='#333333', font=('Consolas', 9)).pack(pady=(4, 0))

        # Drag-and-drop
        self.drop_target_register = None
        try:
            self.dnd_bind('<<Drop>>', self._on_drop)
        except Exception:
            pass
        self.bind('<Key-o>', lambda e: self.open_dat())

    def _on_strings_frame_resize(self, event):
        self.strings_canvas.configure(scrollregion=self.strings_canvas.bbox('all'))

    def _on_canvas_resize(self, event):
        self.strings_canvas.itemconfig(self._str_win, width=event.width)

    # ── Status ────────────────────────────────────────────────────────────────
    def set_status(self, msg, state='normal'):
        colors = {'ok': '#5ec85e', 'err': '#e06060', 'busy': '#e8a020', 'normal': '#555555'}
        self.lbl_status.configure(text=msg, foreground=colors.get(state, '#555555'))
        self.update_idletasks()

    # ── File ops ──────────────────────────────────────────────────────────────
    def open_dat(self):
        path = filedialog.askopenfilename(
            title='Abrir arquivo .dat',
            filetypes=[('DAT files', '*.dat'), ('All files', '*.*')])
        if path:
            self._load_dat(path)

    def _load_dat(self, path):
        self.set_status('Lendo arquivo...', 'busy')
        try:
            with open(path, 'rb') as f:
                buf = f.read()

            if len(buf) < 17:
                raise ValueError('Arquivo muito pequeno')

            size_be = struct.unpack('>I', buf[:4])[0]
            stream  = buf[4:]

            self.set_status('Descomprimindo LZMA...', 'busy')
            try:
                dec = lzma.decompress(stream)
            except lzma.LZMAError:
                dec = lzma.decompress(stream, format=lzma.FORMAT_ALONE)

            self.raw_dec  = dec
            self.offsets  = read_offsets(dec)
            self.dat_path = path
            self.text_blocks = {}
            for bi in TEXT_BLOCKS:
                start = self.offsets[bi]
                end   = self.offsets[bi+1] if bi+1 < N_BLOCKS else len(dec)
                self.text_blocks[bi] = parse_block(dec[start:end])

            self.orig_blocks = copy.deepcopy(self.text_blocks)

            self.drop_frame.place_forget()
            for btn in (self.btn_save, self.btn_exp, self.btn_imp, self.btn_rst):
                btn.configure(state='normal')

            self._build_sidebar()
            self._select_block(14)

            total = sum(len(v) for v in self.text_blocks.values())
            fname = os.path.basename(path)
            self.set_status(f'{fname} · {total} strings carregadas', 'ok')

        except Exception as e:
            self.set_status(f'Erro: {e}', 'err')
            messagebox.showerror('Erro ao abrir', str(e))

    def save_dat(self):
        path = filedialog.asksaveasfilename(
            title='Salvar .dat',
            initialfile=os.path.basename(self.dat_path) if self.dat_path else '5529.dat',
            defaultextension='.dat',
            filetypes=[('DAT files', '*.dat'), ('All files', '*.*')])
        if not path:
            return

        self.set_status('Reconstruindo buffer...', 'busy')
        try:
            new_dec = rebuild(self.raw_dec, self.offsets, self.text_blocks)

            self.set_status('Comprimindo LZMA (aguarde)...', 'busy')
            comp = lzma.compress(new_dec, format=lzma.FORMAT_ALONE,
                                 filters=[{'id': lzma.FILTER_LZMA1,
                                           'preset': 5,
                                           'dict_size': 1 << 23}])

            # CRÍTICO: o Python gera bytes 5-12 do header LZMA como 0xFFFFFFFFFFFFFFFF
            # (tamanho desconhecido). O decoder do jogo (sub_29e) lê esses bytes como
            # o tamanho do buffer a alocar — com 0xFF...FF ele trava/freeze por OOM.
            # Fix: patchear bytes 5-8 com o tamanho real descomprimido (LE 4 bytes)
            # e zerar bytes 9-12, exatamente como no arquivo original.
            comp = bytearray(comp)
            comp[5:9]  = struct.pack('<I', len(new_dec))
            comp[9:13] = b'\x00\x00\x00\x00'
            comp = bytes(comp)

            size_be = struct.pack('>I', len(comp))
            out = size_be + comp

            with open(path, 'wb') as f:
                f.write(out)

            self.set_status(f'Salvo! {len(out)} bytes → {os.path.basename(path)}', 'ok')

        except Exception as e:
            self.set_status(f'Erro ao salvar: {e}', 'err')
            messagebox.showerror('Erro ao salvar', str(e))

    def export_json(self):
        path = filedialog.asksaveasfilename(
            title='Exportar JSON',
            initialfile='5529_strings.json',
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')])
        if not path:
            return
        data = {}
        for bi, strings in self.text_blocks.items():
            data[f'block_{bi}'] = {
                'name': BLOCK_NAMES.get(bi, f'Block {bi}'),
                'strings': strings
            }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.set_status(f'JSON exportado → {os.path.basename(path)}', 'ok')

    def import_json(self):
        path = filedialog.askopenfilename(
            title='Importar JSON',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')])
        if not path:
            return
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            count = 0
            for key, val in data.items():
                bi = int(key.replace('block_', ''))
                if bi in self.text_blocks and isinstance(val.get('strings'), list):
                    self.text_blocks[bi] = val['strings']
                    count += 1
            self._build_sidebar()
            self.render_strings()
            self.set_status(f'JSON importado · {count} blocos', 'ok')
        except Exception as e:
            self.set_status(f'Erro no JSON: {e}', 'err')
            messagebox.showerror('Erro ao importar JSON', str(e))

    def reset_all(self):
        if not messagebox.askyesno('Resetar', 'Resetar todas as strings para o original?'):
            return
        self.text_blocks = copy.deepcopy(self.orig_blocks)
        self._build_sidebar()
        self.render_strings()
        self.set_status('Resetado para original', 'ok')

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        for w in self.sidebar_inner.winfo_children():
            w.destroy()
        self._sb_buttons = {}

        for bi in TEXT_BLOCKS:
            name = BLOCK_NAMES.get(bi, f'Block {bi}')
            mod  = self._is_modified(bi)
            cnt  = len(self.text_blocks.get(bi, []))
            is_cur = bi == self.cur_block

            fg_name = '#e8a020' if mod else ('#e8a020' if is_cur else '#888888')
            fg_meta = '#8a5a10' if is_cur else '#444444'
            bg      = '#221800' if is_cur else '#111111'

            frm = tk.Frame(self.sidebar_inner, bg=bg, cursor='hand2')
            frm.pack(fill='x')
            tk.Frame(frm, bg='#1c1c1c', height=1).pack(fill='x')

            inner = tk.Frame(frm, bg=bg, padx=10, pady=7)
            inner.pack(fill='x')

            marker = '● ' if mod else ''
            lbl_name = tk.Label(inner, text=marker + name, bg=bg, fg=fg_name,
                                font=('Consolas', 9, 'bold'), anchor='w', justify='left')
            lbl_name.pack(fill='x')
            lbl_meta = tk.Label(inner, text=f'Bloco {bi} · {cnt} strings',
                                bg=bg, fg=fg_meta, font=('Consolas', 8), anchor='w')
            lbl_meta.pack(fill='x')

            for w in (frm, inner, lbl_name, lbl_meta):
                w.bind('<Button-1>', lambda e, b=bi: self._select_block(b))

            self._sb_buttons[bi] = frm

    def _select_block(self, bi):
        self.cur_block = bi
        self._build_sidebar()
        self.render_strings()

    def _is_modified(self, bi):
        a = self.orig_blocks.get(bi, [])
        b = self.text_blocks.get(bi, [])
        return len(a) == len(b) and any(x != y for x, y in zip(a, b))

    def _refresh_sidebar_entry(self, bi):
        self._build_sidebar()

    # ── Strings panel ─────────────────────────────────────────────────────────
    def render_strings(self):
        if self.cur_block is None:
            return

        for w in self.strings_frame.winfo_children():
            w.destroy()
        self.row_widgets = []

        strings = self.text_blocks.get(self.cur_block, [])
        orig    = self.orig_blocks.get(self.cur_block, [])
        search  = self.search_var.get().lower()
        only_mod= self.only_mod.get()
        shown   = 0

        for idx, s in enumerate(strings):
            orig_s = orig[idx] if idx < len(orig) else ''
            mod    = s != orig_s
            if only_mod and not mod:
                continue
            if search and search not in s.lower() and search not in orig_s.lower():
                continue
            shown += 1

            row_bg = '#1c1600' if mod else '#1c1c1c'
            row_border = '#5a3a00' if mod else '#242424'

            row = tk.Frame(self.strings_frame, bg=row_bg,
                           highlightthickness=1, highlightbackground=row_border,
                           pady=3, padx=5)
            row.pack(fill='x', pady=2, padx=6)

            # Index
            tk.Label(row, text=str(idx), bg=row_bg, fg='#444444',
                     font=('Consolas', 9), width=4, anchor='e').pack(side='left', padx=(0, 4))

            # Textarea
            n_lines = max(1, (len(s) // 80) + s.count('\n') + 1)
            ta = tk.Text(row, height=n_lines, bg='#131313', fg='#cccccc',
                         insertbackground='#e8a020', relief='flat',
                         font=('Consolas', 10), wrap='word', padx=4, pady=3,
                         highlightthickness=1, highlightbackground='#2e2e2e',
                         highlightcolor='#e8a020')
            ta.insert('1.0', s)
            ta.pack(side='left', fill='x', expand=True)

            # Bytes label
            lbl_bytes = tk.Label(row, text=f'{len(s)}b', bg=row_bg,
                                 fg='#444444', font=('Consolas', 9), width=6, anchor='e')
            lbl_bytes.pack(side='left', padx=(4, 0))

            # Bind para mudanças
            def _on_change(event, _bi=self.cur_block, _idx=idx,
                           _orig=orig_s, _ta=ta, _row=row,
                           _lbl=lbl_bytes, _row_bg_orig=row_bg):
                new_val = _ta.get('1.0', 'end-1c')
                self.text_blocks[_bi][_idx] = new_val
                _lbl.configure(text=f'{len(new_val)}b',
                               fg='#e06060' if len(new_val) > 500 else '#444444')
                is_mod = new_val != _orig
                bg = '#1c1600' if is_mod else '#1c1c1c'
                border = '#5a3a00' if is_mod else '#242424'
                _row.configure(bg=bg, highlightbackground=border)

            ta.bind('<KeyRelease>', _on_change)
            ta.bind('<FocusOut>',   _on_change)

            self.row_widgets.append((orig_s, ta, lbl_bytes))

        self.lbl_count.configure(text=f'{shown} / {len(strings)} strings')
        self.strings_canvas.yview_moveto(0)

    # ── Drag & drop (TkinterDnD2 opcional) ───────────────────────────────────
    def _on_drop(self, event):
        path = event.data.strip('{}')
        if path.endswith('.dat'):
            self._load_dat(path)

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Tentar usar TkinterDnD2 para drag-and-drop real (opcional)
    try:
        from tkinterdnd2 import TkinterDnD
        class App(DevilHunterEditor, TkinterDnD.Tk):
            def __init__(self):
                TkinterDnD.Tk.__init__(self)
                DevilHunterEditor.__init__(self)
                self.drop_target_register('DND_Files')
                self.dnd_bind('<<Drop>>', lambda e: self._load_dat(e.data.strip('{}')))
        app = App()
    except ImportError:
        app = DevilHunterEditor()

    app.mainloop()
