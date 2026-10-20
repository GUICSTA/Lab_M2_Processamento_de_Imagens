import cv2
import numpy as np
from pathlib import Path

Path("images/testes").mkdir(parents=True, exist_ok=True)

# 1. Máscara sintética com dois pixels apenas na diagonal
img_diag = np.zeros((10, 10), dtype=np.uint8)
img_diag[4, 4] = 255
img_diag[5, 5] = 255
cv2.imwrite("images/testes/diagonal.png", img_diag)

# 2. Máscara sintética com ruído isolado e um furo (para testar Abertura/Fechamento)
img_ruido = np.zeros((50, 50), dtype=np.uint8)
img_ruido[10:40, 10:40] = 255 # Objeto principal
img_ruido[20:25, 20:25] = 0   # Furo no meio (para o fechamento tapar)
img_ruido[5, 5] = 255         # Ruído isolado (para a abertura apagar)
cv2.imwrite("images/testes/ruido_furo.png", img_ruido)

# 3. Máscara Vazia
img_vazia = np.zeros((20, 20), dtype=np.uint8)
cv2.imwrite("images/testes/vazia.png", img_vazia)

# 4. Objeto que toca a borda
img_borda = np.zeros((20, 20), dtype=np.uint8)
img_borda[0:10, 0:10] = 255
cv2.imwrite("images/testes/borda.png", img_borda)

print("Imagens de teste sintéticas geradas na pasta images/testes/")