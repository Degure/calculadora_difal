# Calculadora de DIFAL (ICMS)

App Streamlit **independente** do sistema de propostas.

## O que faz

- Calcula DIFAL estimado (nacional ou importado)
- Mapa do Brasil com UF + alíquota interna de ICMS
- Seleção por mapa, grade de botões, selectbox ou digitação da UF
- Mostra a **conta completa** passo a passo para apresentação

## Como rodar

```bash
cd calculadora_difal
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Publicar (Streamlit Community Cloud)

1. Suba a pasta `calculadora_difal` (com `brazil-states.geojson`) para um repositório GitHub
2. Em [share.streamlit.io](https://share.streamlit.io) → New app
3. Main file: `app.py`

## Observação fiscal

Ferramenta **orientativa**. O DIFAL na NF depende do enquadramento da operação. Valide com o fiscal.
