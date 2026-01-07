import sys
from pathlib import Path

# Header PNG padrão (16 bytes)
PNG_HEADER = bytes([
    0x89, 0x50, 0x4E, 0x47,
    0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D,
    0x49, 0x48, 0x44, 0x52
])

HEADER_SIZE_B3D = 14
HEADER_SIZE_PNG = 16


def b3d_to_png(b3d_path: Path):
    data = b3d_path.read_bytes()

    if len(data) <= HEADER_SIZE_B3D:
        raise ValueError("Arquivo B3D muito pequeno")

    # Copia header original
    original_header = data[:HEADER_SIZE_B3D]
    image_data = data[HEADER_SIZE_B3D:]

    # Cria PNG válido
    png_data = PNG_HEADER + image_data

    png_path = b3d_path.with_suffix(".png")
    header_path = b3d_path.with_suffix(".hdr")

    png_path.write_bytes(png_data)
    header_path.write_bytes(original_header)

    print(f"[OK] PNG gerado: {png_path.name}")
    print(f"[OK] Header salvo: {header_path.name}")


def png_to_b3d(png_path: Path):
    data = png_path.read_bytes()

    if not data.startswith(PNG_HEADER):
        raise ValueError("Arquivo PNG inválido ou não convertido pelo script")

    header_path = png_path.with_suffix(".hdr")
    if not header_path.exists():
        raise FileNotFoundError("Header original (.hdr) não encontrado")

    original_header = header_path.read_bytes()
    image_data = data[HEADER_SIZE_PNG:]

    # Reconstrói B3D
    b3d_data = original_header + image_data
    b3d_path = png_path.with_suffix(".b3d")

    b3d_path.write_bytes(b3d_data)

    print(f"[OK] B3D reconstruído: {b3d_path.name}")


def main():
    if len(sys.argv) != 3:
        print("Uso:")
        print("  python b3d_png_tool.py to_png arquivo.b3d")
        print("  python b3d_png_tool.py to_b3d arquivo.png")
        return

    mode = sys.argv[1]
    file_path = Path(sys.argv[2])

    if not file_path.exists():
        print("Arquivo não encontrado")
        return

    if mode == "to_png":
        b3d_to_png(file_path)
    elif mode == "to_b3d":
        png_to_b3d(file_path)
    else:
        print("Modo inválido. Use to_png ou to_b3d.")


if __name__ == "__main__":
    main()
