import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any
import math

def _get_ax_zones(ax, lic, lc, lsc):
    sig = (lsc - lc) / 3.0
    ax.axhline(lc + sig, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(lc + 2*sig, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(lc - sig, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(lc - 2*sig, color='gray', linestyle=':', alpha=0.5)

def _mark_points(ax, indices, vals, res, lic_arr, lsc_arr, we_rules=None):
    for i, v in enumerate(vals):
        if v is None: continue
        is_ex = res["goal"] == "Calibrar" and i in res.get("excluded", [])
        if is_ex:
            ax.plot(i, v, marker='x', markersize=10, color='gray')
            ax.text(i+0.1, v, "×", color="gray", fontsize=10)
            continue
            
        if we_rules:
            rules_violated = [r for r, idxs in we_rules.items() if i in idxs]
            if rules_violated:
                color = 'red' if 'R1' in rules_violated else ('orange' if 'R2' in rules_violated else 'magenta')
                ax.plot(i, v, marker='o', markersize=8, color=color)
                ax.text(i+0.2, v, ",".join(rules_violated), color=color, fontsize=9)
        else:
            lic = lic_arr[i] if isinstance(lic_arr, list) else lic_arr
            lsc = lsc_arr[i] if isinstance(lsc_arr, list) else lsc_arr
            if v > lsc or v < lic:
                ax.plot(i, v, marker='o', markersize=8, color='red')
                ax.text(i+0.2, v, "R1", color="red", fontsize=9)

def plot_xbar_r(res: Dict[str, Any], filepath: Path):
    fl, m = res["final_limits"], res["m_total"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle(f"{res['metadata']['Label']} - Carta {res['type']} ({res['goal']})", fontsize=12)
    
    ax1.plot(range(m), res["xbar_all"], marker='o', color='blue')
    ax2.plot(range(m), res["r_all"], marker='o', color='blue')
    
    if res.get("kalman"):
        ax1.plot(range(m), res["kalman"], linestyle='--', color='darkorange', linewidth=2, label='Filtro de Kalman')

    for ax, t, vals, lc, lic, lsc in [(ax1, 'X̄', res["xbar_all"], fl['lc_x'], fl['lic_x'], fl['lsc_x']), 
                                      (ax2, 'R', res["r_all"], fl['lc_r'], fl['lic_r'], fl['lsc_r'])]:
        ax.axhline(lc, color='green', label='LC')
        ax.axhline(lsc, color='red', linestyle='--', label='LSC')
        ax.axhline(lic, color='red', linestyle='--', label='LIC')
        if t == 'X̄': _get_ax_zones(ax, lic, lc, lsc)
        
        rules = res.get("we_rules_x" if t == 'X̄' else "we_rules_r")
        _mark_points(ax, range(m), vals, res, lic, lsc, we_rules=rules)
        
        ax.set_ylabel(f"Média X̄" if t == 'X̄' else f"Amplitude R")
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
    
    ax2.set_xlabel("Amostra")
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()

def plot_imr(res: Dict[str, Any], filepath: Path):
    fl, m = res["final_limits"], res["m_total"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle(f"{res['metadata']['Label']} - Carta IMR ({res['goal']})", fontsize=12)
    
    ax1.plot(range(m), res["data_raw"], marker='o', color='blue')
    ax2.plot(range(m), res["mr_raw"], marker='o', color='purple')
    
    if res.get("kalman"):
        ax1.plot(range(m), res["kalman"], linestyle='--', color='darkorange', linewidth=2, label='Filtro de Kalman')
        
    for ax, t, vals, lc, lic, lsc in [(ax1, 'I', res["data_raw"], fl['lc_x'], fl['lic_x'], fl['lsc_x']), 
                                      (ax2, 'MR', res["mr_raw"], fl['lc_mr'], fl['lic_mr'], fl['lsc_mr'])]:
        ax.axhline(lc, color='green', label='LC')
        ax.axhline(lsc, color='red', linestyle='--', label='LSC')
        ax.axhline(lic, color='red', linestyle='--', label='LIC')
        if t == 'I': _get_ax_zones(ax, lic, lc, lsc)
        
        rules = res.get("we_rules_x" if t == 'I' else "we_rules_mr")
        _mark_points(ax, range(m), vals, res, lic, lsc, we_rules=rules)
        
        ax.set_ylabel(f"Individual (I)" if t == 'I' else f"Amplitude Móvel (MR)")
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
    
    ax2.set_xlabel("Amostra")
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()

def plot_p(res: Dict[str, Any], filepath: Path):
    fl, m = res["final_limits"], res["m_total"]
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle(f"{res['metadata']['Label']} - Carta P ({res['goal']})", fontsize=12)
    
    p_vals = [d["d"]/d["n"] for d in res["data_raw"]]
    lics = [lim[0] for lim in fl["limits_per_sample"]]
    lscs = [lim[2] for lim in fl["limits_per_sample"]]
    
    ax.plot(range(m), p_vals, marker='o', color='blue', label='Fração (p)')
    ax.axhline(fl['pbar'], color='green', label='LC')
    ax.step(range(m), lics, color='red', linestyle='--', where='mid', label='LIC/LSC')
    ax.step(range(m), lscs, color='red', linestyle='--', where='mid')
    
    _mark_points(ax, range(m), p_vals, res, lics, lscs, we_rules=res.get("we_rules_p"))
    ax.set_ylabel("Fração Não Conforme")
    ax.set_xlabel("Amostra")
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()

def plot_c(res: Dict[str, Any], filepath: Path):
    fl, m = res["final_limits"], res["m_total"]
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle(f"{res['metadata']['Label']} - Carta C ({res['goal']})", fontsize=12)
    
    ax.plot(range(m), res["data_raw"], marker='o', color='blue')
    ax.axhline(fl['lc'], color='green', label='LC')
    ax.axhline(fl['lsc'], color='red', linestyle='--', label='LSC')
    ax.axhline(fl['lic'], color='red', linestyle='--', label='LIC')
    
    _mark_points(ax, range(m), res["data_raw"], res, fl['lic'], fl['lsc'], we_rules=res.get("we_rules_c"))
    ax.set_ylabel("Contagem de Defeitos (c)")
    ax.set_xlabel("Amostra")
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()

def plot_capability(res: Dict[str, Any], filepath: Path):
    fl = res["final_limits"]
    mu, sigma = fl["lc_x"], fl["sigma_hat"]
    lse, lie = res["lse"], res["lie"]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    x_min, x_max = min(lie, mu - 4*sigma), max(lse, mu + 4*sigma)
    step = (x_max - x_min) / 200
    
    xs = [x_min + i*step for i in range(201)]
    ys = [(1.0 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mu) / sigma)**2) for x in xs]
    
    ax.plot(xs, ys, color='blue', label='N(LC, σ̂)')
    ax.axvline(lse, color='red', linestyle='--', label='LSE')
    ax.axvline(lie, color='red', linestyle='--', label='LIE')
    ax.axvline(mu, color='green', linestyle='-', label='Alvo/Média')
    
    ax.set_title(f"Análise de Capacidade - {res['metadata']['Label']}")
    ax.legend()
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()