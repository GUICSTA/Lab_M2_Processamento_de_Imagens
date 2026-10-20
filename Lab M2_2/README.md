Instalar dependências:
pip install opencv-python numpy

Executar a segmentação:

python main.py

python main.py --input imagem_teste.jpg --output results/estrela_mask.png --operation segment --method otsu

Executar a análise de componentes e morfologia:

python main.py --input results/estrela_mask.png --output results/estrela --operation analyze --connectivity 8 --min-area 50

Testes:

python gerar_testes.py

# Teste da Diagonal
python main.py --input images/testes/diagonal.png --output results_tests/diag --operation analyze

# Teste do Ruído e Furo
python main.py --input images/testes/ruido_furo.png --output results_tests/ruido --operation analyze --min-area 5

# Teste da Máscara Vazia
python main.py --input images/testes/vazia.png --output results_tests/vazia --operation analyze

# Teste de parâmetro inválido
python main.py --input images/testes/borda.png --output results_tests/borda --operation analyze --connectivity 5
