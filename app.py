# Calculadora de DIFAL — versão leve para Streamlit Community Cloud
# Arquivo principal OBRIGATÓRIO: app.py (não use "app (7).py")

from pathlib import Path

import pandas as pd
import streamlit as st

from icms_data import (
    UFS_BRASIL,
    NOMES_UF,
    ICMS_INTERNA,
    UF_ORIGEM_PADRAO,
    normalizar_uf,
    calcular_difal,
    calcular_difal_nf,
)

st.set_page_config(
    page_title="Calculadora de DIFAL | ICMS",
    page_icon="📐",
    layout="wide",
)

# ---------- helpers ----------
def _fmt_brl(v: float) -> str:
    return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _aplicar_uf_clique(sigla: str) -> str:
    """1º clique = origem, 2º = destino, 3º = nova origem."""
    sigla = normalizar_uf(sigla)
    if sigla not in ICMS_INTERNA:
        return ""
    if st.session_state.selecao_passo == "origem":
        st.session_state.uf_origem = sigla
        st.session_state.sel_origem = sigla
        st.session_state.selecao_passo = "destino"
        return f"Origem: **{sigla}**. Agora escolha o **destino**."
    st.session_state.uf_destino = sigla
    st.session_state.sel_destino = sigla
    st.session_state.selecao_passo = "origem"
    return (
        f"Destino: **{sigla}**. Par: **{st.session_state.uf_origem} → {sigla}**. "
        f"Próximo clique redefine a **origem**."
    )


# ---------- session ----------
if "uf_origem" not in st.session_state:
    st.session_state.uf_origem = UF_ORIGEM_PADRAO
if "uf_destino" not in st.session_state:
    st.session_state.uf_destino = "SP"
if "selecao_passo" not in st.session_state:
    st.session_state.selecao_passo = "destino"
if "mapa_feedback" not in st.session_state:
    st.session_state.mapa_feedback = ""
if "sel_origem" not in st.session_state:
    st.session_state.sel_origem = st.session_state.uf_origem
if "sel_destino" not in st.session_state:
    st.session_state.sel_destino = st.session_state.uf_destino

# ---------- CSS leve ----------
st.markdown(
    """
<style>
.resultado-box {
    background: linear-gradient(135deg, #0f2744 0%, #1a365d 100%);
    color: #f7fafc !important;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin: 0.5rem 0 1rem 0;
}
.resultado-box h2 { color: #f7fafc !important; margin: 0 0 0.3rem 0; font-size: 1.05rem; }
.resultado-valor { font-size: 2rem; font-weight: 700; color: #68d391 !important; }
.passo-dark {
    background: #2d3748 !important;
    border-left: 4px solid #63b3ed !important;
    color: #edf2f7 !important;
    padding: 0.6rem 0.9rem;
    margin: 0.35rem 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.95rem;
    line-height: 1.45;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==================== HEADER ====================
st.title("Calculadora de DIFAL")
st.caption(
    "Estimativa comercial do Diferencial de Alíquota de ICMS. "
    "Matriz ICMS 2025 · orientativo — valide com o fiscal na NF."
)

# ==================== ENTRADAS ====================
col_esq, col_dir = st.columns([1.2, 1])

with col_esq:
    st.subheader("1. Dados da operação")

    modo_calc = st.radio(
        "Modo de cálculo",
        options=["Simples (1 base)", "NF com vários produtos"],
        horizontal=True,
    )

    itens_nf = []
    frete_nf = 0.0
    origem_produto = "Nacional"
    valor_base = 0.0

    if modo_calc.startswith("Simples"):
        origem_produto = st.radio(
            "Origem do produto",
            options=["Nacional", "Importado"],
            horizontal=True,
            help="Nacional: matriz ICMS 2025. Importado: interestadual 4%.",
        )
        valor_base = st.number_input(
            "Base de cálculo / valor da NF (R$)",
            min_value=0.0,
            value=100000.0,
            step=1000.0,
            format="%.2f",
        )
    else:
        st.caption(
            "Cada produto tem tipo próprio. O frete é rateado por valor "
            "(média ponderada) e entra na base do DIFAL de cada item."
        )
        n_itens = st.number_input(
            "Quantidade de produtos na NF",
            min_value=1,
            max_value=30,
            value=2,
            step=1,
        )
        for i in range(int(n_itens)):
            st.markdown(f"**Produto {i + 1}**")
            pc1, pc2, pc3 = st.columns([2.2, 1.2, 1.2])
            with pc1:
                desc = st.text_input("Descrição", value=f"Produto {i + 1}", key=f"desc_{i}")
            with pc2:
                val = st.number_input(
                    "Valor (R$)",
                    min_value=0.0,
                    value=10000.0 if i == 0 else 5000.0,
                    step=100.0,
                    key=f"val_{i}",
                )
            with pc3:
                tipo_i = st.selectbox("Tipo", options=["Nacional", "Importado"], key=f"tipo_{i}")
            itens_nf.append(
                {
                    "descricao": desc,
                    "valor": float(val),
                    "tipo": "importado" if tipo_i == "Importado" else "nacional",
                }
            )
        frete_nf = st.number_input(
            "Frete total da NF (R$)",
            min_value=0.0,
            value=0.0,
            step=50.0,
            format="%.2f",
        )

    st.markdown("**UF de origem e destino**")

    def _sync_origem():
        st.session_state.uf_origem = st.session_state.sel_origem

    def _sync_destino():
        st.session_state.uf_destino = st.session_state.sel_destino

    if st.session_state.sel_origem not in UFS_BRASIL:
        st.session_state.sel_origem = st.session_state.uf_origem
    if st.session_state.sel_destino not in UFS_BRASIL:
        st.session_state.sel_destino = st.session_state.uf_destino

    c1, c2, c3 = st.columns(3)
    with c1:
        st.selectbox(
            "Origem (remetente)",
            options=UFS_BRASIL,
            format_func=lambda u: f"{u} — {NOMES_UF[u]} ({ICMS_INTERNA[u]:.1f}%)",
            key="sel_origem",
            on_change=_sync_origem,
        )
        st.session_state.uf_origem = st.session_state.sel_origem
    with c2:
        st.selectbox(
            "Destino (destinatário)",
            options=UFS_BRASIL,
            format_func=lambda u: f"{u} — {NOMES_UF[u]} ({ICMS_INTERNA[u]:.1f}%)",
            key="sel_destino",
            on_change=_sync_destino,
        )
        st.session_state.uf_destino = st.session_state.sel_destino
    with c3:
        dig_o = st.text_input("Origem (sigla)", value=st.session_state.uf_origem, max_chars=2)
        dig_d = st.text_input("Destino (sigla)", value=st.session_state.uf_destino, max_chars=2)
        if dig_o and normalizar_uf(dig_o) in ICMS_INTERNA:
            u = normalizar_uf(dig_o)
            st.session_state.uf_origem = u
            st.session_state.sel_origem = u
        if dig_d and normalizar_uf(dig_d) in ICMS_INTERNA:
            u = normalizar_uf(dig_d)
            st.session_state.uf_destino = u
            st.session_state.sel_destino = u

    prox = st.session_state.selecao_passo
    if prox == "origem":
        st.info(
            f"Próximo clique na grade = **ORIGEM**. "
            f"Atual: {st.session_state.uf_origem} → {st.session_state.uf_destino}"
        )
    else:
        st.info(
            f"Próximo clique na grade = **DESTINO** "
            f"(origem: **{st.session_state.uf_origem}**)."
        )
    if st.button("Reiniciar seleção (começar pela origem)"):
        st.session_state.selecao_passo = "origem"
        st.session_state.mapa_feedback = ""
        st.rerun()

with col_dir:
    st.subheader("2. Seleção rápida de UF")
    st.caption(
        f"🟠 Origem **{st.session_state.uf_origem}** · "
        f"🟢 Destino **{st.session_state.uf_destino}** · "
        f"1º clique = origem · 2º = destino"
    )
    if st.session_state.mapa_feedback:
        st.success(st.session_state.mapa_feedback)

    # Grade de botões (leve, sem Plotly — estável no Cloud)
    cols = st.columns(9)
    for i, uf in enumerate(UFS_BRASIL):
        with cols[i % 9]:
            marcado = uf in (st.session_state.uf_origem, st.session_state.uf_destino)
            if st.button(
                f"{uf}\n{ICMS_INTERNA[uf]:.0f}%",
                key=f"btn_{uf}",
                type="primary" if marcado else "secondary",
            ):
                st.session_state.mapa_feedback = _aplicar_uf_clique(uf)
                st.rerun()

    # Mapa opcional (pesado) — só se o usuário pedir e plotly estiver instalado
    with st.expander("Mapa do Brasil (opcional, mais lento)"):
        st.caption("Carrega GeoJSON + Plotly. Pode demorar no plano free.")
        if st.button("Carregar mapa agora"):
            st.session_state["load_map"] = True
        if st.session_state.get("load_map"):
            try:
                import plotly.express as px
                import plotly.graph_objects as go
                import json

                geo_path = Path(__file__).resolve().parent / "brazil-states.geojson"
                if not geo_path.exists():
                    st.warning("Arquivo brazil-states.geojson não encontrado no repositório.")
                else:
                    with open(geo_path, encoding="utf-8") as f:
                        geo = json.load(f)
                    o = st.session_state.uf_origem
                    d = st.session_state.uf_destino
                    df = pd.DataFrame(
                        {
                            "sigla": UFS_BRASIL,
                            "nome": [NOMES_UF[u] for u in UFS_BRASIL],
                            "aliquota": [ICMS_INTERNA[u] for u in UFS_BRASIL],
                            "cor": [
                                30 if u == o else (28 if u == d else ICMS_INTERNA[u])
                                for u in UFS_BRASIL
                            ],
                        }
                    )
                    fig = px.choropleth(
                        df,
                        geojson=geo,
                        locations="sigla",
                        featureidkey="properties.sigla",
                        color="cor",
                        hover_name="nome",
                        hover_data={"sigla": True, "aliquota": True, "cor": False},
                        color_continuous_scale="Blues",
                        range_color=(16, 30),
                    )
                    fig.update_geos(fitbounds="locations", visible=False)
                    fig.update_layout(
                        margin=dict(l=0, r=0, t=20, b=0),
                        height=420,
                        coloraxis_showscale=False,
                        title=f"Origem {o} · Destino {d}",
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Não foi possível montar o mapa: {e}")

# ==================== CÁLCULO ====================
st.divider()
uf_origem = st.session_state.uf_origem
uf_destino = st.session_state.uf_destino

if modo_calc.startswith("Simples"):
    tipo = "importado" if origem_produto == "Importado" else "nacional"
    resultado = calcular_difal(valor_base, uf_destino, uf_origem, tipo)
else:
    resultado = calcular_difal_nf(itens_nf, frete_nf, uf_destino, uf_origem)

st.subheader("3. Resultado do DIFAL")

r1, r2, r3, r4 = st.columns(4)
r1.metric("Origem → Destino", f"{resultado['uf_origem']} → {resultado['uf_destino']}")
r2.metric("Composição", resultado.get("origem_produto_label") or "—")
r3.metric(
    "Base total",
    _fmt_brl(resultado.get("valor_base") or resultado.get("valor_base_total") or 0),
)
_delta = f"{resultado['diferenca_pp']:.2f} p.p." if resultado.get("diferenca_pp") else None
r4.metric("DIFAL estimado", _fmt_brl(resultado["valor_difal"]), delta=_delta)

_valor_html = _fmt_brl(resultado["valor_difal"])
_inter_txt = (
    f"Interestadual <b>{resultado.get('aliquota_interestadual', 0):.2f}%</b> · "
    f"Δ <b>{resultado.get('diferenca_pp', 0):.2f} p.p.</b>"
    if resultado.get("aliquota_interestadual")
    else "Vários itens — veja rateio abaixo"
)
st.markdown(
    f"""
<div class="resultado-box">
  <h2>DIFAL estimado para apresentação</h2>
  <div class="resultado-valor">{_valor_html}</div>
  <div style="opacity:0.95;margin-top:0.4rem;color:#edf2f7;">
    {resultado.get("nome_origem", "")} ({resultado["uf_origem"]}) →
    {resultado.get("nome_destino", "")} ({resultado["uf_destino"]}) ·
    {resultado.get("origem_produto_label", "")}<br/>
    Interna destino <b>{resultado.get("aliquota_interna_destino", 0):.2f}%</b>
    · {_inter_txt}
  </div>
</div>
""",
    unsafe_allow_html=True,
)

c_a, c_b, c_c = st.columns(3)
c_a.info(
    f"**ICMS interestadual** (na NF)\n\n{_fmt_brl(resultado.get('valor_icms_interestadual') or 0)}"
)
c_b.info(
    f"**ICMS interno teórico** (destino)\n\n{_fmt_brl(resultado.get('valor_icms_interno_teorico') or 0)}"
)
c_c.info(f"**DIFAL** (diferença)\n\n{_fmt_brl(resultado['valor_difal'])}")

if resultado.get("itens"):
    st.markdown("#### Rateio do frete e DIFAL por produto")
    rows = []
    for it in resultado["itens"]:
        rows.append(
            {
                "Produto": it.get("descricao", ""),
                "Tipo": "Importado" if it.get("tipo") == "importado" else "Nacional",
                "Valor (R$)": _fmt_brl(it.get("valor", 0)),
                "Frete rateado (R$)": _fmt_brl(it.get("frete_rateado", 0)),
                "Base (R$)": _fmt_brl(it.get("base", 0)),
                "Inter. %": f"{it.get('aliquota_interestadual', 0):.2f}",
                "Δ p.p.": f"{it.get('diferenca_pp', 0):.2f}",
                "DIFAL (R$)": _fmt_brl(it.get("valor_difal", 0)),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("#### Conta completa (passo a passo)")
for passo in resultado.get("passos") or []:
    st.markdown(f'<div class="passo-dark">{passo}</div>', unsafe_allow_html=True)

if resultado.get("observacao"):
    st.caption(resultado["observacao"])

st.markdown("#### Fórmula")
st.latex(
    r"\mathrm{DIFAL}_{item} = (\mathrm{valor}_{item} + \mathrm{frete}_{rateado}) "
    r"\times \frac{(\mathrm{Alíq.\ interna\ destino} - \mathrm{Alíq.\ interestadual})}{100}"
)
st.latex(r"\mathrm{DIFAL}_{NF} = \sum \mathrm{DIFAL}_{item}")

if (
    modo_calc.startswith("Simples")
    and resultado.get("aplica")
    and (resultado.get("diferenca_pp") or 0) > 0
):
    st.latex(
        rf"\mathrm{{DIFAL}} = {_fmt_brl(resultado['valor_base']).replace('R$ ', '')} \times "
        rf"\frac{{({resultado['aliquota_interna_destino']:.2f} - {resultado['aliquota_interestadual']:.2f})}}{{100}} = "
        rf"{_fmt_brl(resultado['valor_difal']).replace('R$ ', '')}"
    )

with st.expander("Tabela de alíquotas internas (todos os estados)"):
    st.dataframe(
        pd.DataFrame(
            {
                "UF": UFS_BRASIL,
                "Estado": [NOMES_UF[u] for u in UFS_BRASIL],
                "Alíquota interna (%)": [ICMS_INTERNA[u] for u in UFS_BRASIL],
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.caption(
    "Ferramenta orientativa. O DIFAL na NF depende do enquadramento fiscal. "
    "Consulte o departamento fiscal. · Matriz ICMS 2025."
)
