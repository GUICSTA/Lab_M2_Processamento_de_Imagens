import argparse
import json
import csv
from pathlib import Path
import cv2
import numpy as np

def segment_image(input_path, output_path, method="otsu", threshold_value=127):
    img = cv2.imread(str(input_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Não foi possível carregar a imagem de entrada: {input_path}")
    
    if method == "otsu":
        _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, thresh = cv2.threshold(img, threshold_value, 255, cv2.THRESH_BINARY)
        
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), thresh)
    print(f"Máscara salva em: {output_path}")

def analyze_mask(input_path, output_prefix, connectivity=8, min_area=0):
    input_path = Path(input_path)
    output_prefix = Path(output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Carregar máscara e Validação Programática
    mask = cv2.imread(str(input_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise FileNotFoundError(f"Não foi possível carregar a máscara: {input_path}")
    
    if len(mask.shape) != 2:
        raise ValueError("A máscara não possui canal único. Verifique a imagem de entrada.")

    valores_unicos = np.unique(mask)
    if not np.all(np.isin(valores_unicos, [0, 255])):
        print("[Aviso] A máscara contém valores diferentes de 0 e 255. Binarizando automaticamente.")
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    else:
        print("[Info] Validação programática concluída: a máscara possui apenas canal único e valores 0/255.")

    initial_fg_pixels = cv2.countNonZero(mask)
    
    initial_mask_path = output_prefix.with_name(output_prefix.name + "_initial.png")
    cv2.imwrite(str(initial_mask_path), mask)

    # 2. Rotulação com conectividade 4 e 8 para relatório/comparação
    num_labels_4, _, stats_4, centroids_4 = cv2.connectedComponentsWithStats(mask, connectivity=4)
    num_labels_8, _, stats_8, centroids_8 = cv2.connectedComponentsWithStats(mask, connectivity=8)
    
    raw_count_4 = num_labels_4 - 1
    raw_count_8 = num_labels_8 - 1
    print(f"Componentes (Conectividade 4): {raw_count_4}")
    print(f"Componentes (Conectividade 8): {raw_count_8}")

    # 3. Montar sequência morfológica
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    
    # Abertura
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    opened_path = output_prefix.with_name(output_prefix.name + "_stage1_open.png")
    cv2.imwrite(str(opened_path), opened)
    
    # Fechamento
    final_mask = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)
    final_mask_path = output_prefix.with_name(output_prefix.name + "_stage2_close.png")
    cv2.imwrite(str(final_mask_path), final_mask)
    
    final_fg_pixels = cv2.countNonZero(final_mask)

    # 4. Recontar e analisar na máscara final com a conectividade escolhida
    if connectivity not in [4, 8]:
        raise ValueError("Parâmetro --connectivity deve ser 4 ou 8.")
        
    num_labels, labels_matrix, stats, centroids = cv2.connectedComponentsWithStats(final_mask, connectivity=connectivity)
    
    csv_path = output_prefix.with_name(output_prefix.name + "_final.csv")
    kept_count = 0
    
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["label", "area", "x", "y", "width", "height", "cx", "cy", "kept"])
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            cx, cy = centroids[i]
            
            kept = area >= min_area
            if kept:
                kept_count += 1
                
            writer.writerow([i, area, x, y, w, h, round(cx, 2), round(cy, 2), str(kept).lower()])

    # 5. Gerar imagem de visualização com caixas delimitadoras e rótulos
    vis_img = cv2.cvtColor(final_mask, cv2.COLOR_GRAY2BGR)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            x, y, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            cv2.rectangle(vis_img, (x, y), (x + w, y + h), (0, 255, 0), 1)
            cv2.putText(vis_img, str(i), (x, max(y - 5, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            
    labels_vis_path = output_prefix.with_name(output_prefix.name + "_labels.png")
    cv2.imwrite(str(labels_vis_path), vis_img)

    # 6. Salvar em JSON
    summary = {
        "connectivity": connectivity,
        "min_area_filter": min_area,
        "raw_counts": {
            "connectivity_4": raw_count_4,
            "connectivity_8": raw_count_8
        },
        "filtered_count": kept_count,
        "total_components_before_filter": num_labels - 1,
        "foreground_pixels": {
            "initial": int(initial_fg_pixels),
            "final": int(final_fg_pixels)
        },
        "morphological_sequence": [
            {"operation": "morphologyEx_OPEN", "kernel_size": 3, "iterations": 1},
            {"operation": "morphologyEx_CLOSE", "kernel_size": 3, "iterations": 1}
        ]
    }
    
    summary_path = output_prefix.with_name(output_prefix.name + "_summary.json")
    with open(summary_path, mode="w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
        
    print(f"Análise concluída com sucesso! Resultados salvos em prefixo: {output_prefix}")

def main():
    parser = argparse.ArgumentParser(description="PDI Lab - Processamento de Imagens M2.1 / M2.2")
    parser.add_argument("--input", required=True, help="Caminho para a imagem ou máscara de entrada")
    parser.add_argument("--output", required=True, help="Caminho de saída ou prefixo para os resultados")
    parser.add_argument("--operation", required=True, choices=["segment", "analyze"], help="Operação a ser executada")
    parser.add_argument("--method", default="otsu", choices=["otsu", "fixed"], help="Método de limiarização para o segment")
    parser.add_argument("--threshold", type=int, default=127, help="Valor de limiar para método fixed")
    parser.add_argument("--connectivity", type=int, default=8, choices=[4, 8], help="Conectividade (4 ou 8)")
    parser.add_argument("--min-area", type=int, default=0, help="Área mínima para filtro de componentes")
    
    args = parser.parse_args()
    
    if args.operation == "segment":
        segment_image(args.input, args.output, method=args.method, threshold_value=args.threshold)
    elif args.operation == "analyze":
        analyze_mask(args.input, args.output, connectivity=args.connectivity, min_area=args.min_area)

if __name__ == "__main__":
    import os
    print("Diretório atual de trabalho:", os.getcwd())
    main()