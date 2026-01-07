from pathlib import Path

# =========================
# MAPAS DE CONVERSÃO
# =========================

R = {
    '3E':'А','3F':'Б','40':'В','41':'Г','42':'Д','43':'Е','44':'Ё','45':'Ж','46':'З','47':'И',
    '48':'Й','49':'К','4A':'Л','4B':'М','4C':'Н','4D':'О','4E':'П','4F':'Р','50':'С','51':'Т',
    '52':'У','53':'Ф','54':'Х','55':'Ц','56':'Ч','57':'Ш','58':'Щ','59':'Ъ','5A':'Ы','5B':'Ь',
    '5C':'Э','5D':'Ю','5E':'Я','FF':' '
}

R_REV = {v: int(k, 16) for k, v in R.items()}

L = {
    'A':0x00,'B':0x01,'C':0x02,'D':0x03,'E':0x04,'F':0x05,'G':0x06,'H':0x07,'I':0x08,'J':0x09,
    'K':0x0A,'L':0x0B,'M':0x0C,'N':0x0D,'O':0x0E,'P':0x0F,'Q':0x10,'R':0x11,'S':0x12,'T':0x13,
    'U':0x14,'V':0x15,'W':0x16,'X':0x17,'Y':0x18,'Z':0x19,
    '0':0x1A,'1':0x1B,'2':0x1C,'3':0x1D,'4':0x1E,'5':0x1F,'6':0x20,'7':0x21,'8':0x22,'9':0x23,
    ' ':0xFF,'.':0x24
}

# =========================
# FUNÇÕES
# =========================

def decode_text(bytes_seq):
    out = ""
    for b in bytes_seq:
        hexv = f"{b:02X}"
        out += R.get(hexv, ' ')
    return out


def encode_text(text):
    data = []
    for ch in text.upper():
        if ch in R_REV:
            data.append(R_REV[ch])
        elif ch in L:
            data.append(L[ch])
    return data


def extract_blocks(data: bytes):
    blocks = []
    i = 0
    while i < len(data):
        if 0x40 <= data[i] <= 0x5E:
            start = i
            buf = []
            while i < len(data) and ((0x3E <= data[i] <= 0x5E) or data[i] == 0xFF):
                buf.append(data[i])
                i += 1

            text = decode_text(buf)
            if text.strip():
                blocks.append({
                    "offset": start,
                    "length": len(buf),
                    "original": text
                })
        else:
            i += 1
    return blocks


# =========================
# DUMP PARA TRADUÇÃO
# =========================

def dump_texts(b3d_path: Path):
    data = b3d_path.read_bytes()
    blocks = extract_blocks(data)

    out = []
    for i, b in enumerate(blocks):
        out.append(f"[{i}] OFFSET=0x{b['offset']:08X} LEN={b['length']}")
        out.append(b['original'])
        out.append("")

    dump_path = b3d_path.with_suffix(".txt")
    dump_path.write_text("\n".join(out), encoding="utf-8")

    print(f"[OK] {len(blocks)} textos extraídos")
    print(f"[OK] Arquivo gerado: {dump_path.name}")


# =========================
# APLICAR TRADUÇÃO
# =========================

def apply_translation(b3d_path: Path):
    data = bytearray(b3d_path.read_bytes())
    txt_path = b3d_path.with_suffix(".txt")

    if not txt_path.exists():
        raise FileNotFoundError("Arquivo .txt de tradução não encontrado")

    blocks = extract_blocks(data)
    lines = txt_path.read_text(encoding="utf-8").splitlines()

    i = 0
    idx = -1
    for line in lines:
        if line.startswith("["):
            idx += 1
            continue

        if not line.strip():
            continue

        block = blocks[idx]
        new_bytes = encode_text(line)

        if len(new_bytes) > block["length"]:
            print(f"[WARN] Offset 0x{block['offset']:X} excede tamanho, truncando")
            new_bytes = new_bytes[:block["length"]]

        while len(new_bytes) < block["length"]:
            new_bytes.append(0xFF)

        for j in range(block["length"]):
            data[block["offset"] + j] = new_bytes[j]

    out_path = b3d_path.with_name(b3d_path.stem + "_traduzido.b3d")
    out_path.write_bytes(data)

    print(f"[OK] Tradução aplicada: {out_path.name}")


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Uso:")
        print("  python b3d_text_editor.py dump arquivo.b3d")
        print("  python b3d_text_editor.py apply arquivo.b3d")
        sys.exit(1)

    mode = sys.argv[1]
    file = Path(sys.argv[2])

    if mode == "dump":
        dump_texts(file)
    elif mode == "apply":
        apply_translation(file)
    else:
        print("Modo inválido")
