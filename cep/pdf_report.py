"""
Módulo de geração de relatórios em PDF para Controle Estatístico de Processos (CEP).
Suporta geração de relatórios individuais por processo e relatórios consolidados em PDF
contendo múltiplos processos (calibrações e acompanhamentos), com cartas de controle,
análise de capacidade, tabelas de deslocamento e métricas de diagnóstico.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages

# Paleta de Cores Profissional
C_NAVY_DARK = "#0F172A"
C_NAVY_LIGHT = "#1E293B"
C_BLUE_PRIMARY = "#1E40AF"
C_BLUE_BADGE = "#2563EB"
C_AMBER_BADGE = "#D97706"
C_GREEN = "#16A34A"
C_RED = "#DC2626"
C_ORANGE = "#EA580C"
C_BG_CARD = "#F8FAFC"
C_BORDER = "#CBD5E1"
C_TEXT_DARK = "#0F172A"
C_TEXT_MUTED = "#64748B"


def _add_page_header(ax, title: str, subtitle: str, badge_text: str, badge_color: str):
    """Desenha a faixa de cabeçalho padronizada no topo da página."""
    # Fundo do cabeçalho
    ax.add_patch(patches.Rectangle((0.0, 0.925), 1.0, 0.075, facecolor=C_NAVY_DARK, edgecolor="none", zorder=2))
    
    # Textos do título
    ax.text(0.04, 0.965, title, fontsize=12, fontweight="bold", color="white", va="center", zorder=3)
    ax.text(0.04, 0.940, subtitle, fontsize=8, color="#94A3B8", va="center", zorder=3)
    
    # Badge lateral
    badge_w, badge_h = 0.22, 0.035
    bx = 0.96 - badge_w
    by = 0.945
    ax.add_patch(patches.FancyBboxPatch(
        (bx, by), badge_w, badge_h,
        boxstyle="round,pad=0.005,rounding_size=0.01",
        facecolor=badge_color, edgecolor="none", zorder=3
    ))
    ax.text(bx + badge_w / 2.0, by + badge_h / 2.0, badge_text,
            fontsize=8.5, fontweight="bold", color="white", ha="center", va="center", zorder=4)


def _add_page_footer(ax, page_num: int, total_pages: Optional[int] = None):
    """Desenha o rodapé técnico da página."""
    ax.plot([0.04, 0.96], [0.035, 0.035], color=C_BORDER, linewidth=0.8, zorder=2)
    ax.text(0.04, 0.020, "Software de Controle Estatístico de Processos (CEP) – UnB / FGA",
            fontsize=7.5, color=C_TEXT_MUTED, va="center", zorder=3)
    pag_str = f"Página {page_num} de {total_pages}" if total_pages else f"Página {page_num}"
    ax.text(0.96, 0.020, pag_str, fontsize=7.5, color=C_TEXT_MUTED, ha="right", va="center", zorder=3)


def _draw_card_box(ax, x, y, w, h, title: str, bg_color=C_BG_CARD, border_color=C_BORDER):
    """Desenha um card estilizado com título."""
    # Fundo e borda
    ax.add_patch(patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.005,rounding_size=0.012",
        facecolor=bg_color, edgecolor=border_color, linewidth=1.0, zorder=1
    ))
    # Barra de título do card
    th = 0.028
    ax.add_patch(patches.FancyBboxPatch(
        (x, y + h - th), w, th,
        boxstyle="round,pad=0.005,rounding_size=0.012",
        facecolor=border_color, edgecolor="none", zorder=2
    ))
    # Retângulo inferior da barra de título para não arredondar a junção
    ax.add_patch(patches.Rectangle((x, y + h - th), w, th * 0.5, facecolor=border_color, edgecolor="none", zorder=2))
    ax.text(x + 0.015, y + h - th / 2.0, title, fontsize=8.5, fontweight="bold", color=C_NAVY_DARK, va="center", zorder=3)


def _get_process_status(res: Dict[str, Any]) -> Tuple[str, str, str]:
    """Retorna (status_texto, detalhe, cor) para o diagnóstico do processo."""
    goal = res.get("goal", "Calibrar")
    if goal == "Calibrar":
        excl = res.get("excluded", [])
        if excl:
            return "Revisado (Fase I)", f"{len(excl)} amostras excluídas", C_AMBER_BADGE
        return "Estável (Fase I)", "Sem exclusões de amostras", C_GREEN
    else:
        # Acompanhamento: verificar violações Western Electric
        we_x = res.get("we_rules_x", {})
        we_r = res.get("we_rules_r", {}) or res.get("we_rules_mr", {})
        we_p = res.get("we_rules_p", {})
        we_c = res.get("we_rules_c", {})
        
        all_rules = [we_x, we_r, we_p, we_c]
        total_violators = sum(len(idxs) for rules in all_rules for idxs in rules.values())
        
        if total_violators > 0:
            return "Atenção (Fase II)", f"{total_violators} violações de regras", C_RED
        return "Sob Controle", "Processo em conformidade", C_GREEN


def _build_page1_process(pdf: PdfPages, res: Dict[str, Any], chart_img_path: Optional[Path],
                         page_num: int, total_pages: Optional[int] = None):
    """Constrói a Página 1 de um processo: Ficha Técnica, KPIs e Carta de Controle."""
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    meta = res.get("metadata", {})
    label = meta.get("Label", "Processo")
    goal = res.get("goal", "Calibrar")
    chart_type = res.get("type", "X")
    m = res.get("m_total", len(res.get("data_raw", [])))
    n = res.get("n", "Variável")
    unit = meta.get("Unit", "-")
    created_by = meta.get("Created_by", "Anônimo")
    measured_at = meta.get("Measured_at", "N/A")

    badge_txt = "FASE I: CALIBRAÇÃO" if goal == "Calibrar" else "FASE II: ACOMPANHAMENTO"
    badge_col = C_BLUE_BADGE if goal == "Calibrar" else C_AMBER_BADGE

    # 1. Cabeçalho
    _add_page_header(ax, f"RELATÓRIO CEP: {label.upper()}",
                     f"Carta de Controle Tipo {chart_type} | Objetivo: {goal}",
                     badge_txt, badge_col)

    # 2. Faixa de Metadados
    ax.add_patch(patches.FancyBboxPatch(
        (0.04, 0.840), 0.92, 0.070,
        boxstyle="round,pad=0.005,rounding_size=0.01",
        facecolor=C_BG_CARD, edgecolor=C_BORDER, linewidth=1.0, zorder=1
    ))
    ax.text(0.06, 0.885, f"Identificação: {label}", fontsize=11, fontweight="bold", color=C_NAVY_DARK, zorder=2)
    ax.text(0.55, 0.885, f"Tipo de Carta: Carta {chart_type}", fontsize=10, fontweight="bold", color=C_BLUE_PRIMARY, zorder=2)
    
    meta_line = (f"Data/Hora: {measured_at}   |   Responsável: {created_by}   |   "
                 f"Unidade: {unit}   |   Amostras (m): {m}   |   Subgrupo (n): {n}")
    ax.text(0.06, 0.855, meta_line, fontsize=8, color=C_TEXT_MUTED, zorder=2)

    # 3. Três Cards de Resumo
    fl = res.get("final_limits", {})
    cap = res.get("capability", {})
    status_title, status_sub, status_col = _get_process_status(res)

    card_y = 0.690
    card_h = 0.138
    card_w = 0.293

    # Card 1: Limites de Controle
    _draw_card_box(ax, 0.04, card_y, card_w, card_h, "LIMITES DE CONTROLE")
    cy = card_y + card_h - 0.045
    if chart_type in ["X", "IMR"]:
        t1 = "X̄" if chart_type == "X" else "I"
        t2 = "R" if chart_type == "X" else "MR"
        k2 = "r" if chart_type == "X" else "mr"
        ax.text(0.055, cy, f"Carta {t1}:", fontsize=7.5, fontweight="bold", color=C_TEXT_DARK, zorder=3)
        ax.text(0.055, cy - 0.016, f"LIC={fl.get('lic_x', 0):.4f} | LC={fl.get('lc_x', 0):.4f} | LSC={fl.get('lsc_x', 0):.4f}",
                fontsize=7.0, color=C_TEXT_MUTED, zorder=3)
        ax.text(0.055, cy - 0.035, f"Carta {t2}:", fontsize=7.5, fontweight="bold", color=C_TEXT_DARK, zorder=3)
        ax.text(0.055, cy - 0.051, f"LIC={fl.get('lic_' + k2, 0):.4f} | LC={fl.get('lc_' + k2, 0):.4f} | LSC={fl.get('lsc_' + k2, 0):.4f}",
                fontsize=7.0, color=C_TEXT_MUTED, zorder=3)
        sig = fl.get("sigma_hat", 0)
        ax.text(0.055, cy - 0.072, f"σ̂ do Processo = {sig:.6f}", fontsize=8.0, fontweight="bold", color=C_BLUE_PRIMARY, zorder=3)
    elif chart_type == "P":
        pbar = fl.get("pbar", 0)
        ax.text(0.055, cy, "Fração Não Conforme:", fontsize=7.5, fontweight="bold", color=C_TEXT_DARK, zorder=3)
        ax.text(0.055, cy - 0.020, f"LC (p̄) = {pbar:.6f} ({pbar*100:.2f}%)", fontsize=8.0, color=C_BLUE_PRIMARY, zorder=3)
        ax.text(0.055, cy - 0.045, "Limites por Amostra:", fontsize=7.5, fontweight="bold", color=C_TEXT_DARK, zorder=3)
        ax.text(0.055, cy - 0.065, "Limites dinâmicos (função de n)", fontsize=7.0, color=C_TEXT_MUTED, zorder=3)
    elif chart_type == "C":
        ax.text(0.055, cy, "Contagem de Defeitos:", fontsize=7.5, fontweight="bold", color=C_TEXT_DARK, zorder=3)
        ax.text(0.055, cy - 0.020, f"LIC = {fl.get('lic', 0):.4f}", fontsize=7.5, color=C_TEXT_MUTED, zorder=3)
        ax.text(0.055, cy - 0.038, f"LC (c̄) = {fl.get('lc', 0):.4f}", fontsize=8.0, fontweight="bold", color=C_BLUE_PRIMARY, zorder=3)
        ax.text(0.055, cy - 0.056, f"LSC = {fl.get('lsc', 0):.4f}", fontsize=7.5, color=C_TEXT_MUTED, zorder=3)

    # Card 2: Capacidade / Desempenho
    _draw_card_box(ax, 0.353, card_y, card_w, card_h, "CAPACIDADE / DESEMPENHO")
    c2y = card_y + card_h - 0.045
    if cap:
        rcp = cap.get("RCP", 0)
        rcpk = cap.get("RCPk", 0)
        ppm = cap.get("ppm", 0)
        k_val = cap.get("k", 0)
        cap_stat = "Capaz" if rcpk >= 1.33 else ("Marginal" if rcpk >= 1.0 else "Incapaz")
        stat_c = C_GREEN if rcpk >= 1.33 else (C_AMBER_BADGE if rcpk >= 1.0 else C_RED)
        
        ax.text(0.368, c2y, f"RCP = {rcp:.3f}   |   RCPk = {rcpk:.3f}", fontsize=8.0, fontweight="bold", color=C_TEXT_DARK, zorder=3)
        ax.text(0.368, c2y - 0.020, f"Desvio Alvo (k) = {k_val:.4f}", fontsize=7.5, color=C_TEXT_MUTED, zorder=3)
        ax.text(0.368, c2y - 0.040, f"Fora de espec.: {ppm:.2f} ppm", fontsize=7.5, color=C_TEXT_MUTED, zorder=3)
        
        # Badge de capacidade
        ax.add_patch(patches.FancyBboxPatch(
            (0.368, c2y - 0.076), 0.16, 0.026,
            boxstyle="round,pad=0.003,rounding_size=0.008",
            facecolor=stat_c, edgecolor="none", zorder=3
        ))
        ax.text(0.368 + 0.08, c2y - 0.063, f"Classif.: {cap_stat}", fontsize=7.5, fontweight="bold",
                color="white", ha="center", va="center", zorder=4)
    else:
        if chart_type == "P":
            pbar = fl.get("pbar", 0)
            ax.text(0.368, c2y, "Métricas de Atributos:", fontsize=7.5, fontweight="bold", color=C_TEXT_DARK, zorder=3)
            ax.text(0.368, c2y - 0.020, f"Fração Não Conforme: {pbar*100:.3f}%", fontsize=8.0, color=C_TEXT_DARK, zorder=3)
            ax.text(0.368, c2y - 0.040, f"Estimativa PPM: {pbar*1_000_000:.1f} ppm", fontsize=8.0, color=C_BLUE_PRIMARY, zorder=3)
        elif chart_type == "C":
            cbar = fl.get("lc", 0)
            ax.text(0.368, c2y, "Métricas de Atributos:", fontsize=7.5, fontweight="bold", color=C_TEXT_DARK, zorder=3)
            ax.text(0.368, c2y - 0.020, f"Defeitos / amostra: {cbar:.4f}", fontsize=8.0, color=C_BLUE_PRIMARY, zorder=3)
            ax.text(0.368, c2y - 0.040, "Monitoramento Poisson", fontsize=7.5, color=C_TEXT_MUTED, zorder=3)

    # Card 3: Diagnóstico & Estabilidade
    _draw_card_box(ax, 0.667, card_y, card_w, card_h, "DIAGNÓSTICO")
    c3y = card_y + card_h - 0.045
    
    # Badge do Status
    ax.add_patch(patches.FancyBboxPatch(
        (0.682, c3y - 0.005), 0.22, 0.026,
        boxstyle="round,pad=0.003,rounding_size=0.008",
        facecolor=status_col, edgecolor="none", zorder=3
    ))
    ax.text(0.682 + 0.11, c3y + 0.008, status_title, fontsize=8.0, fontweight="bold",
            color="white", ha="center", va="center", zorder=4)
    ax.text(0.682, c3y - 0.028, status_sub, fontsize=7.5, color=C_TEXT_MUTED, zorder=3)

    if goal == "Calibrar":
        iters = len(res.get("iterations", []))
        excl = res.get("excluded", [])
        ax.text(0.682, c3y - 0.050, f"Iterações na Fase I: {iters}", fontsize=7.5, color=C_TEXT_DARK, zorder=3)
        excl_str = str(excl) if excl else "Nenhuma"
        ax.text(0.682, c3y - 0.070, f"Excluídas: {excl_str}", fontsize=7.0, color=C_TEXT_MUTED, zorder=3)
    else:
        has_k = len(res.get("kalman", [])) > 0
        dh = res.get("delta_hat_analysis")
        if dh:
            ax.text(0.682, c3y - 0.050, f"Desloc. estimado (δ̂): {dh.get('delta', 0):.2f} σ",
                    fontsize=7.5, fontweight="bold", color=C_ORANGE, zorder=3)
        ax.text(0.682, c3y - 0.070, f"Filtro Kalman: {'Ativado' if has_k else 'Não'}",
                fontsize=7.0, color=C_TEXT_MUTED, zorder=3)

    # 4. Carta de Controle Gráfica
    chart_box_y = 0.055
    chart_box_h = 0.615
    ax.add_patch(patches.FancyBboxPatch(
        (0.04, chart_box_y), 0.92, chart_box_h,
        boxstyle="round,pad=0.005,rounding_size=0.012",
        facecolor="white", edgecolor=C_BORDER, linewidth=1.0, zorder=1
    ))
    
    # Barra de título da carta
    ct_h = 0.030
    ax.add_patch(patches.FancyBboxPatch(
        (0.04, chart_box_y + chart_box_h - ct_h), 0.92, ct_h,
        boxstyle="round,pad=0.005,rounding_size=0.012",
        facecolor=C_NAVY_LIGHT, edgecolor="none", zorder=2
    ))
    ax.add_patch(patches.Rectangle((0.04, chart_box_y + chart_box_h - ct_h), 0.92, ct_h * 0.5,
                                   facecolor=C_NAVY_LIGHT, edgecolor="none", zorder=2))
    ax.text(0.06, chart_box_y + chart_box_h - ct_h / 2.0,
            f"CARTA DE CONTROLE: {chart_type.upper()} ({goal.upper()})",
            fontsize=9.0, fontweight="bold", color="white", va="center", zorder=3)

    if chart_img_path and Path(chart_img_path).exists():
        img = plt.imread(str(chart_img_path))
        img_ax = fig.add_axes([0.05, chart_box_y + 0.01, 0.90, chart_box_h - ct_h - 0.02])
        img_ax.imshow(img)
        img_ax.axis("off")
    else:
        ax.text(0.50, chart_box_y + chart_box_h / 2.0, "Imagem da Carta de Controle não disponível",
                fontsize=10, color=C_TEXT_MUTED, ha="center", va="center", zorder=3)

    # 5. Rodapé
    _add_page_footer(ax, page_num, total_pages)

    pdf.savefig(fig, dpi=150)
    plt.close(fig)


def _build_page2_process(pdf: PdfPages, res: Dict[str, Any], cap_img_path: Optional[Path],
                         page_num: int, total_pages: Optional[int] = None):
    """Constrói a Página 2 de um processo: Análise de Deslocamento, Capacidade e Violações."""
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    meta = res.get("metadata", {})
    label = meta.get("Label", "Processo")
    goal = res.get("goal", "Calibrar")
    chart_type = res.get("type", "X")
    cap = res.get("capability")

    badge_txt = "FASE I: CALIBRAÇÃO" if goal == "Calibrar" else "FASE II: ACOMPANHAMENTO"
    badge_col = C_BLUE_BADGE if goal == "Calibrar" else C_AMBER_BADGE

    # 1. Cabeçalho
    _add_page_header(ax, f"{label.upper()} – DETALHAMENTO TÉCNICO",
                     "Análise de Capacidade, Probabilidades de Deslocamento e Baseline",
                     badge_txt, badge_col)

    top_y = 0.505
    top_h = 0.405

    # 2. Bloco Superior: Se houver capacidade (Variáveis X / IMR)
    if cap and cap_img_path and Path(cap_img_path).exists():
        # Lado Esquerdo: Imagem do Gráfico de Capacidade
        _draw_card_box(ax, 0.04, top_y, 0.45, top_h, "DISTRIBUIÇÃO E LIMITES DE ESPECIFICAÇÃO")
        img_cap = plt.imread(str(cap_img_path))
        cap_ax = fig.add_axes([0.05, top_y + 0.015, 0.43, top_h - 0.045])
        cap_ax.imshow(img_cap)
        cap_ax.axis("off")

        # Lado Direito: Tabela / Métricas detalhadas de Capacidade
        _draw_card_box(ax, 0.51, top_y, 0.45, top_h, "ÍNDICES DE CAPACIDADE DO PROCESSO")
        fl = res.get("final_limits", {})
        lse = res.get("lse", 0)
        lie = res.get("lie", 0)
        lc = fl.get("lc_x", 0)
        sig = fl.get("sigma_hat", 0)
        
        cap_rows = [
            ["Limite Inferior (LIE)", f"{lie:.4f}"],
            ["Alvo / Centro (LC)", f"{lc:.4f}"],
            ["Limite Superior (LSE)", f"{lse:.4f}"],
            ["Desvio Padrão (σ̂)", f"{sig:.6f}"],
            ["Largura Especificação", f"{(lse - lie):.4f}"],
            ["Largura Natural (6σ)", f"{(6 * sig):.4f}"],
            ["Índice RCP (Cp)", f"{cap.get('RCP', 0):.4f}"],
            ["Índice RCPS (Cps)", f"{cap.get('RCPS', 0):.4f}"],
            ["Índice RCPI (Cpi)", f"{cap.get('RCPI', 0):.4f}"],
            ["Índice RCPk (Cpk)", f"{cap.get('RCPk', 0):.4f}"],
            ["Desvio de Centralização (k)", f"{cap.get('k', 0):.4f}"],
            ["Estimativa Fora Espec.", f"{cap.get('ppm', 0):.2f} ppm"]
        ]
        
        if "capability_atual" in res:
            cap_rows.append(["RCPk Atual (Média Deslocada)", f"{res['capability_atual'].get('RCPk', 0):.4f}"])

        tab_cap = ax.table(
            cellText=cap_rows,
            colWidths=[0.24, 0.17],
            loc="center",
            bbox=[0.53, top_y + 0.02, 0.41, top_h - 0.05]
        )
        tab_cap.auto_set_font_size(False)
        tab_cap.set_fontsize(7.5)
        tab_cap.set_zorder(10)
        for (r, c), cell in tab_cap.get_celld().items():
            cell.set_zorder(10)
            cell.set_edgecolor(C_BORDER)
            if c == 0:
                cell.set_text_props(fontweight="bold", color=C_TEXT_DARK)
            else:
                cell.set_text_props(color=C_BLUE_PRIMARY if "RCP" in cap_rows[r][0] else C_TEXT_DARK)
            cell.set_facecolor("#FFFFFF" if r % 2 == 0 else "#F8FAFC")
    else:
        # Se atributos ou sem gráfico de capacidade: Métricas gerais
        _draw_card_box(ax, 0.04, top_y, 0.92, top_h, "MÉTRICAS DO PROCESSO")
        fl = res.get("final_limits", {})
        if chart_type == "P":
            pbar = fl.get("pbar", 0)
            ppm = pbar * 1_000_000
            ax.text(0.08, top_y + top_h - 0.06, f"Fração Média Não Conforme (p̄): {pbar:.6f} ({pbar*100:.4f}%)",
                    fontsize=10, fontweight="bold", color=C_BLUE_PRIMARY, zorder=3)
            ax.text(0.08, top_y + top_h - 0.09, f"Taxa de Não Conformes: {ppm:.2f} ppm", fontsize=9, color=C_TEXT_DARK, zorder=3)
            ax.text(0.08, top_y + top_h - 0.12, "Limites de Controle Dinâmicos por Amostra: Calculados conforme tamanho do subgrupo n(i)",
                    fontsize=8.5, color=C_TEXT_MUTED, zorder=3)
        elif chart_type == "C":
            cbar = fl.get("lc", 0)
            ax.text(0.08, top_y + top_h - 0.06, f"Média de Defeitos por Unidade Inspecionada (c̄): {cbar:.4f}",
                    fontsize=10, fontweight="bold", color=C_BLUE_PRIMARY, zorder=3)
            ax.text(0.08, top_y + top_h - 0.09, f"Limites de Controle: LIC = {fl.get('lic', 0):.4f} | LSC = {fl.get('lsc', 0):.4f}",
                    fontsize=9, color=C_TEXT_DARK, zorder=3)

    # 3. Bloco Inferior Esquerdo: Tabela de Deslocamento (β, Pd, ARL1)
    bot_y = 0.055
    bot_h = 0.430
    _draw_card_box(ax, 0.04, bot_y, 0.45, bot_h, "ANÁLISE DE DESLOCAMENTO (β, Pd, ARL1)")
    
    shifts = res.get("shift", [])
    shift_headers = ["Desloc. (δ)", "Risco β", "Detecção (Pd)", "ARL1"]
    shift_rows = []
    for s in shifts:
        shift_rows.append([
            f"{s.get('delta', 0):.2f} σ",
            f"{s.get('beta', 0):.4f}",
            f"{s.get('Pd', 0):.4f}",
            f"{s.get('ARL1', 0):.2f}"
        ])
        
    tab_shift = ax.table(
        cellText=shift_rows,
        colLabels=shift_headers,
        colWidths=[0.11, 0.10, 0.12, 0.10],
        loc="center",
        bbox=[0.055, bot_y + 0.08, 0.42, bot_h - 0.13]
    )
    tab_shift.auto_set_font_size(False)
    tab_shift.set_fontsize(8.0)
    tab_shift.set_zorder(10)
    
    for (r, c), cell in tab_shift.get_celld().items():
        cell.set_zorder(10)
        cell.set_edgecolor(C_BORDER)
        if r == 0:
            cell.set_facecolor(C_NAVY_LIGHT)
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("#FFFFFF" if r % 2 == 1 else "#F8FAFC")
            cell.set_text_props(color=C_TEXT_DARK)

    if goal == "Acompanhar" and "delta_hat_analysis" in res:
        dh = res["delta_hat_analysis"]
        ax.text(0.06, bot_y + 0.035,
                f"Deslocamento Atual (δ̂) = {dh.get('delta', 0):.2f} σ   |   Pd = {dh.get('Pd', 0):.4f}   |   ARL1 = {dh.get('ARL1', 0):.2f}",
                fontsize=8.0, fontweight="bold", color=C_ORANGE, zorder=3)
    else:
        ax.text(0.06, bot_y + 0.035, "ARL1 = Número médio de amostras até detectar o deslocamento",
                fontsize=7.0, color=C_TEXT_MUTED, zorder=3)

    # 4. Bloco Inferior Direito: Baseline ou Violações Western Electric
    _draw_card_box(ax, 0.51, bot_y, 0.45, bot_h,
                   "PARÂMETROS BASELINE (FASE II)" if goal == "Calibrar" else "VIOLAÇÕES E REGRAS DETECTADAS")
    
    if goal == "Calibrar":
        fl = res.get("final_limits", {})
        if chart_type in ["X", "IMR"]:
            base = {
                "LSC": round(fl.get("lsc_x", 0), 6),
                "LC": round(fl.get("lc_x", 0), 6),
                "LIC": round(fl.get("lic_x", 0), 6),
                "Sigma": round(fl.get("sigma_hat", 0), 6)
            }
        elif chart_type == "P":
            base = {"LC": round(fl.get("pbar", 0), 6)}
        else:
            base = {"LC": round(fl.get("lc", 0), 6)}
            
        base_json = json.dumps(base, indent=2)
        ax.text(0.53, bot_y + bot_h - 0.055, "Parâmetros calculados prontos para monitoramento:",
                fontsize=8.0, color=C_TEXT_DARK, zorder=3)
        
        # Caixa de código
        ax.add_patch(patches.FancyBboxPatch(
            (0.53, bot_y + 0.12), 0.41, 0.22,
            boxstyle="round,pad=0.005,rounding_size=0.008",
            facecolor="#1E293B", edgecolor="none", zorder=3
        ))
        ax.text(0.55, bot_y + 0.23, base_json, fontsize=8.5, family="monospace", color="#38BDF8", va="center", zorder=4)
        
        excl = res.get("excluded", [])
        if excl:
            ax.text(0.53, bot_y + 0.065, f"Amostras eliminadas por violação de 3σ: {excl}",
                    fontsize=7.5, fontweight="bold", color=C_RED, zorder=3)
        else:
            ax.text(0.53, bot_y + 0.065, "Nenhuma amostra violou os limites de controle (3σ).",
                    fontsize=7.5, color=C_GREEN, zorder=3)
    else:
        # Modo Acompanhar: Violações Western Electric
        we_x = res.get("we_rules_x", {})
        we_r = res.get("we_rules_r", {}) or res.get("we_rules_mr", {}) or res.get("we_rules_p", {}) or res.get("we_rules_c", {})
        
        rule_lines = [
            ("R1 (Fora de 3σ)", "1 ponto além da Zona A"),
            ("R2 (Zona A)", "2 de 3 pontos consecutivos na Zona A"),
            ("R3 (Zona B)", "4 de 5 pontos consecutivos na Zona B ou além"),
            ("R4 (Zona C)", "8 pontos consecutivos do mesmo lado da LC")
        ]
        
        ax.text(0.53, bot_y + bot_h - 0.055, "Regras do Western Electric Handbook:", fontsize=8.0, fontweight="bold", color=C_TEXT_DARK, zorder=3)
        
        ry = bot_y + bot_h - 0.085
        for r_name, r_desc in rule_lines:
            rk = r_name.split()[0]
            viols_x = we_x.get(rk, [])
            viols_r = we_r.get(rk, [])
            v_all = sorted(list(set(viols_x + viols_r)))
            
            c_tag = C_RED if v_all else C_GREEN
            txt_v = f"Amostras: {v_all}" if v_all else "Nenhuma violação"
            
            ax.text(0.53, ry, f"• {r_name}: {r_desc}", fontsize=7.5, color=C_TEXT_DARK, zorder=3)
            ax.text(0.55, ry - 0.020, txt_v, fontsize=7.0, fontweight="bold", color=c_tag, zorder=3)
            ry -= 0.052

    # 5. Rodapé
    _add_page_footer(ax, page_num, total_pages)

    pdf.savefig(fig, dpi=150)
    plt.close(fig)


def _build_executive_cover_page(pdf: PdfPages, entries: List[Dict[str, Any]], total_pages: int):
    """Constrói a capa e o sumário executivo quando múltiplos processos são consolidados."""
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Banner Superior Principal
    ax.add_patch(patches.Rectangle((0.0, 0.88), 1.0, 0.12, facecolor=C_NAVY_DARK, edgecolor="none", zorder=2))
    ax.text(0.05, 0.955, "RELATÓRIO CONSOLIDADO DE PROCESSOS (CEP)", fontsize=15, fontweight="bold", color="white", zorder=3)
    ax.text(0.05, 0.925, "Controle Estatístico de Processos – Universidade de Brasília (UnB / FGA)",
            fontsize=9.5, color="#94A3B8", zorder=3)
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    ax.text(0.95, 0.925, f"Emissão: {now_str}", fontsize=8.5, color="#CBD5E1", ha="right", zorder=3)

    # Quatro Mini Cards de Métricas Gerais
    n_total = len(entries)
    n_cal = sum(1 for e in entries if e.get("goal") == "Calibrar")
    n_mon = sum(1 for e in entries if e.get("goal") == "Acompanhar")
    n_capaz = sum(1 for e in entries if e.get("capability", {}).get("RCPk", 0) >= 1.33)

    metrics = [
        ("Total de Processos", str(n_total), C_BLUE_PRIMARY),
        ("Fase I (Calibração)", str(n_cal), C_BLUE_BADGE),
        ("Fase II (Acompanhar)", str(n_mon), C_AMBER_BADGE),
        ("Processos Capazes", str(n_capaz), C_GREEN)
    ]

    card_w = 0.215
    for idx, (m_title, m_val, m_col) in enumerate(metrics):
        cx = 0.04 + idx * 0.235
        ax.add_patch(patches.FancyBboxPatch(
            (cx, 0.770), card_w, 0.085,
            boxstyle="round,pad=0.005,rounding_size=0.01",
            facecolor=C_BG_CARD, edgecolor=C_BORDER, linewidth=1.0, zorder=2
        ))
        ax.text(cx + card_w / 2.0, 0.825, m_val, fontsize=16, fontweight="bold", color=m_col, ha="center", zorder=3)
        ax.text(cx + card_w / 2.0, 0.790, m_title, fontsize=7.5, color=C_TEXT_MUTED, ha="center", zorder=3)

    # Tabela Consolidada de Processos
    table_y = 0.120
    table_h = 0.620
    _draw_card_box(ax, 0.04, table_y, 0.92, table_h, "QUADRO GERAL DOS PROCESSOS GERADOS")

    headers = ["#", "Processo (Label)", "Tipo", "Fase", "m", "Centro (LC)", "σ̂ / p̄", "Capacidade", "Diagnóstico"]
    rows = []
    
    for i, res in enumerate(entries, 1):
        meta = res.get("metadata", {})
        label = meta.get("Label", f"Processo {i}")
        t = res.get("type", "-")
        goal = res.get("goal", "-")
        m = str(res.get("m_total", "-"))
        fl = res.get("final_limits", {})
        
        if t in ["X", "IMR"]:
            lc_val = f"{fl.get('lc_x', 0):.3f}"
            sig_val = f"{fl.get('sigma_hat', 0):.4f}"
        elif t == "P":
            lc_val = f"{fl.get('pbar', 0):.4f}"
            sig_val = f"{fl.get('pbar', 0)*100:.2f}%"
        else:
            lc_val = f"{fl.get('lc', 0):.2f}"
            sig_val = "-"
            
        cap = res.get("capability")
        if cap:
            rcpk = cap.get("RCPk", 0)
            cap_str = f"RCPk={rcpk:.2f}"
        else:
            cap_str = "Atributos"
            
        st_title, _, _ = _get_process_status(res)
        rows.append([str(i), label[:22], t, goal, m, lc_val, sig_val, cap_str, st_title])

    tab_h = min(table_h - 0.08, max(0.12, (len(rows) + 1) * 0.038))
    tab_top = table_y + table_h - 0.045
    tab_main = ax.table(
        cellText=rows,
        colLabels=headers,
        colWidths=[0.04, 0.22, 0.07, 0.12, 0.05, 0.12, 0.10, 0.12, 0.16],
        loc="center",
        bbox=[0.055, tab_top - tab_h, 0.89, tab_h]
    )
    tab_main.auto_set_font_size(False)
    tab_main.set_fontsize(8.0)
    tab_main.set_zorder(10)

    for (r, c), cell in tab_main.get_celld().items():
        cell.set_zorder(10)
        cell.set_edgecolor(C_BORDER)
        if r == 0:
            cell.set_facecolor(C_NAVY_DARK)
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("#FFFFFF" if r % 2 == 1 else "#F8FAFC")
            cell.set_text_props(color=C_TEXT_DARK)

    # Notas Técnicas e Normativas
    ax.text(0.05, 0.075, "Normas e Métodos: Regras do Western Electric Handbook (WECO), NBR ISO 7870-2 (Cartas de Controle de Shewhart),",
            fontsize=7.0, color=C_TEXT_MUTED, zorder=3)
    ax.text(0.05, 0.060, "Filtro de Kalman para rastreamento de desvio e Análise de Deslocamento segundo Montgomery (SPC).",
            fontsize=7.0, color=C_TEXT_MUTED, zorder=3)

    _add_page_footer(ax, 1, total_pages)

    pdf.savefig(fig, dpi=150)
    plt.close(fig)


def generate_process_pdf(res: Dict[str, Any], out_pdf_path: Path,
                         chart_img_path: Optional[Path] = None,
                         cap_img_path: Optional[Path] = None) -> Path:
    """
    Gera um relatório individual em PDF para um único processo.
    Produz 2 páginas com ficha técnica, carta de controle, capacidade e deslocamento.
    """
    out_pdf_path = Path(out_pdf_path)
    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    with PdfPages(str(out_pdf_path)) as pdf:
        _build_page1_process(pdf, res, chart_img_path, page_num=1, total_pages=2)
        _build_page2_process(pdf, res, cap_img_path, page_num=2, total_pages=2)
        
    return out_pdf_path


def generate_consolidated_pdf(entries: List[Tuple[Dict[str, Any], Optional[Path], Optional[Path]]],
                              out_pdf_path: Path) -> Path:
    """
    Gera um relatório consolidado em PDF contendo múltiplos processos.
    Inclui capa / sumário executivo inicial, seguido de 2 páginas para cada processo.
    
    entries: Lista de tuplas (res, chart_img_path, cap_img_path)
    """
    out_pdf_path = Path(out_pdf_path)
    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    total_processes = len(entries)
    # Se múltiplos processos, adiciona 1 página de capa executiva
    total_pages = 1 + (total_processes * 2) if total_processes > 1 else (total_processes * 2)

    with PdfPages(str(out_pdf_path)) as pdf:
        cur_page = 1
        
        # Capa executiva para 2 ou mais processos
        if total_processes > 1:
            _build_executive_cover_page(pdf, [e[0] for e in entries], total_pages)
            cur_page += 1
            
        # Páginas detalhadas de cada processo
        for res, chart_p, cap_p in entries:
            _build_page1_process(pdf, res, chart_p, page_num=cur_page, total_pages=total_pages)
            cur_page += 1
            _build_page2_process(pdf, res, cap_p, page_num=cur_page, total_pages=total_pages)
            cur_page += 1

    return out_pdf_path


def consolidate_output_directory(saida_dir: Path, out_pdf_path: Optional[Path] = None) -> Optional[Path]:
    """
    Varre a pasta de saída procurando todos os processos já gerados (subpastas com resultados.json)
    e compila um único relatório consolidado em PDF com todos eles.
    """
    saida_dir = Path(saida_dir)
    if not saida_dir.exists():
        return None

    entries: List[Tuple[Dict[str, Any], Optional[Path], Optional[Path]]] = []

    for sub in sorted(saida_dir.iterdir()):
        if sub.is_dir():
            res_file = sub / "resultados.json"
            if res_file.exists():
                try:
                    with open(res_file, "r", encoding="utf-8") as f:
                        res = json.load(f)
                    
                    # Localiza imagens dos gráficos disponíveis
                    chart_p = None
                    for name in ["carta_xbar_r.png", "carta_imr.png", "carta_p.png", "carta_c.png"]:
                        p = sub / name
                        if p.exists():
                            chart_p = p
                            break

                    cap_p = sub / "capacidade.png"
                    cap_p = cap_p if cap_p.exists() else None

                    entries.append((res, chart_p, cap_p))
                except Exception as e:
                    print(f"Aviso ao carregar {res_file}: {e}")

    if not entries:
        return None

    target_pdf = out_pdf_path if out_pdf_path else saida_dir / "relatorio_consolidado.pdf"
    return generate_consolidated_pdf(entries, target_pdf)
