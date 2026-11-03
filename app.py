# Calculadora de DIFAL — app standalone (Streamlit)
# Isolado do sistema de propostas Casa do Frentista / GP Company

import json
import os
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
)

st.set_page_config(
    page_title="Calculadora de DIFAL | ICMS",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).resolve().parent
GEOJSON_PATH = BASE / "brazil-states.geojson"

# ---------- CSS leve ----------
st.markdown(
    """
<style>
    .block-container { padding-top: 1.2rem; }
    .resultado-box {
        background: linear-gradient(135deg, #0f2744 0%, #1a365d 100%);
        color: #fff;
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        margin: 0.5rem 0 1rem 0;
    }
    .resultado-box h2 { color: #fff; margin: 0 0 0.4rem 0; font-size: 1.1rem; }
    .resultado-valor { font-size: 2.2rem; font-weight: 700; color: #68d391; }
    .passo {
        background: #f7fafc;
        border-left: 4px solid #2b6cb0;
        padding: 0.55rem 0.9rem;
        margin: 0.35rem 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
    }
    .uf-chip {
        display: inline-block;
        background: #ebf8ff;
        border: 1px solid #90cdf4;
        border-radius: 8px;
        padding: 0.25rem 0.6rem;
        margin: 0.15rem;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Session state ----------
if "uf_origem" not in st.session_state:
    st.session_state.uf_origem = UF_ORIGEM_PADRAO
if "uf_destino" not in st.session_state:
    st.session_state.uf_destino = "SP"
if "mapa_modo" not in st.session_state:
    st.session_state.mapa_modo = "origem"  # origem | destino


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _carregar_geojson():
    if GEOJSON_PATH.exists():
        with open(GEOJSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    return None


def _mapa_aliquotas(destaque_origem: str, destaque_destino: str):
    """Choropleth das alíquotas internas + destaque origem/destino."""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
    except ImportError:
        return None

    geo = _carregar_geojson()
    if not geo:
        return None

    df = pd.DataFrame(
        {
            "sigla": UFS_BRASIL,
            "nome": [NOMES_UF[u] for u in UFS_BRASIL],
            "aliquota": [ICMS_INTERNA[u] for u in UFS_BRASIL],
            "rotulo": [f"{u} · {ICMS_INTERNA[u]:.1f}%" for u in UFS_BRASIL],
        }
    )

    fig = px.choropleth(
        df,
        geojson=geo,
        locations="sigla",
        featureidkey="properties.sigla",
        color="aliquota",
        hover_name="nome",
        hover_data={"sigla": True, "aliquota": True, "rotulo": False},
        color_continuous_scale="Blues",
        range_color=(16, 23),
        labels={"aliquota": "Alíq. interna %", "sigla": "UF"},
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=480,
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        coloraxis_colorbar=dict(title="ICMS %"),
        title=dict(
            text="Alíquota interna de ICMS por UF · clique no mapa ou use os seletor es abaixo",
            font=dict(size=14),
        ),
    )

    # Marcadores de texto (UF + alíquota) — centroids aproximados via geojson
    try:
        import numpy as np

        lons, lats, texts, colors = [], [], [], []
        for feat in geo["features"]:
            sigla = feat["properties"]["sigla"]
            aliq = ICMS_INTERNA.get(sigla, 0)
            # centroid simples do primeiro polígono
            coords = feat["geometry"]["coordinates"]
            geom = feat["geometry"]["type"]
            if geom == "Polygon":
                ring = coords[0]
            else:  # MultiPolygon
                ring = coords[0][0]
            arr = np.array(ring)
            lon, lat = float(arr[:, 0].mean()), float(arr[:, 1].mean())
            lons.append(lon)
            lats.append(lat)
            texts.append(f"{sigla}<br>{aliq:.0f}%")
            if sigla == destaque_origem:
                colors.append("#dd6b20")
            elif sigla == destaque_destino:
                colors.append("#38a169")
            else:
                colors.append("#2b6cb0")

        fig.add_trace(
            go.Scattergeo(
                lon=lons,
                lat=lats,
                text=texts,
                mode="text",
                textfont=dict(size=10, color="#1a202c", family="Arial Black"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    except Exception:
        pass

    return fig


# ==================== HEADER ====================
st.title("Calculadora de DIFAL")
st.caption(
    "Estimativa comercial do Diferencial de Alíquota de ICMS (operações interestaduais). "
    "Matriz ICMS 2025 · orientativo — valide com o fiscal na NF."
)

# ==================== ENTRADAS ====================
col_esq, col_dir = st.columns([1.15, 1])

with col_esq:
    st.subheader("1. Dados da operação")

    origem_produto = st.radio(
        "Origem do produto",
        options=["Nacional", "Importado"],
        horizontal=True,
        help=(
            "Nacional: alíquota interestadual pela matriz ICMS 2025. "
            "Importado: interestadual fixa de 4% (Res. Senado 13/2012)."
        ),
    )

    valor_base = st.number_input(
        "Base de cálculo / valor da NF (R$)",
        min_value=0.0,
        value=100000.0,
        step=1000.0,
        format="%.2f",
        help="Em geral: (produtos − descontos) + frete, conforme a regra fiscal da operação.",
    )

    st.markdown("**UF de origem e destino**")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        opts = UFS_BRASIL
        i_o = opts.index(st.session_state.uf_origem) if st.session_state.uf_origem in opts else opts.index("SC")
        uf_origem = st.selectbox(
            "Origem (remetente)",
            options=opts,
            index=i_o,
            format_func=lambda u: f"{u} — {NOMES_UF[u]} ({ICMS_INTERNA[u]:.1f}%)",
            key="sel_origem",
        )
        st.session_state.uf_origem = uf_origem
    with c2:
        i_d = opts.index(st.session_state.uf_destino) if st.session_state.uf_destino in opts else opts.index("SP")
        uf_destino = st.selectbox(
            "Destino (destinatário)",
            options=opts,
            index=i_d,
            format_func=lambda u: f"{u} — {NOMES_UF[u]} ({ICMS_INTERNA[u]:.1f}%)",
            key="sel_destino",
        )
        st.session_state.uf_destino = uf_destino
    with c3:
        st.markdown("Digitar UF")
        dig_o = st.text_input("Origem (sigla)", value=st.session_state.uf_origem, max_chars=2, key="txt_o")
        dig_d = st.text_input("Destino (sigla)", value=st.session_state.uf_destino, max_chars=2, key="txt_d")
        if dig_o and normalizar_uf(dig_o) in ICMS_INTERNA:
            st.session_state.uf_origem = normalizar_uf(dig_o)
            uf_origem = st.session_state.uf_origem
        if dig_d and normalizar_uf(dig_d) in ICMS_INTERNA:
            st.session_state.uf_destino = normalizar_uf(dig_d)
            uf_destino = st.session_state.uf_destino

    st.markdown("**Atalho: clicar no mapa**")
    modo = st.radio(
        "Próximo clique no mapa define:",
        options=["origem", "destino"],
        format_func=lambda x: "UF de **origem**" if x == "origem" else "UF de **destino**",
        horizontal=True,
        key="mapa_modo",
    )

with col_dir:
    st.subheader("2. Mapa do Brasil — alíquota interna")
    st.caption("Laranja = origem · Verde = destino · número = ICMS interno da UF")

    fig = _mapa_aliquotas(st.session_state.uf_origem, st.session_state.uf_destino)
    if fig is not None:
        event = st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key="mapa_brasil",
        )
        # Captura clique
        try:
            points = (event or {}).get("selection", {}).get("points", []) if event else []
            if points:
                pt = points[0]
                sigla = None
                if "location" in pt:
                    sigla = pt["location"]
                elif "properties" in pt and isinstance(pt["properties"], dict):
                    sigla = pt["properties"].get("sigla")
                elif "hovertext" in pt:
                    # fallback
                    pass
                if sigla and sigla in ICMS_INTERNA:
                    if st.session_state.mapa_modo == "origem":
                        st.session_state.uf_origem = sigla
                        st.success(f"Origem definida: **{sigla}**")
                    else:
                        st.session_state.uf_destino = sigla
                        st.success(f"Destino definido: **{sigla}**")
        except Exception:
            pass
    else:
        st.warning(
            "Mapa indisponível (plotly ou geojson). Use os seletores de UF. "
            "Instale: `pip install plotly pandas`"
        )

# Grade clicável de UFs (sempre disponível)
st.markdown("##### Grade rápida de estados (UF + alíquota interna)")
st.caption("Clique em um botão e o estado será aplicado conforme o modo escolhido acima (origem ou destino).")
cols = st.columns(9)
for i, uf in enumerate(UFS_BRASIL):
    with cols[i % 9]:
        label = f"{uf}\n{ICMS_INTERNA[uf]:.0f}%"
        tipo_btn = "primary" if uf in (st.session_state.uf_origem, st.session_state.uf_destino) else "secondary"
        if st.button(label, key=f"btn_{uf}", use_container_width=True, type=tipo_btn):
            if st.session_state.mapa_modo == "origem":
                st.session_state.uf_origem = uf
            else:
                st.session_state.uf_destino = uf
            st.rerun()

# ==================== CÁLCULO ====================
st.divider()
uf_origem = st.session_state.uf_origem
uf_destino = st.session_state.uf_destino
tipo = "importado" if origem_produto == "Importado" else "nacional"

resultado = calcular_difal(valor_base, uf_destino, uf_origem, tipo)

st.subheader("3. Resultado do DIFAL")

r1, r2, r3, r4 = st.columns(4)
r1.metric("Origem → Destino", f"{resultado['uf_origem']} → {resultado['uf_destino']}")
r2.metric("Produto", resultado["origem_produto_label"])
r3.metric("Base de cálculo", _fmt_brl(resultado["valor_base"]))
r4.metric(
    "DIFAL estimado",
    _fmt_brl(resultado["valor_difal"]),
    delta=f"{resultado['diferenca_pp']:.2f} p.p." if resultado["diferenca_pp"] else None,
)

_valor_html = _fmt_brl(resultado["valor_difal"])
st.markdown(
    f"""
<div class="resultado-box">
  <h2>DIFAL estimado para apresentação</h2>
  <div class="resultado-valor">{_valor_html}</div>
  <div style="opacity:0.9;margin-top:0.4rem;">
    {resultado["nome_origem"]} ({resultado["uf_origem"]}) →
    {resultado["nome_destino"]} ({resultado["uf_destino"]}) ·
    produto {resultado["origem_produto_label"]}<br/>
    Interna destino <b>{resultado["aliquota_interna_destino"]:.2f}%</b>
    − Interestadual <b>{resultado["aliquota_interestadual"]:.2f}%</b>
    = <b>{resultado["diferenca_pp"]:.2f} p.p.</b>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

c_a, c_b, c_c = st.columns(3)
c_a.info(f"**ICMS interestadual** (na NF)\n\n{_fmt_brl(resultado['valor_icms_interestadual'])}")
c_b.info(f"**ICMS interno teórico** (destino)\n\n{_fmt_brl(resultado['valor_icms_interno_teorico'])}")
c_c.info(f"**DIFAL** (diferença)\n\n{_fmt_brl(resultado['valor_difal'])}")

st.markdown("#### Conta completa (passo a passo)")
for passo in resultado.get("passos") or []:
    st.markdown(f'<div class="passo">{passo}</div>', unsafe_allow_html=True)

if resultado.get("observacao"):
    st.caption(resultado["observacao"])

st.markdown("#### Fórmula")
st.latex(r"\mathrm{DIFAL} = \mathrm{Base} \times \frac{(\mathrm{Alíq.\ interna\ destino} - \mathrm{Alíq.\ interestadual})}{100}")

if resultado["aplica"] and resultado["diferenca_pp"] > 0:
    st.latex(
        rf"\mathrm{{DIFAL}} = {_fmt_brl(resultado['valor_base']).replace('R$ ', '')} \times "
        rf"\frac{{({resultado['aliquota_interna_destino']:.2f} - {resultado['aliquota_interestadual']:.2f})}}{{100}} = "
        rf"{_fmt_brl(resultado['valor_difal']).replace('R$ ', '')}"
    )

with st.expander("Tabela de alíquotas internas (todos os estados)"):
    df_tab = pd.DataFrame(
        {
            "UF": UFS_BRASIL,
            "Estado": [NOMES_UF[u] for u in UFS_BRASIL],
            "Alíquota interna (%)": [ICMS_INTERNA[u] for u in UFS_BRASIL],
        }
    )
    st.dataframe(df_tab, use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "Ferramenta orientativa para apoio comercial. "
    "O DIFAL efetivo na NF depende do enquadramento (contribuinte, não contribuinte, benefícios, ST, etc.). "
    "Consulte o departamento fiscal. · Matriz ICMS 2025."
)
