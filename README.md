# 🗺️ Note Maps v2.0

Sistema desktop (Python + CustomTkinter) para leitura, conversão e relatórios de planilhas da DPGO / COPESP.

## 🚀 Novidades v2.0
- **Nova aba: Relatório por CNPJ/PI** — gera PDF individual por prestador+PI pronto para e-mail
- Correção do bug de sobrescrita do arquivo mapa
- Correção do bug do Relatório Detalhado não carregar sem visitar a aba antes
- Validação de extensão e tamanho de arquivo (limite 50 MB)
- Proteção contra path traversal na pasta de destino
- Suporte automático a qualquer nome de aba Excel (não apenas "Sheet1")
- Sanitização de nomes de arquivos gerados

## 💻 Instalação
```bash
pip install pandas fpdf customtkinter openpyxl
python main.py
```

## 📂 Arquivos
| Arquivo | Descrição |
|---|---|
| `main.py` | Janela principal, menu lateral, estado global |
| `conversor.py` | Aba "Gerar Extrato NF" → .xlsx agrupado |
| `gerador_pdf.py` | Aba "Relatório Detalhado" → PDF por fatura |
| `relatorio_cnpj_pdf.py` | **NOVO** Aba "Relatório por CNPJ/PI" → PDFs por prestador |

## 👨‍💻 Desenvolvedor
Thallisson Henrique — Auxiliar Financeiro / COPESP
