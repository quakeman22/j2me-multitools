import struct
from PIL import Image

# ==============================================================================
# 1. CLASSES DE ESTRUTURA DE DADOS
#    Reflete as estruturas internas do ASprite.java
# ==============================================================================

class BSprite:
    def __init__(self):
        self.version = 0
        self.flags = 0
        
        self.palettes = []      # Lista de Paletas (Lista de [R, G, B, A] cores)
        self.modules = []       # Lista de Módulos (Largura, Altura)
        self.fmodules = []      # Lista de FModules (Módulo Index, Offset X, Offset Y, Flags)
        self.frames = []        # Lista de Frames (Contagem FModules, Índice Início FModule, Bounding Box)
        self.aframes = []       # Lista de AFrames (Frame Index, Duration, Offset X, Offset Y, Flags)
        self.anims = []         # Lista de Anims (Contagem AFrames, Índice Início AFrame)
        
        self.modules_data = None # Dados de pixel binários codificados
        self.data_format = 0     # I2, I4, I256, I127RLE, etc.

class FrameInfo:
    def __init__(self, fmodule_count, fmodule_start_index, bounds_rect=None):
        self.fmodule_count = fmodule_count
        self.fmodule_start_index = fmodule_start_index
        self.bounds_rect = bounds_rect or (0, 0, 0, 0) # x, y, w, h
        
class AnimInfo:
    def __init__(self, aframe_count, aframe_start_index):
        self.aframe_count = aframe_count
        self.aframe_start_index = aframe_start_index

# ==============================================================================
# 2. FUNÇÕES DE LEITURA BINÁRIA (LITTLE-ENDIAN)
#    Emulação da leitura byte-a-byte do Java
# ==============================================================================

def read_byte(f):
    """Lê 1 byte como um inteiro sem sinal (0-255)"""
    return struct.unpack('<B', f.read(1))[0]

def read_short(f):
    """Lê 2 bytes como um inteiro de 16 bits sem sinal (Little-Endian)"""
    return struct.unpack('<H', f.read(2))[0]

def read_int(f):
    """Lê 4 bytes como um inteiro de 32 bits sem sinal (Little-Endian)"""
    return struct.unpack('<I', f.read(4))[0]

# ==============================================================================
# 3. MÓDULO DE DESCODIFICAÇÃO DE PIXEL (SIMULANDO ASprite.DecodeImage)
#    Esta função converte os bytes codificados em pixels ARGB coloridos.
# ==============================================================================

def decode_module(sprite, module_index, palette_index=0):
    """
    Decodifica o array de bytes do módulo para uma imagem PIL.
    Esta é uma simulação da lógica de descompressão RLE e conversão de índice.
    """
    if module_index >= len(sprite.modules) or not sprite.modules[module_index]:
        print(f"Erro: Módulo {module_index} inválido.")
        return None

    width, height = sprite.modules[module_index]
    palette = sprite.palettes[palette_index]
    
    # Offsets de dados não são armazenados no objeto BSprite, mas seriam calculados
    # por uma função 'LoadSprite' mais completa.
    # Para este exemplo, *precisamos* do offset de início do módulo no array 'modules_data'.
    # O ASprite.java lê o tamanho do módulo, mas não armazena offsets.
    # Esta função assume que o dado binário bruto *para este módulo* é passado.
    # Iremos simular a descompressão.
    
    # --------------------------------------------------------------------------
    # --- ASSUNÇÃO: Para o extrator, precisamos do array de índices de paleta ---
    # --------------------------------------------------------------------------
    
    # *** ESTA PARTE REQUER O ALGORITMO EXATO DE COMPACTAÇÃO ***
    # Como não temos o DecodeImage, assumimos uma descompressão simples para I256.
    
    # Vamos criar um array fictício de índices de paleta (pixels_indices)
    # Aqui, na vida real, você descompactaria 'sprite.modules_data' no offset correto.
    
    total_pixels = width * height
    pixels_indices = [] # Array de índices da paleta (0 a 255)

    if sprite.data_format == 0x100: # I256 (1 byte por pixel - sem compressão)
        # Implementação simulada: Leitura direta de 1 byte por pixel (índice 0-255)
        # Se você tivesse o array 'modules_data' segmentado:
        # pixels_indices = list(raw_module_data)
        
        # Como não temos o 'raw_module_data' segmentado, vamos retornar uma imagem vazia
        # ou, se o objetivo é mostrar a estrutura, podemos simular:
        pass # A descompressão real deve vir aqui
        
    elif sprite.data_format in [0x127, 0x128]: # I127RLE, I256RLE
        # Descompressão RLE deve ser implementada aqui.
        pass
        
    # --- SIMULAÇÃO PARA DEMONSTRAÇÃO (Todos os pixels pretos) ---
    pixels_indices = [0] * total_pixels 
    # ------------------------------------------------------------
    
    
    # Agora, mapear índices para cores ARGB (32-bit integer)
    pixels_argb = []
    
    if len(palette) > 0:
        for index in pixels_indices:
            # O índice 0 geralmente é a cor transparente (ou a primeira cor da paleta)
            if index < len(palette):
                color = palette[index]
                # A paleta já deve estar no formato (R, G, B, A)
                pixels_argb.append(color)
            else:
                pixels_argb.append((0, 0, 0, 0)) # Cor transparente se o índice for inválido
    else:
        # Paleta vazia, pixels transparentes
        pixels_argb = [(0, 0, 0, 0)] * total_pixels

    # Criar a imagem PIL (RGBA)
    img = Image.new('RGBA', (width, height))
    
    # A biblioteca PIL aceita (R, G, B, A) tuplas
    img.putdata(pixels_argb)
    return img

# ==============================================================================
# 4. FUNÇÃO DE LEITURA PRINCIPAL (BSprite.Load)
#    Lê todo o arquivo binário e preenche o objeto BSprite
# ==============================================================================

def load_bsprite(file_path):
    """
    Carrega o arquivo BSprite e desserializa suas estruturas internas.
    """
    sprite = BSprite()
    
    try:
        with open(file_path, 'rb') as f:
            
            # --- 4.1. CABEÇALHO ---
            sprite.version = read_short(f) # ASprite.bs_version (0x03DF para v003)
            sprite.flags = read_int(f)     # ASprite.bs_flags
            
            if sprite.version != 0x03DF:
                print(f"Aviso: Versão BSprite ({hex(sprite.version)}) não é a esperada (0x03DF). A leitura pode falhar.")

            # --- 4.2. ESTRUTURA DO SPRITE ---
            
            # Módulos (Largura e Altura)
            n_modules = read_short(f)
            sprite.modules = []
            for _ in range(n_modules):
                w = read_byte(f)
                h = read_byte(f)
                sprite.modules.append((w, h))

            # FModules (Índices e Offsets)
            n_fmodules = read_short(f)
            sprite.fmodules = []
            for _ in range(n_fmodules):
                module_index = read_byte(f)
                offset_x = read_byte(f)
                offset_y = read_byte(f)
                flags = read_byte(f)
                sprite.fmodules.append((module_index, offset_x, offset_y, flags))
            
            # Frames (Contagem de FModules e Índice de Início)
            n_frames = read_short(f)
            sprite.frames = []
            for _ in range(n_frames):
                fmodule_count = read_byte(f)
                fmodule_start_index = read_short(f)
                bounds_rect = None
                # ASprite.java verifica se precisa ler o bounds rect.
                # Assumindo que o bounds rect é lido:
                x = read_byte(f)
                y = read_byte(f)
                w = read_byte(f)
                h = read_byte(f)
                bounds_rect = (x, y, w, h)
                sprite.frames.append(FrameInfo(fmodule_count, fmodule_start_index, bounds_rect))

            # AFrames (Quadro, Duração, Offsets)
            n_aframes = read_short(f)
            sprite.aframes = []
            for _ in range(n_aframes):
                frame_index = read_byte(f)
                duration = read_byte(f)
                offset_x = read_byte(f)
                offset_y = read_byte(f)
                flags = read_byte(f)
                sprite.aframes.append((frame_index, duration, offset_x, offset_y, flags))

            # Anims (Contagem de AFrames e Índice de Início)
            n_anims = read_short(f)
            sprite.anims = []
            anims_af_start = [read_short(f) for _ in range(n_anims)]
            anims_af_count = [read_byte(f) for _ in range(n_anims)]

            for i in range(n_anims):
                sprite.anims.append(AnimInfo(anims_af_count[i], anims_af_start[i]))
                
            # --- 4.3. PALETA DE CORES ---
            
            color_format = read_short(f) # 0x8888, 0x4444, etc.
            n_palettes = read_byte(f)    # Número de paletas (geralmente 1 ou 2)
            n_colors = read_byte(f)      # Número de cores por paleta

            sprite.palettes = []
            # O Java converte cores de 4444, 1555, 0565 para ARGB 32-bit.
            # Aqui, leremos as cores brutas e faremos uma conversão simples para ARGB (R, G, B, A).
            for p in range(n_palettes):
                palette = []
                for c in range(n_colors):
                    # Assumindo que a paleta está no formato ARGB de 32 bits (int)
                    # Se estiver em 16 bits (short), a lógica muda.
                    # O código Java lê em 32 bits depois da conversão interna.
                    # Vamos ler 32 bits (4 bytes) e decompor, ou 16 bits (2 bytes) se for 4444/1555.
                    
                    # Simulação do formato 16-bit (R5G6B5 ou similar)
                    if color_format != 0x8888 and color_format != 0x4444:
                       # Se não for 32-bit completo (raro em paletas BSprite v003), leia 2 bytes
                       raw_color = read_short(f) 
                       # Conversão de R5G6B5 para R, G, B:
                       r = ((raw_color >> 11) & 0x1F) << 3
                       g = ((raw_color >> 5) & 0x3F) << 2
                       b = (raw_color & 0x1F) << 3
                       a = 255 # Assume opaco
                    else:
                       # Assumindo 32-bit ARGB, lendo 4 bytes:
                       raw_color = read_int(f)
                       a = (raw_color >> 24) & 0xFF
                       r = (raw_color >> 16) & 0xFF
                       g = (raw_color >> 8) & 0xFF
                       b = raw_color & 0xFF
                       
                    palette.append((r, g, b, a))
                sprite.palettes.append(palette)

            # --- 4.4. DADOS DE IMAGEM CODIFICADOS ---
            
            sprite.data_format = read_short(f)
            
            # O código Java lê o tamanho do bloco para CADA módulo antes de ler o array.
            # Aqui, lemos apenas a soma dos tamanhos dos dados de imagem.
            total_data_len = 0
            for i in range(n_modules):
                module_data_len = read_short(f)
                total_data_len += module_data_len
                # Na vida real, você salvaria este 'module_data_len' para saber onde começar a ler.
                
            sprite.modules_data = f.read(total_data_len)
            
            print(f"Sucesso: Arquivo BSprite carregado com {n_modules} Módulos e {n_anims} Animações.")
            return sprite

    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {file_path}")
        return None
    except struct.error as e:
        print(f"Erro de estrutura binária: O arquivo parece estar corrompido ou o formato não é BSprite v003. Detalhes: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado durante o carregamento: {e}")
        return None

# ==============================================================================
# 5. MÓDULO DE RENDERIZAÇÃO DE FRAME
#    Combina Módulos em um Frame de Imagem
# ==============================================================================

def render_frame_to_image(sprite, frame_index, palette_index=0):
    """
    Renderiza um frame específico do sprite em uma imagem PIL.
    """
    if frame_index >= len(sprite.frames):
        return None

    frame = sprite.frames[frame_index]
    
    # 5.1. Determinar o tamanho total da imagem (baseado no Bounding Box)
    x, y, w, h = frame.bounds_rect
    
    # Se a Bounding Box for inválida, calcule uma aproximação:
    if w == 0 or h == 0:
        print("Aviso: Bounding Box inválida. Usando dimensões mínimas.")
        w, h = 1, 1 # Mínimo
    
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0)) # Imagem base transparente

    # 5.2. Iterar sobre FModules
    fmodule_end = frame.fmodule_start_index + frame.fmodule_count
    
    for fm_index in range(frame.fmodule_start_index, fmodule_end):
        if fm_index >= len(sprite.fmodules):
            print(f"Erro: Índice de FModule {fm_index} fora do alcance.")
            continue
            
        module_index, offset_x, offset_y, flags = sprite.fmodules[fm_index]
        
        # 5.3. Decodificar o Módulo (Simulado)
        # Note: A decodificação real deve ser feita uma vez e armazenada.
        module_img = decode_module(sprite, module_index, palette_index)
        
        if module_img:
            # 5.4. Aplicar transformações (Flip/Rotação)
            # Os flags (0x01, 0x02, 0x04) definem as transformações em tempo de execução
            
            # FLAG_FLIP_X (Espelhamento horizontal)
            if flags & 0x01:
                module_img = module_img.transpose(Image.FLIP_LEFT_RIGHT)
            
            # FLAG_FLIP_Y (Espelhamento vertical)
            if flags & 0x02:
                module_img = module_img.transpose(Image.FLIP_TOP_BOTTOM)
                
            # FLAG_ROT_90 (Rotação 90 graus)
            if flags & 0x04:
                module_img = module_img.transpose(Image.ROTATE_90)

            # 5.5. Colar na imagem final
            # O offset_x/y são relativos ao Frame Bounding Box (x, y)
            paste_x = offset_x - x
            paste_y = offset_y - y
            
            img.paste(module_img, (paste_x, paste_y), module_img)

    return img

# ==============================================================================
# 6. FUNÇÃO PRINCIPAL DE VISUALIZAÇÃO/EXTRAÇÃO
# ==============================================================================

def main_extractor(file_path):
    # 1. Carregar o arquivo BSprite
    sprite = load_bsprite(file_path)

    if not sprite:
        return

    # 2. Iterar e extrair todos os Frames
    output_dir = "extracted_frames"
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nTentando renderizar e extrair {len(sprite.frames)} Frames...")

    for i in range(len(sprite.frames)):
        # O código abaixo tenta renderizar o frame. Se a lógica de decodificação
        # não estiver 100% correta para o seu arquivo, esta parte pode falhar.
        
        # Usamos o índice de paleta 0 por padrão
        frame_image = render_frame_to_image(sprite, i, palette_index=0)
        
        if frame_image:
            output_filename = os.path.join(output_dir, f"frame_{i:03d}.png")
            frame_image.save(output_filename)
            # Se for um extrator, você salva a imagem:
            # print(f"  > Salvando {output_filename}")
        else:
            print(f"  > Falha ao renderizar Frame {i}.")

    # 3. Mostrar informações básicas (para fins de editor/visualizador)
    print("\n--- Informações do BSprite ---")
    print(f"Versão: {hex(sprite.version)}")
    print(f"Flags: {hex(sprite.flags)}")
    print(f"Paletas: {len(sprite.palettes)}")
    print(f"Cores por Paleta: {len(sprite.palettes[0]) if sprite.palettes else 0}")
    print(f"Total de Módulos (Peças Gráficas): {len(sprite.modules)}")
    print(f"Total de Frames (Estágios do Sprite): {len(sprite.frames)}")
    print(f"Total de Animações: {len(sprite.anims)}")
    
    if len(sprite.anims) > 0:
        anim_0 = sprite.anims[0]
        print(f"Animação 0: {anim_0.aframe_count} AFrames, Início em {anim_0.aframe_start_index}")

# ==============================================================================
# 7. EXECUÇÃO
# ==============================================================================

if __name__ == "__main__":
    # --- SUBSTITUA 'meu_sprite.bsprite' PELO CAMINHO DO SEU ARQUIVO ---
    BSPRITE_FILE = "meu_sprite.bsprite" 
    
    # Exemplo: main_extractor("data/hero.bsprite")
    
    print(f"Iniciando Extrator BSprite para o arquivo: {BSPRITE_FILE}\n")
    print("--- LEMBRETE: O ALGORITMO DE DESCOMPRESSÃO PODE PRECISAR DE AJUSTES ---")
    
    # Substitua a linha abaixo pelo seu arquivo de teste:
    # main_extractor(BSPRITE_FILE) 
    
    # Para fins de demonstração, deixaremos a chamada comentada para evitar erro 
    # de arquivo não encontrado se você executar o script sem o arquivo.
    # Se você quiser testar, descomente a linha acima e garanta que o arquivo está no local.
