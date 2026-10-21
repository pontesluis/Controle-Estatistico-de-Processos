import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import matplotlib.pyplot as plt

# Garante suporte a caracteres especiais no terminal do Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from cep.io_json import read_and_validate_json
from cep.modes import run_calibration, run_monitoring
from cep.report import generate_text_report, save_json_results
from cep.plots import plot_xbar_r, plot_imr, plot_p, plot_c, plot_capability
from cep.pdf_report import generate_process_pdf, consolidate_output_directory


def process_single_file(json_path: Path, args) -> Optional[Tuple[Dict[str, Any], Path, Optional[Path], Optional[Path]]]:
    """Processa um único arquivo JSON de calibração ou acompanhamento."""
    try:
        dados_entrada = read_and_validate_json(json_path)
    except Exception as e:
        print(f"\n[ERRO DE VALIDAÇÃO em {json_path}]: {e}")
        return None

    goal = dados_entrada["Goal"]
    if goal == "calibrar":
        resultados = run_calibration(dados_entrada, not args.sem_revisao, args.deltas)
    else:
        resultados = run_monitoring(dados_entrada, args.deltas, use_kalman=True, q=args.q)

    out_dir = args.saida / json_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Relatório em Texto
    report_text = generate_text_report(resultados)
    (out_dir / "relatorio.txt").write_text(report_text, encoding="utf-8")
    print(report_text)

    # 2. Resultados consolidados em JSON
    save_json_results(resultados, out_dir / "resultados.json")

    # 3. Geração e salvamento das imagens dos gráficos
    chart_p = None
    if resultados["type"] == "X":
        chart_p = out_dir / "carta_xbar_r.png"
        plot_xbar_r(resultados, chart_p)
    elif resultados["type"] == "IMR":
        chart_p = out_dir / "carta_imr.png"
        plot_imr(resultados, chart_p)
    elif resultados["type"] == "P":
        chart_p = out_dir / "carta_p.png"
        plot_p(resultados, chart_p)
    elif resultados["type"] == "C":
        chart_p = out_dir / "carta_c.png"
        plot_c(resultados, chart_p)

    cap_p = None
    if resultados["type"] in ["X", "IMR"] and ("lse" in resultados or "LSE" in dados_entrada):
        cap_p = out_dir / "capacidade.png"
        plot_capability(resultados, cap_p)

    # 4. Exibição interativa na tela (se não foi passado --sem-graficos)
    if not args.sem_graficos and chart_p and chart_p.exists():
        img_c = plt.imread(str(chart_p))
        fig1 = plt.figure(f"Carta de Controle - {json_path.stem}")
        plt.imshow(img_c)
        plt.axis("off")

        if cap_p and cap_p.exists():
            img_cap = plt.imread(str(cap_p))
            fig2 = plt.figure(f"Análise de Capacidade - {json_path.stem}")
            plt.imshow(img_cap)
            plt.axis("off")

        plt.show()

    # 5. Geração do Relatório Individual em PDF
    if not args.sem_pdf:
        pdf_ind = out_dir / "relatorio.pdf"
        generate_process_pdf(resultados, pdf_ind, chart_p, cap_p)
        print(f"📄 PDF Individual gerado: {pdf_ind.absolute()}")

    print(f"Resultados salvos com sucesso em: {out_dir.absolute()}\n")
    return resultados, out_dir, chart_p, cap_p


def main():
    parser = argparse.ArgumentParser(
        description="Software de Controle Estatístico de Processos (CEP)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("dados", type=Path, nargs="*", help="Caminho(s) para o(s) arquivo(s) JSON de entrada")
    parser.add_argument("--saida", type=Path, default=Path("saida"), help="Pasta de saída")
    parser.add_argument("--sem-revisao", action="store_true", help="Desliga a revisão iterativa")
    parser.add_argument("--kalman", action="store_true", help="Ativa o Filtro de Kalman")
    parser.add_argument("--q", type=float, default=0.05, help="Parâmetro 'q' do Kalman")
    parser.add_argument("--deltas", type=float, nargs="+", default=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0], help="Deltas em σ")
    parser.add_argument("--sem-graficos", action="store_true", help="Não abre janelas interativas na tela (gera arquivos silenciosamente)")
    parser.add_argument("--sem-pdf", action="store_true", help="Desativa a geração de relatórios em PDF")
    parser.add_argument("--pdf-saida", type=Path, default=None, help="Caminho ou nome personalizado para o PDF consolidado")
    parser.add_argument("--consolidar", action="store_true", help="Gera/atualiza o PDF consolidado com todos os processos da pasta de saída")

    args = parser.parse_args()

    # Se apenas solicitou consolidação sem passar novos arquivos
    if args.consolidar and not args.dados:
        pdf_cons = consolidate_output_directory(args.saida, args.pdf_saida)
        if pdf_cons:
            print("=" * 60)
            print("📄 RELATÓRIO PDF CONSOLIDADO GERADO COM SUCESSO:")
            print(f"   --> {pdf_cons.absolute()}")
            print("=" * 60)
        else:
            print(f"Nenhum processo anterior encontrado na pasta de saída: {args.saida}")
        return

    # Se nenhum arquivo foi informado e não foi pedido consolidar
    if not args.dados:
        parser.print_help()
        sys.exit(0)

    # Processa cada arquivo JSON informado
    processed = []
    for json_file in args.dados:
        res_tuple = process_single_file(json_file, args)
        if res_tuple:
            processed.append(res_tuple)

    # Geração do Relatório Consolidado em PDF (contendo todos os processos gerados)
    if not args.sem_pdf:
        pdf_cons = consolidate_output_directory(args.saida, args.pdf_saida)
        if pdf_cons:
            print("=" * 60)
            print("📄 RELATÓRIO PDF CONSOLIDADO (COM TODOS OS PROCESSOS):")
            print(f"   --> {pdf_cons.absolute()}")
            print("=" * 60)


if __name__ == "__main__":
    main()
