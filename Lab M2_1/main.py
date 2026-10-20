import argparse
from pathlib import Path
import cv2

def segment_image(input_path, output_path, method="otsu", threshold_value=127):
    """
    Laboratório M2.1
    """
    # Carregar a imagem de entrada em escala de cinza
    img = cv2.imread(str(input_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Não foi possível carregar a imagem de entrada: {input_path}")
    
    # Aplicar limiarização conforme o método escolhido
    if method == "otsu":
        _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, thresh = cv2.threshold(img, threshold_value, 255, cv2.THRESH_BINARY)
        
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Salvar a máscara binária resultante
    cv2.imwrite(str(output_path), thresh)
    print(f"Máscara binária salva com sucesso em: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="PDI Lab - M2.1 Segmentação de Imagens")
    parser.add_argument("--input", required=True, help="Caminho para a imagem original de entrada")
    parser.add_argument("--output", required=True, help="Caminho para salvar a máscara binária gerada")
    parser.add_argument("--method", default="otsu", choices=["otsu", "fixed"], help="Método de limiarização (otsu ou fixed)")
    parser.add_argument("--threshold", type=int, default=127, help="Valor de limiar para o método fixed")
    
    args = parser.parse_args()
    segment_image(args.input, args.output, method=args.method, threshold_value=args.threshold)

if __name__ == "__main__":
    main()