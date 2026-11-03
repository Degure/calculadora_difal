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
    calcular_difal_nf,
)

st.set_page_config(
    page_title="Calculadora de DIFAL | ICMS",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).resolve().parent
GEOJSON_PATH = BASE / "brazil-states.geojson"

# ---------- CSS (compatível com tema claro e escuro) ----------
st.markdown(
    """
<style>
    .block-container { padding-top: 1.2rem; }
    .resultado-box {
        background: linear-gradient(135deg, #0f2744 0%, #1a365d 100%);
        color: #f7fafc !important;
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        margin: 0.5rem 0 1rem 0;
    }
    .resultado-box h2 { color: #f7fafc !important; margin: 0 0 0.4rem 0; font-size: 1.1rem; }
    .resultado-valor { font-size: 2.2rem; font-weight: 700; color: #68d391 !important; }
    .passo {
        background: rgba(49, 130, 206, 0.12);
        border-left: 4px solid #63b3ed;
        color: inherit;
        padding: 0.65rem 0.95rem;
        margin: 0.4rem 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
        line-height: 1.45;
    }
    /* Fallback texto legível em qualquer tema */
    .passo, .passo * {
        color: var(--text-color, inherit) !important;
    }
    [data-theme="dark"] .passo, .stApp[data-theme="dark"] .passo {
        background: rgba(99, 179, 237, 0.15);
        border-left-color: #63b3ed;
        color: #e2e8f0 !important;
    }
    /* Força contraste se o tema escuro não propagar variáveis */
    .passo-dark {
        background: #2d3748 !important;
        border-left: 4px solid #63b3ed !important;
        color: #edf2f7 !important;
        padding: 0.65rem 0.95rem;
        margin: 0.4rem 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
        line-height: 1.45;
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
# Próximo clique no mapa/grade: "origem" → depois "destino" → volta para "origem"
if "selecao_passo" not in st.session_state:
    st.session_state.selecao_passo = "destino"  # já há origem padrão; próximo clique = destino
# Evita loop: não reprocessa a mesma seleção do Plotly em reruns consecutivos
if "mapa_last_token" not in st.session_state:
    st.session_state.mapa_last_token = None
if "mapa_feedback" not in st.session_state:
    st.session_state.mapa_feedback = ""


def _aplicar_uf_clique(sigla: str) -> str:
    """
    Fluxo automático sem switch:
      1º clique → origem, próximo vira destino
      2º clique → destino, próximo vira origem
      3º clique → nova origem (reinicia o ciclo)
    Retorna mensagem de feedback.
    """
    sigla = normalizar_uf(sigla)
    if sigla not in ICMS_INTERNA:
        return ""
    if st.session_state.selecao_passo == "origem":
        st.session_state.uf_origem = sigla
        st.session_state.sel_origem = sigla  # sincroniza o selectbox
        st.session_state.selecao_passo = "destino"
        return f"Origem: **{sigla}**. Agora clique no **destino**."
    # passo destino
    st.session_state.uf_destino = sigla
    st.session_state.sel_destino = sigla
    st.session_state.selecao_passo = "origem"
    return (
        f"Destino: **{sigla}**. Par: **{st.session_state.uf_origem} → {sigla}**. "
        f"Próximo clique redefine a **origem**."
    )


def _token_selecao_plotly(points: list) -> str:
    """Identifica unicamente a seleção atual (não muda só porque o passo mudou)."""
    if not points:
        return ""
    pt = points[0] or {}
    sigla = pt.get("location") or ""
    if not sigla and isinstance(pt.get("properties"), dict):
        sigla = pt["properties"].get("sigla") or ""
    return "|".join(
        [
            str(sigla),
            str(pt.get("point_index", pt.get("pointNumber", ""))),
            str(pt.get("curveNumber", "")),
            str(pt.get("lon", "")),
            str(pt.get("lat", "")),
        ]
    )


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _carregar_geojson():
    if GEOJSON_PATH.exists():
        with open(GEOJSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    return None


def _mapa_aliquotas(destaque_origem: str, destaque_destino: str):
    """Choropleth com alíquotas; origem e destino destacados ao mesmo tempo."""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
    except ImportError:
        return None

    geo = _carregar_geojson()
    if not geo:
        return None

    def _papel(u: str) -> str:
        if u == destaque_origem and u == destaque_destino:
            return "Origem e destino"
        if u == destaque_origem:
            return "Origem"
        if u == destaque_destino:
            return "Destino"
        return "Demais"

    df = pd.DataFrame(
        {
            "sigla": UFS_BRASIL,
            "nome": [NOMES_UF[u] for u in UFS_BRASIL],
            "aliquota": [ICMS_INTERNA[u] for u in UFS_BRASIL],
            "papel": [_papel(u) for u in UFS_BRASIL],
            # escala contínua, mas “empurra” origem/destino para cores distintas no hover
            "cor_mapa": [
                30 if u == destaque_origem else (28 if u == destaque_destino else ICMS_INTERNA[u])
                for u in UFS_BRASIL
            ],
        }
    )

    fig = px.choropleth(
        df,
        geojson=geo,
        locations="sigla",
        featureidkey="properties.sigla",
        color="cor_mapa",
        hover_name="nome",
        hover_data={"sigla": True, "aliquota": True, "papel": True, "cor_mapa": False},
        color_continuous_scale=[
            [0.0, "#cfe2f3"],
            [0.5, "#6fa8dc"],
            [0.85, "#1a5276"],
            [0.92, "#38a169"],  # destino
            [1.0, "#dd6b20"],   # origem
        ],
        range_color=(16, 30),
        labels={"aliquota": "Alíq. interna %", "sigla": "UF", "papel": "Seleção"},
    )
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(
        margin=dict(l=0, r=0, t=36, b=0),
        height=480,
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        coloraxis_showscale=False,
        title=dict(
            text=f"🟠 Origem {destaque_origem or '—'}  ·  🟢 Destino {destaque_destino or '—'}  ·  clique no mapa",
            font=dict(size=14),
        ),
    )

    # Rótulos UF + % e marcadores nos estados selecionados
    try:
        import numpy as np

        lons, lats, texts = [], [], []
        lo_o, la_o, lo_d, la_d = None, None, None, None
        for feat in geo["features"]:
            sigla = feat["properties"]["sigla"]
            aliq = ICMS_INTERNA.get(sigla, 0)
            coords = feat["geometry"]["coordinates"]
            geom = feat["geometry"]["type"]
            ring = coords[0] if geom == "Polygon" else coords[0][0]
            arr = np.array(ring)
            lon, lat = float(arr[:, 0].mean()), float(arr[:, 1].mean())
            lons.append(lon)
            lats.append(lat)
            texts.append(f"<b>{sigla}</b><br>{aliq:.0f}%")
            if sigla == destaque_origem:
                lo_o, la_o = lon, lat
            if sigla == destaque_destino:
                lo_d, la_d = lon, lat

        fig.add_trace(
            go.Scattergeo(
                lon=lons,
                lat=lats,
                text=texts,
                mode="text",
                textfont=dict(size=10, color="#1a202c", family="Arial"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        # Círculos de destaque (origem e destino ao mesmo tempo)
        if lo_o is not None:
            fig.add_trace(
                go.Scattergeo(
                    lon=[lo_o],
                    lat=[la_o],
                    mode="markers",
                    marker=dict(size=18, color="#dd6b20", line=dict(width=2, color="#fff")),
                    name="Origem",
                    hoverinfo="skip",
                )
            )
        if lo_d is not None and destaque_destino != destaque_origem:
            fig.add_trace(
                go.Scattergeo(
                    lon=[lo_d],
                    lat=[la_d],
                    mode="markers",
                    marker=dict(size=18, color="#38a169", line=dict(width=2, color="#fff")),
                    name="Destino",
                    hoverinfo="skip",
                )
            )
        elif lo_d is not None and destaque_destino == destaque_origem:
            # mesmo estado: anel extra
            fig.add_trace(
                go.Scattergeo(
                    lon=[lo_d],
                    lat=[la_d],
                    mode="markers",
                    marker=dict(size=26, color="rgba(56,161,105,0.35)", line=dict(width=2, color="#38a169")),
                    name="Origem=Destino",
                    hoverinfo="skip",
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

    modo_calc = st.radio(
        "Modo de cálculo",
        options=["Simples (1 base)", "NF com vários produtos"],
        horizontal=True,
        help=(
            "Simples: um valor de base e um tipo (nacional/importado). "
            "Vários produtos: cada item tem tipo próprio e o frete é rateado por valor."
        ),
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
            help="Em geral: (produtos − descontos) + frete, se o frete já estiver embutido na base.",
        )
    else:
        st.caption(
            "Informe cada produto da NF. O **frete** é diluído por média ponderada "
            "(proporcional ao valor de cada item) e entra na base do DIFAL daquele item."
        )
        n_itens = st.number_input("Quantidade de produtos na NF", min_value=1, max_value=30, value=2, step=1)
        for i in range(int(n_itens)):
            st.markdown(f"**Produto {i+1}**")
            pc1, pc2, pc3 = st.columns([2.2, 1.2, 1.2])
            with pc1:
                desc = st.text_input("Descrição", value=f"Produto {i+1}", key=f"desc_{i}")
            with pc2:
                val = st.number_input("Valor (R$)", min_value=0.0, value=10000.0 if i == 0 else 5000.0, step=100.0, key=f"val_{i}")
            with pc3:
                tipo_i = st.selectbox("Tipo", options=["Nacional", "Importado"], key=f"tipo_{i}")
            itens_nf.append({
                "descricao": desc,
                "valor": float(val),
                "tipo": "importado" if tipo_i == "Importado" else "nacional",
            })
        frete_nf = st.number_input(
            "Frete total da NF (R$)",
            min_value=0.0,
            value=0.0,
            step=50.0,
            format="%.2f",
            help="Rateado entre os produtos: frete_item = frete × (valor_item / soma_produtos).",
        )

    st.markdown("**UF de origem e destino**")
    # Mantém selectbox alinhado ao estado (mapa/grade também gravam sel_origem / sel_destino)
    if "sel_origem" not in st.session_state:
        st.session_state.sel_origem = st.session_state.uf_origem
    if "sel_destino" not in st.session_state:
        st.session_state.sel_destino = st.session_state.uf_destino
    # Garante valor válido
    if st.session_state.sel_origem not in UFS_BRASIL:
        st.session_state.sel_origem = st.session_state.uf_origem
    if st.session_state.sel_destino not in UFS_BRASIL:
        st.session_state.sel_destino = st.session_state.uf_destino

    def _sync_origem():
        st.session_state.uf_origem = st.session_state.sel_origem

    def _sync_destino():
        st.session_state.uf_destino = st.session_state.sel_destino

    c1, c2, c3 = st.columns([1, 1, 1])
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
        st.markdown("Digitar UF")
        dig_o = st.text_input("Origem (sigla)", value=st.session_state.uf_origem, max_chars=2, key="txt_o")
        dig_d = st.text_input("Destino (sigla)", value=st.session_state.uf_destino, max_chars=2, key="txt_d")
        if dig_o and normalizar_uf(dig_o) in ICMS_INTERNA:
            u = normalizar_uf(dig_o)
            st.session_state.uf_origem = u
            st.session_state.sel_origem = u
        if dig_d and normalizar_uf(dig_d) in ICMS_INTERNA:
            u = normalizar_uf(dig_d)
            st.session_state.uf_destino = u
            st.session_state.sel_destino = u

    # Indicador do próximo clique (sem switch manual)
    prox = st.session_state.selecao_passo
    if prox == "origem":
        st.info(
            f"Próximo clique no mapa/grade = **ORIGEM**. "
            f"Atual: 🟠 {st.session_state.uf_origem} → 🟢 {st.session_state.uf_destino}"
        )
    else:
        st.info(
            f"Próximo clique no mapa/grade = **DESTINO** "
            f"(origem já é **{st.session_state.uf_origem}**)."
        )
    if st.button("Reiniciar seleção (começar pela origem)"):
        st.session_state.selecao_passo = "origem"
        st.rerun()

with col_dir:
    st.subheader("2. Mapa do Brasil — alíquota interna")
    st.caption(
        "🟠 Laranja = origem · 🟢 Verde = destino (os dois ficam destacados juntos). "
        "1º clique = origem · 2º = destino · 3º = nova origem."
    )

    fig = _mapa_aliquotas(st.session_state.uf_origem, st.session_state.uf_destino)
    if fig is not None:
        # on_select="rerun" já recarrega a página — NÃO chamar st.rerun() de novo
        event = st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key="mapa_brasil",
        )
        try:
            selection = {}
            if event is not None:
                # Streamlit devolve dict ou objeto com .selection
                if isinstance(event, dict):
                    selection = event.get("selection") or {}
                else:
                    selection = getattr(event, "selection", None) or {}
                    if hasattr(selection, "points"):
                        selection = {"points": selection.points}
            points = selection.get("points") or []
            if points:
                token = _token_selecao_plotly(points)
                # Só processa se for um clique NOVO (evita loop infinito)
                if token and token != st.session_state.mapa_last_token:
                    pt = points[0]
                    sigla = pt.get("location")
                    if not sigla and isinstance(pt.get("properties"), dict):
                        sigla = pt["properties"].get("sigla")
                    if sigla and sigla in ICMS_INTERNA:
                        st.session_state.mapa_last_token = token
                        msg = _aplicar_uf_clique(sigla)
                        st.session_state.mapa_feedback = msg
                        # Sem st.rerun(): o on_select já rerodou; estado vale no restante desta execução
            else:
                # Clique vazio / deseleção — libera token para poder clicar de novo no mesmo estado
                st.session_state.mapa_last_token = None
        except Exception:
            pass

        if st.session_state.mapa_feedback:
            st.success(st.session_state.mapa_feedback)
    else:
        st.warning(
            "Mapa indisponível (plotly ou geojson). Use a grade de UFs. "
            "Instale: `pip install plotly pandas`"
        )

# Grade clicável de UFs (mesmo fluxo automático origem → destino → origem)
st.markdown("##### Grade rápida de estados (UF + alíquota interna)")
st.caption(
    f"Clique em um estado: próximo passo é **{st.session_state.selecao_passo.upper()}**. "
    f"Selecionados agora: origem **{st.session_state.uf_origem}** · destino **{st.session_state.uf_destino}**."
)
cols = st.columns(9)
for i, uf in enumerate(UFS_BRASIL):
    with cols[i % 9]:
        label = f"{uf}\n{ICMS_INTERNA[uf]:.0f}%"
        if uf == st.session_state.uf_origem and uf == st.session_state.uf_destino:
            tipo_btn = "primary"
        elif uf == st.session_state.uf_origem or uf == st.session_state.uf_destino:
            tipo_btn = "primary"
        else:
            tipo_btn = "secondary"
        if st.button(label, key=f"btn_{uf}", use_container_width=True, type=tipo_btn):
            _aplicar_uf_clique(uf)
            st.rerun()

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
r3.metric("Base total", _fmt_brl(resultado.get("valor_base") or resultado.get("valor_base_total") or 0))
_delta = None
if resultado.get("diferenca_pp"):
    _delta = f"{resultado['diferenca_pp']:.2f} p.p."
r4.metric("DIFAL estimado", _fmt_brl(resultado["valor_difal"]), delta=_delta)

_valor_html = _fmt_brl(resultado["valor_difal"])
_inter_txt = (
    f"Interestadual <b>{resultado['aliquota_interestadual']:.2f}%</b> · "
    f"Δ <b>{resultado['diferenca_pp']:.2f} p.p.</b>"
    if resultado.get("aliquota_interestadual")
    else "Vários itens — veja rateio e DIFAL por produto abaixo"
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
c_a.info(f"**ICMS interestadual** (na NF)\n\n{_fmt_brl(resultado.get('valor_icms_interestadual') or 0)}")
c_b.info(f"**ICMS interno teórico** (destino)\n\n{_fmt_brl(resultado.get('valor_icms_interno_teorico') or 0)}")
c_c.info(f"**DIFAL** (diferença)\n\n{_fmt_brl(resultado['valor_difal'])}")

# Detalhe por item (modo NF)
if resultado.get("itens"):
    st.markdown("#### Rateio do frete e DIFAL por produto")
    rows = []
    for it in resultado["itens"]:
        rows.append({
            "Produto": it.get("descricao", ""),
            "Tipo": "Importado" if it.get("tipo") == "importado" else "Nacional",
            "Valor (R$)": it.get("valor", 0),
            "Frete rateado (R$)": it.get("frete_rateado", 0),
            "Base (R$)": it.get("base", 0),
            "Inter. %": it.get("aliquota_interestadual", 0),
            "Δ p.p.": it.get("diferenca_pp", 0),
            "DIFAL (R$)": it.get("valor_difal", 0),
        })
    df_itens = pd.DataFrame(rows)
# Formata colunas monetárias como texto BR para leitura fácil
for col in ["Valor (R$)", "Frete rateado (R$)", "Base (R$)", "DIFAL (R$)"]:
    if col in df_itens.columns:
        df_itens[col] = df_itens[col].map(lambda v: _fmt_brl(float(v)))
st.dataframe(df_itens, use_container_width=True, hide_index=True)

st.markdown("#### Conta completa (passo a passo)")
for passo in resultado.get("passos") or []:
    # passo-dark garante legibilidade no tema escuro do Streamlit
    st.markdown(f'<div class="passo-dark">{passo}</div>', unsafe_allow_html=True)

if resultado.get("observacao"):
    st.caption(resultado["observacao"])

st.markdown("#### Fórmula")
st.latex(
    r"\mathrm{DIFAL}_{item} = (\mathrm{valor}_{item} + \mathrm{frete}_{rateado}) "
    r"\times \frac{(\mathrm{Alíq.\ interna\ destino} - \mathrm{Alíq.\ interestadual})}{100}"
)
st.latex(r"\mathrm{DIFAL}_{NF} = \sum \mathrm{DIFAL}_{item}")
st.caption(
    "Frete rateado: "
    r"$frete_{item} = frete_{total} \times (valor_{item} / \sum valor_{produtos})$ · "
    "Nacional usa a matriz ICMS 2025; importado usa interestadual 4%."
)

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
