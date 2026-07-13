import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import os
import base64
import re

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS DEFINITIVO (CLARO / ESCURO)
# ==========================================
st.set_page_config(page_title="Gestão de Riscos IBAMA", layout="wide")

# Paleta Oficial (Carvalho & Fadul)
COR_PRIMARIA = "#7c1617"     # Vermelho Bordô
COR_SECUNDARIA = "#1a1a1a"   # Preto/Chumbo
COR_DOURADO = "#c09f52"      # Dourado de Apoio
COR_FUNDO_APP = "#fcfaf9"    # Off-white quente (Identidade do escritório)
COR_BORDAS = "#e2e8f0"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    /* =========================================================
       ☀️ TEMA PADRÃO (MODO CLARO / LIGHT MODE)
       ========================================================= */
    .stApp {{
        background-color: {COR_FUNDO_APP};
        color: {COR_SECUNDARIA};
    }}
    
    [data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-right: 2px solid {COR_PRIMARIA};
    }}
    
    [data-testid="collapsedControl"] svg {{
        color: {COR_PRIMARIA} !important;
        width: 24px;
        height: 24px;
    }}
    
    header {{ background: transparent !important; }}
    .block-container {{ padding-top: 1rem; padding-bottom: 2rem; max-width: 95%; }}
    
    h1 {{ color: {COR_PRIMARIA} !important; font-weight: 700 !important; font-size: 2rem !important; text-transform: uppercase; letter-spacing: -0.5px; padding-bottom: 5px; }}
    h3 {{ color: {COR_SECUNDARIA} !important; font-weight: 600 !important; font-size: 1.1rem !important; }}
    
    .stTabs [data-baseweb="tab-list"] {{ border-bottom: 1px solid {COR_BORDAS}; gap: 10px; }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 14px;
        color: #64748b;
        padding: 12px 20px;
        background-color: transparent;
        border-radius: 0px;
    }}
    .stTabs [aria-selected="true"] {{
        color: {COR_PRIMARIA} !important;
        border-bottom: 3px solid {COR_PRIMARIA} !important;
        background-color: transparent;
    }}
    
    /* Caixas de Alerta (st.info / st.error) */
    div[data-testid="stNotification"] {{
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
    }}
    div[data-testid="stNotification"] p {{
        color: #1e293b !important;
        font-weight: 500 !important;
    }}

    /* --- AQUI ESTÃO AS REGRAS QUE SUBSTITUIRAM O TEXTÃO DO HTML --- */
    .kpi-card {{
        flex: 1;
        background: #ffffff;
        padding: 22px;
        border-radius: 6px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.04);
        border: 1px solid transparent;
    }}
    .kpi-title {{ font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
    .kpi-val {{ font-size: 30px; color: {COR_SECUNDARIA}; font-weight: 700; margin-top: 4px; white-space: nowrap; }}

    /* =========================================================
       🌙 ADAPTAÇÃO AUTOMÁTICA PARA MODO ESCURO (DARK MODE)
       ========================================================= */
    @media (prefers-color-scheme: dark) {{
        .stApp {{
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: #161b22 !important;
            border-right: 2px solid {COR_PRIMARIA} !important;
        }}
        h3 {{ color: #f8fafc !important; }}
        .stTabs [data-baseweb="tab"] {{ color: #94a3b8; }}
        
        div[data-testid="stNotification"] {{
            background-color: #1e293b !important;
            border: 1px solid #475569 !important;
        }}
        div[data-testid="stNotification"] p {{ color: #f8fafc !important; }}

        /* À noite, os KPIs ficam escuros automaticamente! */
        .kpi-card {{
            background: #161b22 !important;
            border: 1px solid #334155 !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
        }}
        .kpi-title {{ color: #94a3b8 !important; }}
        .kpi-val {{ color: #f8fafc !important; }}

        div[data-testid="stExpander"] {{
            background-color: #161b22 !important;
            border: 1px solid #334155 !important;
            border-radius: 6px !important;
        }}
        div[data-testid="stExpander"] details summary p {{
            color: #f8fafc !important;
        }}
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

def get_image_base64(caminho):
    try:
        with open(caminho, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except:
        return ""

# ==========================================
# 2. MOTOR DE DADOS E LIMPEZA DE ERROS (REGEX)
# ==========================================
def classificar_objeto(desc):
    desc = str(desc).lower()
    if 'defeso' in desc and 'lagosta' in desc: return 'Defeso da Lagosta 🦞'
    elif 'defeso' in desc and ('pargo' in desc or 'lutjanus' in desc): return 'Defeso do Pargo 🐟'
    elif 'lagosta' in desc: return 'Lagosta (Fora do Defeso) 🦞'
    elif 'pargo' in desc or 'lutjanus' in desc: return 'Pargo (Fora do Defeso) 🐟'
    elif 'rapp' in desc or 'ctf' in desc: return 'Omissão Documental (RAPP/CTF)'
    elif 'siscomex' in desc or 'due' in desc or 'ncm' in desc or 'lpco' in desc: return 'Aduaneiro / Siscomex / LPCO'
    elif 'licença' in desc or 'rgp' in desc: return 'Falta de Licença / RGP'
    elif 'resíduo' in desc or 'poluição' in desc: return 'Poluição / Resíduos Sólidos'
    else: return 'Administrativo / Diversos'

def limpar_e_separar_ufs(val):
    val_str = str(val).upper()
    encontrados = []
    for token in re.findall(r'\b[A-Z]{2}\b', val_str):
        if token in {'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'}:
            encontrados.append(token)
    return list(set(encontrados)) if encontrados else ['N/D']

@st.cache_data(ttl=600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmM6tv0bqBxxx4Rc9pAYGPDXDAfWCV3fnv6mZAwoAYfaXBn_jhVNadrlsALWsyFvSYai-oD7QHk_VD/pub?output=csv"
    df = pd.read_csv(url)
    
    df.columns = df.columns.str.strip()
    
    if 'Valor Multa' in df.columns:
        df['Valor Multa'] = df['Valor Multa'].astype(str)
        df['Valor Multa'] = df['Valor Multa'].str.replace('R$', '', regex=False)
        df['Valor Multa'] = df['Valor Multa'].str.replace(' ', '', regex=False)
        df['Valor Multa'] = df['Valor Multa'].str.replace('.', '', regex=False)
        df['Valor Multa'] = df['Valor Multa'].str.replace(',', '.', regex=False)
        df['Valor Multa'] = pd.to_numeric(df['Valor Multa'], errors='coerce').fillna(0)
    else:
        df['Valor Multa'] = 0

    df['Descrição das Autuações'] = df['Descrição das Autuações'].fillna('-')
    df['Sanções Aplicadas'] = df['Sanções Aplicadas'].fillna('-')
    df['Data Infração'] = pd.to_datetime(df['Data Infração'], errors='coerce')
    
    df['Objeto Identificado'] = df['Descrição das Autuações'].apply(classificar_objeto)
    
    df['Apreensão'] = df['Sanções Aplicadas'].str.contains('apreensão', case=False, na=False)
    df['Depósito'] = df['Sanções Aplicadas'].str.contains('depósito', case=False, na=False)
    df['Embargo/Interdição'] = df['Sanções Aplicadas'].str.contains('embargo|interdição', case=False, na=False)
    df['Suspensão'] = df['Sanções Aplicadas'].str.contains('suspensão', case=False, na=False)
    
    df['UF_Lista'] = df['UF'].apply(limpar_e_separar_ufs)
    df['UF_Clean'] = df['UF_Lista'].apply(lambda x: ' / '.join(x))
    
    return df

df_base = carregar_dados()
df = df_base.explode('UF_Lista')
df['UF_Filtro'] = df['UF_Lista']

# ==========================================
# 2.1 BASE GEORREFERENCIADA DO PARQUE INDUSTRIAL PRIME SEAFOOD
# ==========================================
def carregar_unidades_prime():
    unidades = [
        # --- MATRIZ ---
        {
            "nome": "Icapuí Matriz",
            "cnpj": "15.425.593/0001-02",
            "uf": "CE",
            "tipo": "Matriz / Administração",
            "endereco": "Av. Enoque Carneiro, nº 3203, Sala 1, Andar 1, Cajuais, Icapuí/CE - CEP: 62.810-000",
            "lat": -4.7112, "lon": -37.3621,
            "cor": "#c09f52", "icone": "star"
        },
        # --- INDÚSTRIAS DE PROCESSAMENTO ---
        {
            "nome": "Indústria Icapuí",
            "cnpj": "15.452.593/0007-90",
            "uf": "CE",
            "tipo": "Indústria / Beneficiamento",
            "endereco": "Av. Enoque Carneiro, nº 3203, Cajuais, Icapuí/CE - CEP: 62.810-000",
            "lat": -4.7115, "lon": -37.3618,
            "cor": "#7c1617", "icone": "industry"
        },
        {
            "nome": "Indústria Pará (Bragança)",
            "cnpj": "15.452.593/0011-76",
            "uf": "PA",
            "tipo": "Indústria / Beneficiamento",
            "endereco": "Rodovia PA 458, Bragança-Ajuruteua, S/N, Vila Bacuriteua (Zona Rural), Bragança/PA - CEP: 68.603-800",
            "lat": -0.9631, "lon": -46.7324,
            "cor": "#7c1617", "icone": "industry"
        },
        {
            "nome": "Indústria Recife",
            "cnpj": "15.452.593/0002-85",
            "uf": "PE",
            "tipo": "Indústria / Beneficiamento",
            "endereco": "Rua Comendador Moraes, nº 373, Loja 0000, Pina, Recife/PE - CEP: 51.010-197",
            "lat": -8.0872, "lon": -34.8841,
            "cor": "#7c1617", "icone": "industry"
        },
        {
            "nome": "Indústria Alcobaça",
            "cnpj": "15.452.593/0003-66",
            "uf": "BA",
            "tipo": "Indústria / Beneficiamento",
            "endereco": "Rodovia BR 418, S/N, KM 16, Sala 04, Taquari, Alcobaça/BA - CEP: 45.910-972",
            "lat": -17.5181, "lon": -39.1962,
            "cor": "#7c1617", "icone": "industry"
        },
        # --- FILIAIS DE CAPTAÇÃO E ENTREPOSTOS ---
        {
            "nome": "Belém (Campina de Icoaraci)",
            "cnpj": "15.452.593/0014-19",
            "uf": "PA",
            "tipo": "Filial de Captação",
            "endereco": "Rua Monsenhor José Maria Azevedo, nº 457, Sala E, Campina de Icoaraci, Belém/PA - CEP: 66.813-550",
            "lat": -1.2982, "lon": -48.4831,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Calçoene",
            "cnpj": "15.452.593/0020-67",
            "uf": "AP",
            "tipo": "Filial de Captação",
            "endereco": "Rua Hugulino Pinheiro, nº 411, Beira Rio, Calçoene/AP - CEP: 68.960-000",
            "lat": 2.4971, "lon": -50.9502,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Luís Correia",
            "cnpj": "15.452.593/0008-70",
            "uf": "PI",
            "tipo": "Filial de Captação",
            "endereco": "Av. José Maria de Lima, nº 53, Centro, Luís Correia/PI - CEP: 64.220-000",
            "lat": -2.8781, "lon": -41.6692,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Aranaú 1 (Acaraú)",
            "cnpj": "15.452.593/0019-23",
            "uf": "CE",
            "tipo": "Filial de Captação",
            "endereco": "Rua Miguel Arcanjo Meneses, nº 669, Distrito de Aranaú, Acaraú/CE - CEP: 62.580-000",
            "lat": -2.8361, "lon": -40.1332,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Aranaú 2 (Acaraú)",
            "cnpj": "15.452.593/0022-29",
            "uf": "CE",
            "tipo": "Filial de Captação",
            "endereco": "Vila Aranaú, Via 3 - Praia, nº 85, Distrito de Aranaú, Acaraú/CE - CEP: 62.580-000",
            "lat": -2.8351, "lon": -40.1311,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Areia Branca",
            "cnpj": "15.452.593/0016-80",
            "uf": "RN",
            "tipo": "Filial de Captação",
            "endereco": "Rua Coronel Solon, nº 352, Letra A, Quadra 006, Centro, Areia Branca/RN - CEP: 59.655-000",
            "lat": -4.9542, "lon": -37.1351,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Porto do Mangue",
            "cnpj": "15.452.593/0024-90",
            "uf": "RN",
            "tipo": "Filial de Captação",
            "endereco": "Rua Santo Antônio, nº 61, Centro, Porto do Mangue/RN - CEP: 59.668-000",
            "lat": -5.0681, "lon": -36.7822,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Touros",
            "cnpj": "15.452.593/0013-38",
            "uf": "RN",
            "tipo": "Filial de Captação",
            "endereco": "Rua Frei Serafim, nº 1955, Centro, Touros/RN - CEP: 59.584-000",
            "lat": -5.1972, "lon": -35.4611,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Pitangui (Extremoz)",
            "cnpj": "15.452.593/0023-00",
            "uf": "RN",
            "tipo": "Filial de Captação",
            "endereco": "Rua Projetada, S/N, Pitangui, Extremoz/RN - CEP: 59.575-000",
            "lat": -5.6791, "lon": -35.2452,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Natal (Ribeira)",
            "cnpj": "15.452.593/0018-42",
            "uf": "RN",
            "tipo": "Filial de Captação",
            "endereco": "Rua Chile, nº 164, Ribeira, Natal/RN - CEP: 59.012-250",
            "lat": -5.7731, "lon": -35.2032,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Baía Formosa 1",
            "cnpj": "15.452.593/0010-95",
            "uf": "RN",
            "tipo": "Filial de Captação",
            "endereco": "Praça da Conceição, nº 32, Centro, Baía Formosa/RN - CEP: 59.194-000",
            "lat": -6.3712, "lon": -35.0111,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Baía Formosa 2",
            "cnpj": "15.452.593/0021-48",
            "uf": "RN",
            "tipo": "Filial de Captação",
            "endereco": "Travessa João Porfírio de Souza, nº 61, Centro, Baía Formosa/RN - CEP: 59.194-000",
            "lat": -6.3721, "lon": -35.0122,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Acaú (Pitimbu)",
            "cnpj": "15.452.593/0004-47",
            "uf": "PB",
            "tipo": "Filial de Captação",
            "endereco": "Rua Projetada 05, nº 86A, Sala A, Lote 09, Quadra K, Loteamento Pontinha, Pitimbu/PB - CEP: 58.324-000",
            "lat": -7.4321, "lon": -34.8092,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "São José da Coroa Grande",
            "cnpj": "15.452.593/0012-57",
            "uf": "PE",
            "tipo": "Filial de Captação",
            "endereco": "3ª Travessa Constantino Gomes, S/N, Centro, São José da Coroa Grande/PE - CEP: 55.565-000",
            "lat": -8.8981, "lon": -35.1482,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Canavieiras",
            "cnpj": "15.452.593/0017-61",
            "uf": "BA",
            "tipo": "Filial de Captação",
            "endereco": "Rua Adelízia da Silva Rodrigues, nº 85, Centro, Canavieiras/BA - CEP: 45.860-000",
            "lat": -15.6762, "lon": -38.9481,
            "cor": "#0f172a", "icone": "anchor"
        },
        {
            "nome": "Pontal (Alcobaça)",
            "cnpj": "15.452.593/0009-51",
            "uf": "BA",
            "tipo": "Filial de Captação",
            "endereco": "Rua Contorno, nº 73 e 42, Barra, Alcobaça/BA - CEP: 45.910-000",
            "lat": -17.5251, "lon": -39.1912,
            "cor": "#0f172a", "icone": "anchor"
        }
    ]
    return pd.DataFrame(unidades)
    
def renderizar_kpis(df_filtrado):
    # CORREÇÃO: Deduplicar exclusivamente pela chave única do Auto de Infração
    df_unicos = df_filtrado.drop_duplicates(subset=['Nº A.I.'])
    
    valor_total = df_unicos['Valor Multa'].sum()
    valor_formatado = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    qtd_apreensoes = df_unicos['Apreensão'].sum() + df_unicos['Depósito'].sum()
    
    # Repare como o HTML ficou limpo e puxando a formatação do CSS acima:
    html = f"""
    <div style="display: flex; gap: 20px; margin-bottom: 25px; margin-top: 10px;">
        <div class="kpi-card" style="border-left: 4px solid {COR_PRIMARIA};">
            <div class="kpi-title">Autos de Infração Auditados</div>
            <div class="kpi-val">{len(df_unicos)}</div>
        </div>
        <div class="kpi-card" style="border-left: 4px solid {COR_DOURADO};">
            <div class="kpi-title">Passivo Financeiro Consolidado</div>
            <div class="kpi-val">{valor_formatado}</div>
        </div>
        <div class="kpi-card" style="border-left: 4px solid #475569;">
            <div class="kpi-title">Medidas Acautelatórias (Físicas)</div>
            <div class="kpi-val">{qtd_apreensoes}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ==========================================
# 3. BARRA LATERAL (LOGO, FILTROS E ASSINATURA)
# ==========================================
logo_cf = "logo.jpg"
if os.path.exists(logo_cf):
    st.sidebar.image(logo_cf, use_container_width=True)
else:
    st.sidebar.markdown(f"<h2 style='color:{COR_PRIMARIA}; text-align:center;'>CARVALHO & FADUL</h2>", unsafe_allow_html=True)

st.sidebar.markdown("---")

df_exploded = df_base.explode('UF_Lista')
df_exploded['UF_Filtro'] = df_exploded['UF_Lista']

# NOVO BUSCADOR GLOBAL NA LATERAL
st.sidebar.markdown("### 🔍 Busca Rápida")
busca_global = st.sidebar.text_input("", placeholder="Processo, A.I., CNPJ, Termo...", label_visibility="collapsed")

st.sidebar.markdown("### Filtros Globais")
lista_ufs = sorted([x for x in df_exploded['UF_Filtro'].unique() if x != 'N/D'])
uf_selecionada = st.sidebar.selectbox("Estado (UF):", ['Todos'] + lista_ufs)
tipo_selecionado = st.sidebar.selectbox("Natureza da Infração:", ['Todas'] + sorted(df_base['Tipo Infração'].dropna().unique().tolist()))
sancao_selecionada = st.sidebar.selectbox("Medidas Aplicadas:", ["Todas", "Com Apreensão", "Com Embargo", "Com Suspensão"])

# Aplicação dos Filtros da Barra Lateral
df = df_exploded.copy()

# Aplica a busca rápida global
if busca_global:
    mask_global = df.astype(str).apply(lambda x: x.str.contains(busca_global, case=False)).any(axis=1)
    df = df[mask_global]

if uf_selecionada != 'Todos': df = df[df['UF_Filtro'] == uf_selecionada]
if tipo_selecionado != 'Todas': df = df[df['Tipo Infração'] == tipo_selecionado]
if sancao_selecionada == "Com Apreensão": df = df[df['Apreensão'] == True]
elif sancao_selecionada == "Com Embargo": df = df[df['Embargo/Interdição'] == True]
elif sancao_selecionada == "Com Suspensão": df = df[df['Suspensão'] == True]

# Assinatura Profissional Elegante (Autora do Projeto)
st.sidebar.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
logo_jessica_base64 = get_image_base64("PHOTO-2026-06-26-16-01-19.jpg")
img_tag = f'<img src="data:image/jpeg;base64,{logo_jessica_base64}" style="width: 55px; height: 55px; border-radius: 50%; object-fit: cover; margin-bottom: 8px;">' if logo_jessica_base64 else ''

st.sidebar.markdown(f"""
<div style="text-align: center; border-top: 1px solid #e2e8f0; padding-top: 20px; margin-top: 10px;">
    {img_tag}
    <p style="font-size: 11px; color: {COR_SECUNDARIA}; margin: 0; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">Jéssica Araújo</p>
    <p style="font-size: 10px; color: #64748b; margin: 3px 0 0 0; line-height: 1.4;">
        Mestrado em Economia Ambiental (PPGE/UFPA)<br>
        Advocacia Ambiental & Climática<br>
        OAB/PA 37.748
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. CABEÇALHO E MENU SUPERIOR (TABS)
# ==========================================
st.markdown("<h1>Painel Estratégico de Gestão de Riscos e Passivo Ambiental</h1>", unsafe_allow_html=True)
logo_prime_base64 = get_image_base64("associados-prime-sem-fundo.png")
if logo_prime_base64:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-top: -5px; margin-bottom: 15px; opacity: 0.85;">
        <img src="data:image/png;base64,{logo_prime_base64}" style="height: 70px;">
        <span style="font-size: 15px; font-weight: 500; color: #475569; letter-spacing: 0.5px;">| PRIME SEAFOOD LTDA</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<p style='font-size: 15px; font-weight: 500; color: #475569; margin-top: -5px; margin-bottom: 15px;'>Prime Seafood LTDA | Auditoria de Conformidade Administrativa</p>", unsafe_allow_html=True)

st.markdown("<p style='font-size: 14px; color: #64748b; margin-bottom: 5px;'>Ferramenta analítica de contencioso administrativo, mapeamento de passivo e medidas acautelatórias do IBAMA.</p>", unsafe_allow_html=True)

renderizar_kpis(df)

tab_mapa, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Mapa Operacional", 
    "Auditoria de Objetos", 
    "Análise Regional", 
    "Tipologia e Sanções", 
    "Pesquisa Profunda", 
    "Base Consolidada",
    "Mitigação Operacional", 
    "Governança & Jurídico"
])

# Deduplicar exclusivamente pela chave única do Auto de Infração
df_unicos = df.drop_duplicates(subset=['Nº A.I.'])

# =====================================================================
# CSS AVANÇADO (EFEITOS 3D E CARTÕES FLUTUANTES)
# =====================================================================
st.markdown(f"""
<style>
    /* Efeito de Elevação 3D para os Paineis */
    .painel-3d {{
        background: linear-gradient(145deg, #ffffff, #f8fafc);
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05), 0 6px 6px rgba(0,0,0,0.05), inset 0 -3px 0 0 {COR_PRIMARIA};
        margin-bottom: 25px;
        transition: all 0.3s ease;
    }}
    .painel-3d:hover {{
        transform: translateY(-2px);
        box-shadow: 0 15px 25px rgba(0,0,0,0.1), 0 10px 10px rgba(0,0,0,0.05), inset 0 -3px 0 0 {COR_DOURADO};
    }}
    
    /* Estilo do Leitor de PDF Imersivo */
    .leitor-pdf-container {{
        background-color: #1e293b;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        margin-top: 15px;
        margin-bottom: 30px;
        border: 1px solid #475569;
    }}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# MOTOR GLOBAL DE LEITURA NATIVA (INFOGRÁFICO 3D - SEGUNDO CÉREBRO)
# =====================================================================
if 'leitor_ativo' not in st.session_state:
    st.session_state['leitor_ativo'] = None

def carregar_pdf_seguro(caminho_arquivo):
    import os
    try:
        with open(caminho_arquivo, "rb") as file:
            return file.read()
    except FileNotFoundError:
        return b"Arquivo Pendente"

def renderizar_leitor_nativo(chave_aba):
    """
    Renderiza o Infográfico Vivo com Glassmorphism, Hover 3D e Neon Glow.
    Contém a transcrição exata e interativa do PDF Original.
    """
    if st.session_state['leitor_ativo']:
        
        # 1. MAPEAMENTO OFICIAL DOS ARQUIVOS PDF (Para o botão de download)
        mapa_arquivos = {
            "DOC-01: Guia do Motorista": "Guia_Bolso_Motorista_Prime_Seafood.pdf",
            "DOC-02: Triagem de Lagosta": "POP_001_Triagem_Lagosta_Prime.pdf",
            "DOC-03: Manual do Defeso": "Manual_Compliance_Defeso_Estoque.pdf",
            "DOC-04: Guia VMS Pargo": "Guia_VMS_Controle_Frota_Pargo.pdf",
            "DOC-05: Teses Defensivas": "Matriz_Teses_Defensivas_IBAMA.pdf",
            "DOC-06: Due Diligence RGP": "Procedimento_Due_Diligence_RGP.pdf",
            "DOC-07: Cartilha de Petrechos": "Cartilha_Petrechos_Certo_Errado.pdf",
            "DOC-08: Checklist Exportação": "Checklist_Sinal_Verde_Exportacao.pdf",
            "DOC-09: Resumo Executivo": "DOC_09_Resumo_Executivo.pdf",
            "DOC-10: E-book Institucional": "DOC_10_Ebook_Institucional.pdf"
        }
        arquivo_pdf_atual = mapa_arquivos.get(st.session_state['leitor_ativo'])

        # 2. MENU SUPERIOR DO LEITOR (Botão Fechar e Botão Download)
        c_fechar, c_vazio, c_baixar = st.columns([1.5, 2, 1.5])
        with c_fechar:
            if st.button("❌ FECHAR INFOGRÁFICO", use_container_width=True, type="primary", key=f"fechar_{chave_aba}"):
                st.session_state['leitor_ativo'] = None
                st.rerun()
        with c_baixar:
            dados_pdf = carregar_pdf_seguro(arquivo_pdf_atual)
            st.download_button(
                label="📥 BAIXAR PDF ORIGINAL", 
                data=dados_pdf, 
                file_name=arquivo_pdf_atual, 
                mime="application/pdf", 
                key=f"dl_{chave_aba}",
                use_container_width=True
            )
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 3. CSS AVANÇADO (GLASSMORPHISM, HOVER 3D, NEON GLOW)
        st.markdown("""
        <style>
            /* Container Tático */
            .hud-wrapper {
                background-color: #0b1120; padding: 40px; border-radius: 20px;
                box-shadow: inset 0 0 50px rgba(0,0,0,0.8), 0 25px 50px -12px rgba(0,0,0,0.9);
                border: 1px solid #1e293b; margin-bottom: 30px; position: relative; overflow: hidden;
            }
            /* Brilho de fundo militar/tático */
            .hud-wrapper::before {
                content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
                background: radial-gradient(circle, rgba(192,159,82,0.05) 0%, rgba(11,17,32,0) 50%);
                z-index: 0; pointer-events: none;
            }
            /* Cabeçalho do HUD */
            .hud-header { text-align: center; position: relative; z-index: 1; margin-bottom: 40px; }
            .hud-title { color: #c09f52; font-size: 32px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 15px rgba(192,159,82,0.4); margin: 0; }
            .hud-subtitle { color: #94a3b8; font-size: 14px; letter-spacing: 1px; text-transform: uppercase; }
            /* Grid Responsivo para os 4 Módulos */
            .grid-3d { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; position: relative; z-index: 1; }
            /* GLASSMORPHISM: Fundos escuros translúcidos */
            .card-glass {
                background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.6); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                display: flex; flex-direction: column;
            }
            /* HOVER 3D + NEON GLOW */
            .card-glass:hover { transform: translateY(-10px) scale(1.03); z-index: 10; }
            .glow-green:hover { border-color: #22c55e; box-shadow: 0 15px 40px rgba(34, 197, 94, 0.3), inset 0 0 20px rgba(34, 197, 94, 0.1); }
            .glow-blue:hover { border-color: #3b82f6; box-shadow: 0 15px 40px rgba(59, 130, 246, 0.3), inset 0 0 20px rgba(59, 130, 246, 0.1); }
            .glow-gold:hover { border-color: #c09f52; box-shadow: 0 15px 40px rgba(192, 159, 82, 0.3), inset 0 0 20px rgba(192, 159, 82, 0.1); }
            .glow-red:hover { border-color: #ef4444; box-shadow: 0 15px 40px rgba(239, 68, 68, 0.3), inset 0 0 20px rgba(239, 68, 68, 0.1); }
            /* Tipografia Interna */
            .card-icon { font-size: 32px; margin-bottom: 10px; }
            .card-title { color: #f8fafc; font-size: 16px; font-weight: 800; margin-top: 0; margin-bottom: 15px; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }
            .card-list { list-style: none; padding: 0; margin: 0; }
            .card-list li { color: #cbd5e1; font-size: 13.5px; margin-bottom: 12px; line-height: 1.5; padding-left: 20px; position: relative; }
            .card-list li::before { content: '⬡'; position: absolute; left: 0; color: #64748b; font-size: 12px; transition: color 0.3s; }
            .card-glass:hover .card-list li::before { color: #c09f52; }
            .card-list b { color: #ffffff; font-weight: 600; }
        </style>
        """, unsafe_allow_html=True)

       # =================================================================
        # 4. CONTEÚDO NATIVO EXATO DO PDF "GUIA DO MOTORISTA"
        # =================================================================
        if st.session_state['leitor_ativo'] == "DOC-01: Guia do Motorista":
            st.markdown("""
            <style>
                /* Blindagem CSS para garantir que o Streamlit renderize como UI Avançada */
                .cf-hud-wrapper {
                    background-color: #fcfaf9;
                    padding: 45px;
                    border-radius: 16px;
                    box-shadow: 0 15px 40px rgba(0,0,0,0.06);
                    border: 1px solid #e2e8f0;
                    margin-bottom: 30px;
                    font-family: 'Inter', sans-serif;
                }
                .cf-header {
                    text-align: center;
                    margin-bottom: 45px;
                    border-bottom: 2px solid #e2e8f0;
                    padding-bottom: 25px;
                }
                .cf-title {
                    color: #7c1617;
                    font-size: 34px;
                    font-weight: 900;
                    text-transform: uppercase;
                    margin: 0 0 10px 0;
                    letter-spacing: 1px;
                }
                .cf-subtitle {
                    color: #c09f52;
                    font-size: 15px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    margin: 0;
                }
                .cf-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                    gap: 30px;
                }
                .cf-card {
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.03);
                    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    position: relative;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }
                .cf-card:hover {
                    transform: translateY(-10px);
                    box-shadow: 0 20px 40px rgba(124, 22, 23, 0.1);
                    border-color: #c09f52;
                }
                .cf-card-top-line {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 5px;
                }
                /* Cores de Identificação 3D no topo de cada cartão */
                .cf-line-green { background: linear-gradient(90deg, #166534, #22c55e); }
                .cf-line-gray { background: linear-gradient(90deg, #1a1a1a, #475569); }
                .cf-line-gold { background: linear-gradient(90deg, #92400e, #c09f52); }
                .cf-line-red { background: linear-gradient(90deg, #7c1617, #dc2626); }
                
                .cf-icon-wrapper {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    margin-bottom: 20px;
                    border-bottom: 1px solid #f1f5f9;
                    padding-bottom: 15px;
                }
                .cf-icon { font-size: 32px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1)); }
                .cf-card-title { color: #1a1a1a; font-size: 16px; font-weight: 800; margin: 0; text-transform: uppercase; line-height: 1.3; }
                .cf-card-desc { color: #64748b; font-size: 13px; margin: 0 0 20px 0; font-weight: 500; line-height: 1.5; }
                .cf-list { list-style: none; padding: 0; margin: 0; flex-grow: 1; }
                .cf-list li { color: #334155; font-size: 13.5px; margin-bottom: 15px; line-height: 1.6; padding-left: 24px; position: relative; }
                .cf-list li::before { content: '❖'; position: absolute; left: 0; top: 2px; color: #c09f52; font-size: 12px; transition: color 0.3s ease; }
                .cf-card:hover .cf-list li::before { color: #7c1617; }
                .cf-list b { color: #1a1a1a; font-weight: 700; }
                .cf-alert-box { background: #fff1f2; border: 1px solid #fecdd3; border-left: 4px solid #e11d48; padding: 15px; border-radius: 6px; margin-top: 20px; font-size: 12px; color: #9f1239; font-weight: 600; line-height: 1.5; }
            </style>

            <div class="cf-hud-wrapper">
                <div class="cf-header">
                    <h1 class="cf-title">Guia de Bolso Executivo</h1>
                    <p class="cf-subtitle">Abordagem Fiscal & Transporte Normativo | Prime Seafood</p>
            </div>
                
                <div class="cf-grid">
                    
                    <div class="cf-card">
                        <div class="cf-card-top-line cf-line-green"></div>
                        <div class="cf-icon-wrapper">
                            <div class="cf-icon">🚦</div>
                            <h3 class="cf-card-title" style="color: #166534;">1. Checklist Operacional<br>"Sinal Verde"</h3>
            </div>
                        <p class="cf-card-desc">Antes de dar a partida, audite a pasta da cabine. A ausência de qualquer item abaixo veta a saída da doca:</p>
                        <ul class="cf-list">
                            <li><b>NF-e e DANFE:</b> Confirme a separação exata e clara entre Peso Bruto e Peso Líquido.</li>
                            <li><b>GTP (Guia de Trânsito):</b> Dentro da validade e assinada. (Em período de defeso, inclua obrigatoriamente a Declaração de Estoque).</li>
                            <li><b>RGP e CTF/APP:</b> Cópias vigentes da indústria, da embarcação fornecedora e da transportadora.</li>
                            <li><b>Lacres e Termógrafo:</b> Verifique fisicamente se a numeração bate perfeitamente com o descrito na Nota Fiscal.</li>
                        </ul>
            </div>

                    <div class="cf-card">
                        <div class="cf-card-top-line cf-line-gray"></div>
                        <div class="cf-icon-wrapper">
                            <div class="cf-icon">👮</div>
                            <h3 class="cf-card-title" style="color: #1a1a1a;">2. Conduta na Abordagem<br>(Cordialidade Técnica)</h3>
            </div>
                        <p class="cf-card-desc">O motorista representa legalmente a empresa perante as autoridades (IBAMA, PRF, MAPA):</p>
                        <ul class="cf-list">
                            <li><b>Comunicação:</b> Responda estritamente ao que for perguntado de forma respeitosa. Não discuta biologia, legislação ou regras industriais.</li>
                            <li><b>Preservação da Carga:</b> Nunca rompa o lacre do baú sozinho. A abertura só pode ocorrer por ordem explícita e com a presença física do fiscal.</li>
                            <li><b>Aferição de Peso:</b> Se o fiscal alegar excesso de peso "visual", exija formalmente a pesagem em balança certificada e calibrada pelo INMETRO.</li>
                        </ul>
            </div>

                    <div class="cf-card">
                        <div class="cf-card-top-line cf-line-gold"></div>
                        <div class="cf-icon-wrapper">
                            <div class="cf-icon">🦞</div>
                            <h3 class="cf-card-title" style="color: #92400e;">3. Rigor das Espécies<br>(Defesa Técnica no Trânsito)</h3>
            </div>
                        <p class="cf-card-desc">Argumentos rápidos de linha de frente contra autuações arbitrárias por falta de perícia fiscal:</p>
                        <ul class="cf-list">
                            <li><b>Lagosta Viva:</b> Alerte os fiscais sobre o risco iminente de choque térmico ao abrir o baú. Justifique eventual mortalidade como estresse natural do transporte, não por descaudamento ilegal.</li>
                            <li><b>Tamanhos Mínimos (Tolerância Zero):</b> Lagosta Vermelha (22cm total / 13cm cauda). Lagosta Verde (19cm total / 11cm cauda).</li>
                            <li><b>Pargo:</b> Absolutamente todas as caixas devem estar etiquetadas (Nome científico, lote e RGP). É expressamente proibido o transporte a granel.</li>
                        </ul>
            </div>

                    <div class="cf-card">
                        <div class="cf-card-top-line cf-line-red"></div>
                        <div class="cf-icon-wrapper">
                            <div class="cf-icon">🚨</div>
                            <h3 class="cf-card-title" style="color: #7c1617;">4. Protocolo de Crise<br>(SLA Jurídico de 48H)</h3>
            </div>
                        <p class="cf-card-desc">Se a autoridade lavrar o Auto de Infração ou Termo de Apreensão, o tempo é o fator mais crítico:</p>
                        <ul class="cf-list">
                            <li><b>Assine Sempre:</b> Recusar a assinatura é um erro grave que anula a boa-fé. Assine e escreva a <b>ressalva técnica</b> no campo de observações (ex: "pesagem sem balança do INMETRO" ou "mortalidade por estresse térmico").</li>
                            <li><b>Roteiro dos 30 Minutos:</b> Fotografe em alta nitidez o Auto de Infração, Termo de Apreensão, todos os lacres e o painel de temperatura do termógrafo.</li>
                        </ul>
                        <div class="cf-alert-box">
                            ⚠️ PLANTÃO JURÍDICO: Envie todo o material fotográfico imediatamente para a base antes mesmo de deixar o posto fiscal.
            </div>
            </div>

            </div>
            </div>
            """, unsafe_allow_html=True)
            
        # 4. OS OUTROS DOCUMENTOS (EM CONSTRUÇÃO)
        else:
            st.markdown(f"""
            <div style='background-color: #fcfaf9; padding: 40px; border-radius: 16px; border: 1px solid #e2e8f0; margin-bottom: 30px;'>
                <h2 style='color: #7c1617; text-align: center;'>🚧 Módulo {st.session_state['leitor_ativo']}</h2>
                <p style='color: #64748b; text-align: center;'>O infográfico vivo deste documento está na fila de desenvolvimento. Utilize o botão <b>BAIXAR PDF ORIGINAL</b> acima para acessar o arquivo oficial na íntegra.</p>
            </div>
            """, unsafe_allow_html=True)
        
# =====================================================================
# 2. BLOCO DO MAPA AQUI 
# =====================================================================

# =====================================================================
# ABA DO MAPA: MATRIZ GEORREFERENCIADA E MALHA OPERACIONAL
# =====================================================================
with tab_mapa:
    # 1. CABEÇALHO TÉCNICO LIMPO
    st.markdown(f"""
    <div style="border-left: 4px solid {COR_PRIMARIA}; padding-left: 14px; margin-bottom: 15px;">
        <h2 style="margin: 0; color: {COR_SECUNDARIA}; font-size: 1.4rem; font-weight: 700; text-transform: uppercase; letter-spacing: -0.5px;">
            Matriz Georreferenciada e Malha Operacional
        </h2>
        <p style="margin: 3px 0 0 0; color: #64748b; font-size: 13.5px;">
            Mapeamento espacial das unidades da Prime Seafood e sobreposição do contencioso administrativo do IBAMA.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregamento e filtro da base de unidades
    df_unidades_mapa = carregar_unidades_prime()
    if uf_selecionada != 'Todos':
        df_unidades_mapa = df_unidades_mapa[df_unidades_mapa['uf'] == uf_selecionada]

    # Controle de Estado do Layout (Tela Cheia vs Lado a Lado)
    if "map_fullscreen" not in st.session_state:
        st.session_state["map_fullscreen"] = True

    # 2. BARRA DE COMANDO SUPERIOR
    c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1.8, 1.4, 0.3], gap="medium")
    
    with c_ctrl1:
        st.markdown("<b style='font-size:11.5px; color:#1a1a1a; text-transform:uppercase;'>Selecione ou clique na unidade no mapa:</b>", unsafe_allow_html=True)
        lista_opcoes_und = ["Visão Macrorregional (Todos os Polos)"] + df_unidades_mapa['nome'].tolist()
        unidade_dropdown = st.selectbox("", lista_opcoes_und, label_visibility="collapsed", key="mapa_select_und")
        
    with c_ctrl2:
        st.markdown("<b style='font-size:11.5px; color:#1a1a1a; text-transform:uppercase;'>Camadas do Mapa:</b>", unsafe_allow_html=True)
        exibir_camada = st.radio(
            "",
            options=["Visão Integrada", "Apenas Malha Prime Seafood"],
            horizontal=True,
            label_visibility="collapsed",
            key="mapa_seletor_camadas"
        )
        
    with c_ctrl3:
        st.markdown("<b style='font-size:11.5px; color:transparent;'>Layout</b>", unsafe_allow_html=True)
        # BOTÃO DISCRETO E PROFISSIONAL (Apenas Ícone)
        icone_btn = "🗗" if st.session_state["map_fullscreen"] else "⛶"
        if st.button(icone_btn, help="Clique para alternar entre Mapa Expandido e Modo Dividido (Lado a Lado)", use_container_width=True):
            st.session_state["map_fullscreen"] = not st.session_state["map_fullscreen"]
            st.rerun()

    # =================================================================
    # INTEGRAÇÃO BIDIRECIONAL (Clique no Mapa = Atualização da Unidade)
    # =================================================================
    unidade_ativa = unidade_dropdown
    if "ultimo_clique_mapa" in st.session_state and st.session_state["ultimo_clique_mapa"]:
        lat_clique = st.session_state["ultimo_clique_mapa"].get("lat")
        lon_clique = st.session_state["ultimo_clique_mapa"].get("lng")
        if lat_clique and lon_clique:
            for _, und in df_unidades_mapa.iterrows():
                if abs(und['lat'] - lat_clique) < 0.05 and abs(und['lon'] - lon_clique) < 0.05:
                    unidade_ativa = und['nome']
                    break

    # Processamento de Coordenadas e Escopo Regional
    if unidade_ativa == "Visão Macrorregional (Todos os Polos)":
        lat_centro, lon_centro, zoom_inical = -5.5, -39.0, 6
        df_autos_regiao = df.copy() if uf_selecionada == 'Todos' else df[df['UF_Filtro'] == uf_selecionada]
        nome_regiao = "Malha Global"
        obs_unidade = "Visão panorâmica da infraestrutura logístico-industrial. Selecione ou clique em uma unidade costeira no mapa para auditar a exposição financeira e diretrizes preventivas da respectiva região."
    else:
        und_data = df_unidades_mapa[df_unidades_mapa['nome'] == unidade_ativa].iloc[0]
        lat_centro, lon_centro, zoom_inical = und_data['lat'], und_data['lon'], 10
        df_autos_regiao = df[df['UF_Filtro'] == und_data['uf']]
        nome_regiao = f"Estado: {und_data['uf']}"
        
        if "Indústria" in und_data['tipo'] or "Matriz" in und_data['tipo']:
            obs_unidade = f"<b>{und_data['nome']}:</b> Unidade de processamento primário e armazenamento. Risco crítico atrelado à declaração de estoques no Sistema PesqBrasil durante o período de defeso e segregação física em câmaras frigoríficas. Exige due diligence rigorosa na documentação de entrada (NF-e/GTP)."
        else:
            obs_unidade = f"<b>{und_data['nome']}:</b> Posto de captação costeira e transbordo logístico. Risco crítico concentrado no transporte rodoviário e na biometria de espécimes. Obrigatoriedade de validação mensal da vigência do RGP das embarcações fornecedoras e protocolo de vitalidade (70%) pré-embarque."

    # Cálculo Exato dos KPIs Regionais
    df_autos_regiao_unicos = df_autos_regiao.drop_duplicates(subset=['Nº A.I.'])
    total_autos_reg = len(df_autos_regiao_unicos)
    val_total_reg = df_autos_regiao_unicos['Valor Multa'].sum()
    val_fmt_reg = f"R$ {val_total_reg:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    if not df_autos_regiao_unicos.empty and 'Objeto Identificado' in df_autos_regiao_unicos.columns:
        obj_lider_reg = df_autos_regiao_unicos['Objeto Identificado'].mode()[0]
    else:
        obj_lider_reg = "Sem registros na região"

    # Blocos HTML do Relatório Analítico
    kpi1_html = f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid {COR_PRIMARIA}; padding:14px; border-radius:4px; box-shadow:0 1px 2px rgba(0,0,0,0.02); margin-bottom: 10px;">
            <span style="font-size:10.5px; color:#64748b; font-weight:600; text-transform:uppercase;">Autuações no Estado ({nome_regiao})</span><br>
            <b style="font-size:20px; color:{COR_SECUNDARIA};">{total_autos_reg} Auto(s)</b>
        </div>
    """
    kpi2_html = f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid {COR_DOURADO}; padding:14px; border-radius:4px; box-shadow:0 1px 2px rgba(0,0,0,0.02); margin-bottom: 10px;">
            <span style="font-size:10.5px; color:#64748b; font-weight:600; text-transform:uppercase;">Infração Preponderante na Região</span><br>
            <b style="font-size:13.5px; color:#7c1617; display:block; margin-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{obj_lider_reg}</b>
        </div>
    """
    kpi3_html = f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #475569; padding:14px; border-radius:4px; box-shadow:0 1px 2px rgba(0,0,0,0.02); margin-bottom: 10px;">
            <span style="font-size:10.5px; color:#64748b; font-weight:600; text-transform:uppercase;">Exposição Financeira ({nome_regiao})</span><br>
            <b style="font-size:20px; color:{COR_SECUNDARIA};">{val_fmt_reg}</b>
        </div>
    """
    diretriz_html = f"""
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-left:4px solid {COR_PRIMARIA}; padding:14px; border-radius:4px; font-size:11.5px; color:#334155; line-height:1.5; margin-top:4px; margin-bottom:15px;">
            <b style="color:{COR_PRIMARIA}; font-size:11px; text-transform:uppercase;">Diretriz de Conformidade Operacional:</b><br>
            {obs_unidade}
        </div>
    """

    # =================================================================
    # MAPA GEORREFERENCIADO
    # =================================================================
    mapa = folium.Map(
        location=[lat_centro, lon_centro],
        zoom_start=zoom_inical,
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google Satellite"
    )

    # CAMADA: MALHA OPERACIONAL PRIME SEAFOOD
    for _, und in df_unidades_mapa.iterrows():
        und_uf = und['uf']
        df_uf_spec = df[df['UF_Filtro'] == und_uf].drop_duplicates(subset=['Nº A.I.'])
        cnt_autos = len(df_uf_spec)
        obj_top = df_uf_spec['Objeto Identificado'].mode()[0] if not df_uf_spec.empty and 'Objeto Identificado' in df_uf_spec.columns else "N/D"
        obs_popup = "Auditar declaração de estoques e bloqueio sistêmico no defeso." if "Indústria" in und['tipo'] else "Auditar biometria no cais e licença de frota."
        
        # RESTAURADO: Informação detalhada de auditoria dentro do balão do mapa
        html_popup = f"""
        <div style="font-family: 'Inter', sans-serif; width: 270px; padding: 4px;">
            <b style="color: {COR_PRIMARIA}; font-size: 13px; text-transform: uppercase;">{und['nome']}</b><br>
            <span style="background: {und['cor']}; color: #fff; padding: 2px 6px; border-radius: 3px; font-size: 9.5px; font-weight: bold; text-transform: uppercase;">{und['tipo']}</span>
            <hr style="margin: 8px 0; border: 0; border-top: 1px solid #e2e8f0;">
            <b style="font-size: 11px; color: #1a1a1a;">CNPJ:</b> <span style="font-size: 11px; color: #475569;">{und['cnpj']}</span><br>
            <b style="font-size: 11px; color: #1a1a1a;">Localização:</b><br>
            <span style="font-size: 10px; color: #64748b; line-height: 1.3;">{und['endereco']}</span>
            
            <div style="background: #fdf2f2; border: 1px solid #fecaca; padding: 8px; border-radius: 4px; margin-top: 10px;">
                <b style="font-size: 10px; color: #991b1b; text-transform: uppercase;">Auditoria Regional ({und_uf}):</b><br>
                <span style="font-size: 10.5px; color: #1a1a1a;"><b>Volume de Autuações:</b> {cnt_autos} AI(s)</span><br>
                <span style="font-size: 10.5px; color: #1a1a1a;"><b>Objeto Crítico:</b> {obj_top}</span><br>
                <hr style="margin: 4px 0; border: 0; border-top: 1px dashed #fca5a5;">
                <span style="font-size: 10px; color: #7c1617;"><b>Foco Preventivo:</b> {obs_popup}</span>
            </div>
        </div>
        """
        destaque_icone = "star" if und['nome'] == unidade_ativa else und['icone']
        folium.Marker(
            location=[und['lat'], und['lon']],
            popup=folium.Popup(html_popup, max_width=300),
            tooltip=f"🏢 {und['nome']} | Clique para auditar a região",
            icon=folium.Icon(color="darkred" if und['cor'] == "#7c1617" else ("beige" if und['cor'] == "#c09f52" else "darkblue"), icon=destaque_icone, prefix='fa')
        ).add_to(mapa)

    # CAMADA: CONTENCIOSO ADMINISTRATIVO (IBAMA)
    if exibir_camada == "Visão Integrada":
        df_mapa_autos = df.drop_duplicates(subset=['Nº A.I.'])
        for _, auto in df_mapa_autos.iterrows():
            if pd.notnull(auto.get('Lat')) and pd.notnull(auto.get('Lon')):
                popup_auto = f"""
                <div style="font-family: 'Inter', sans-serif; width: 240px;">
                    <b style="color: #ff2a2a; font-size: 11px; text-transform: uppercase;">Auto de Infração (IBAMA)</b><br>
                    <span style="font-size: 12.5px; font-weight: bold; color: #1a1a1a;">Nº {auto['Nº A.I.']}</span>
                    <hr style="margin: 6px 0; border: 0; border-top: 1px solid #e2e8f0;">
                    <b style="font-size:11px;">Exposição Financeira:</b> <span style="color: #7c1617; font-weight: bold;">R$ {auto['Valor Multa']:,.2f}</span><br>
                    <b style="font-size:11px;">Objeto Fiscalizado:</b> <span style="color: #334155; font-size:11px;">{auto['Objeto Identificado']}</span><br>
                    <b style="font-size:11px;">Tipologia:</b> <span style="font-size: 10px; color: #64748b;">{auto['Tipo Infração']}</span>
                </div>
                """
                folium.CircleMarker(
                    location=[auto['Lat'], auto['Lon']],
                    radius=6, popup=folium.Popup(popup_auto, max_width=280),
                    tooltip=f"🚨 A.I: {auto['Nº A.I.']} | {auto['Objeto Identificado']}",
                    color="#ff2a2a", fill=True, fill_color="#ff2a2a", fill_opacity=0.8
                ).add_to(mapa)

    # =================================================================
    # RENDERIZAÇÃO E CAPTURA DE CLIQUE NO MAPA
    # =================================================================
    if st.session_state["map_fullscreen"]:
        # MODO EXPANDIDO (Tela Cheia)
        st.markdown(f"<h3 style='color: {COR_SECUNDARIA}; font-size: 1.1rem; border-bottom: 2px solid {COR_BORDAS}; padding-bottom: 5px; margin-top: 5px;'>Relatório Regional de Exposição</h3>", unsafe_allow_html=True)
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3, gap="medium")
        with col_kpi1: st.markdown(kpi1_html, unsafe_allow_html=True)
        with col_kpi2: st.markdown(kpi2_html, unsafe_allow_html=True)
        with col_kpi3: st.markdown(kpi3_html, unsafe_allow_html=True)
        st.markdown(diretriz_html, unsafe_allow_html=True)
        
        map_output = st_folium(mapa, width="100%", height=620, key="mapa_full")
    else:
        # MODO DIVIDIDO (Lado a Lado)
        st.markdown("<br>", unsafe_allow_html=True)
        col_relatorio, col_mapa = st.columns([1.1, 2.2], gap="large")
        
        with col_relatorio:
            st.markdown(f"<h3 style='color: {COR_SECUNDARIA}; font-size: 1.1rem; border-bottom: 2px solid {COR_BORDAS}; padding-bottom: 5px; margin-top: 0;'>Relatório Regional</h3>", unsafe_allow_html=True)
            st.markdown(kpi1_html, unsafe_allow_html=True)
            st.markdown(kpi2_html, unsafe_allow_html=True)
            st.markdown(kpi3_html, unsafe_allow_html=True)
            st.markdown(diretriz_html, unsafe_allow_html=True)
            
        with col_mapa:
            map_output = st_folium(mapa, width="100%", height=550, key="mapa_split")

    if map_output and "last_object_clicked" in map_output and map_output["last_object_clicked"]:
        st.session_state["ultimo_clique_mapa"] = map_output["last_object_clicked"]

    # =================================================================
    # 5. BASE DE DADOS ESTRUTURADA INFERIOR
    # =================================================================
    st.markdown("---")
    st.markdown("### Base Cadastral do Parque Industrial")
    st.dataframe(
        df_unidades_mapa[['nome', 'uf', 'tipo', 'cnpj', 'endereco']].rename(columns={
            'nome': 'Unidade Operacional',
            'uf': 'UF',
            'tipo': 'Classificação',
            'cnpj': 'CNPJ',
            'endereco': 'Endereço Registrado'
        }), 
        use_container_width=True, 
        hide_index=True
    )


# ---------------------------------------------------------
# ABA 1: AUDITORIA DE OBJETOS E INVESTIGAÇÃO QUALITATIVA
# ---------------------------------------------------------
with tab1:
    c1, c2 = st.columns([1.2, 1], gap="large")
    
    with c1:
        st.markdown("### Frequência por Objeto de Autuação")
        df_obj = df_unicos['Objeto Identificado'].value_counts().reset_index()
        df_obj.columns = ['Objeto', 'Quantidade']
        
        fig_obj = px.bar(df_obj, y='Objeto', x='Quantidade', orientation='h', text_auto=True, color_discrete_sequence=[COR_PRIMARIA])
        fig_obj.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="", margin=dict(l=0, r=0, t=10, b=0), height=400)
        st.plotly_chart(fig_obj, use_container_width=True)
        
    with c2:
        st.markdown("### Investigação Qualitativa Individual")
        st.write("Selecione a categoria para investigar a redação técnica dos fiscais:")
        
        lista_opcoes_objetos = ['Todos'] + df_obj['Objeto'].tolist()
        objeto_alvo = st.selectbox("", lista_opcoes_objetos, label_visibility="collapsed")
        
        if objeto_alvo == 'Todos':
            df_focado = df_unicos
            titulo_caixa_kpi = "Total Geral Mapeado"
        else:
            df_focado = df_unicos[df_unicos['Objeto Identificado'] == objeto_alvo]
            titulo_caixa_kpi = "Total Mapeado na Categoria"
        
        st.markdown(f"""
        <div style="background-color: {COR_PRIMARIA}; padding: 15px 20px; border-radius: 6px; margin-bottom: 20px; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; opacity: 0.9;">{titulo_caixa_kpi}</div>
            <div style="font-size: 22px; font-weight: 700; margin-top: 2px;">{len(df_focado)} Auto(s) de Infração</div>
        </div>
        """, unsafe_allow_html=True)
        
        for _, row in df_focado.iterrows():
            with st.expander(f"A.I: {row['Nº A.I.']} | UF: {row['UF_Clean']}"):
                st.markdown(f"**Processo SEI:** `{row['Nº Processo']}`")
                st.markdown(f"**Valor da Multa:** R$ {row['Valor Multa']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.markdown(f"**Natureza do Enquadramento:** {row['Tipo Infração']}")
                st.markdown(f"**Sanções Aplicadas:**")
                st.error(row['Sanções Aplicadas'] if row['Sanções Aplicadas'] != '-' else 'Nenhuma Sanção Física Listada')
                st.markdown("**Descrição Técnica (Fato Gerador):**")
                st.info(row['Descrição das Autuações'])

# ---------------------------------------------------------
# ABA 2: ANÁLISE REGIONAL
# ---------------------------------------------------------
with tab2:
    df_uf_unique = df.drop_duplicates(subset=['UF_Filtro', 'Nº A.I.'])
    df_uf = df_uf_unique.groupby('UF_Filtro').agg({'Valor Multa': 'sum', 'Nº A.I.': 'nunique'}).reset_index()
    df_uf = df_uf.sort_values(by='Valor Multa', ascending=False)
    
    c_reg1, c_reg2 = st.columns(2, gap="large")
    with c_reg1:
        st.markdown("### Concentração de Passivo Financeiro (R$)")
        fig_uf_val = px.bar(df_uf, x='UF_Filtro', y='Valor Multa', text_auto='.2s', color_discrete_sequence=[COR_PRIMARIA])
        fig_uf_val.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_uf_val, use_container_width=True)
        
    with c_reg2:
        st.markdown("### Densidade de Autos de Infração (Volume)")
        fig_uf_qtd = px.bar(df_uf, x='UF_Filtro', y='Nº A.I.', text_auto=True, color_discrete_sequence=["#475569"])
        fig_uf_qtd.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_uf_qtd, use_container_width=True)

# ---------------------------------------------------------
# ABA 3: TIPOLOGIA E SANÇÕES
# ---------------------------------------------------------
with tab3:
    c_tip1, c_tip2 = st.columns(2, gap="large")
    
    with c_tip1:
        st.markdown("### Enquadramento Técnico")
        tipos_df = df_unicos['Tipo Infração'].value_counts().reset_index()
        tipos_df.columns = ['Natureza da Infração', 'Contagem']
        fig_tipo = px.pie(tipos_df, values='Contagem', names='Natureza da Infração', hole=0.5, color_discrete_sequence=[COR_PRIMARIA, COR_DOURADO, COR_SECUNDARIA, "#94a3b8"])
        fig_tipo.update_traces(textposition='inside', textinfo='percent+label')
        fig_tipo.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_tipo, use_container_width=True)
        
    with c_tip2:
        st.markdown("### Medidas Restritivas Diretas")
        sancoes_data = {
            'Apreensão de Bens': df_unicos['Apreensão'].sum(),
            'Fiel Depositário': df_unicos['Depósito'].sum(),
            'Suspensão Operacional': df_unicos['Suspensão'].sum(),
            'Embargo de Área': df_unicos['Embargo/Interdição'].sum()
        }
        df_sanc = pd.DataFrame(list(sancoes_data.items()), columns=['Medida', 'Total'])
        df_sanc = df_sanc[df_sanc['Total'] > 0]
        
        fig_sanc = px.bar(df_sanc, x='Total', y='Medida', orientation='h', text_auto=True, color_discrete_sequence=[COR_SECUNDARIA])
        fig_sanc.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'}, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_sanc, use_container_width=True)

# ---------------------------------------------------------
# ABA 4: PESQUISA PROFUNDA (FILTROS)
# ---------------------------------------------------------
with tab4:
    st.markdown("### Investigação Analítica")
    st.write("Digite qualquer termo (Processo, CNPJ, Embarcação, Espécie) para varrer as descrições dos autos:")
    
    busca_livre_aba4 = st.text_input("", placeholder="🔍 Buscar termo específico (Aba)...", label_visibility="collapsed", key="busca_aba4")
    
    df_pesquisa = df_unicos.copy()
    if busca_livre_aba4:
        mask = df_pesquisa.astype(str).apply(lambda x: x.str.contains(busca_livre_aba4, case=False)).any(axis=1)
        df_pesquisa = df_pesquisa[mask]
        
    st.markdown(f"**Resultados Encontrados:** {len(df_pesquisa)} auto(s) de infração.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    for _, row in df_pesquisa.iterrows():
        with st.expander(f"Processo SEI: {row['Nº Processo']}  |  Auto de Infração: {row['Nº A.I.']}  |  UF: {row['UF_Clean']}"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"**Valor da Multa:** R$ {row['Valor Multa']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.markdown(f"**Natureza:** {row['Tipo Infração']}")
                st.markdown(f"**Objeto Classificado:** {row['Objeto Identificado']}")
                st.markdown(f"**Medida Aplicada:**")
                st.error(row['Sanções Aplicadas'] if row['Sanções Aplicadas'] != '-' else 'Nenhuma Sanção Física Listada')
            with c2:
                st.markdown("**Descrição Técnica Lavrada pelo Fiscal:**")
                st.info(row['Descrição das Autuações'])

# ---------------------------------------------------------
# ABA 5: BASE DE DADOS CONSOLIDADA
# ---------------------------------------------------------
with tab5:
    st.markdown("### Matriz de Dados (Pronta para Auditoria)")
    colunas_finais = ['Nº Processo', 'Nº A.I.', 'Data Infração', 'UF_Clean', 'Objeto Identificado', 'Tipo Infração', 'Valor Multa', 'Descrição das Autuações']
    df_export = df_unicos[colunas_finais].rename(columns={'UF_Clean': 'UF'})
    
    st.dataframe(df_export, use_container_width=True, hide_index=True)
    
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Exportar Matriz Analítica (CSV)", data=csv, file_name='Auditoria_IBAMA.csv', mime='text/csv')


# ==========================================
# ABA 6: MITIGAÇÃO OPERACIONAL E CAMPO
# ==========================================
with tab6:
    st.markdown(f"""
    renderizar_leitor_nativo("aba6")
    
    if st.session_state['leitor_ativo'] is None:
        if st.button("👁️ ABRIR GUIA DO MOTORISTA (3D)"):
            st.session_state['leitor_ativo'] = "DOC-01: Guia do Motorista"
            st.rerun()
    
    <div class='painel-3d'>
        <p style="margin: 0 0 5px 0; color: {COR_DOURADO}; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px;">Linha de Frente • Portos e Rodovias</p>
        <h2 style="margin: 0 0 10px 0; color: {COR_SECUNDARIA}; font-size: 1.6rem; font-weight: 800; text-transform: uppercase;">
            Plano de Mitigação: Operacional & Campo
        </h2>
        <p style="margin: 0; color: #475569; font-size: 11pt; text-align: justify; line-height: 1.6;">
            Esta aba consolida as <b>Barreiras Físicas de Compliance</b>. Aqui estão ancorados os protocolos interativos desenvolvidos para as docas, balanças e frotas de captura, com o objetivo de anular autuações por petrechos proibidos e tamanhos ilícitos.
        </p>
        </div>
        <p style="margin: 0 0 5px 0; color: {COR_PRIMARIA}; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px;">Clique em um documento para abrir a versão digital ou fazer o download da versão oficial:</p>
        
    """, unsafe_allow_html=True)
    
    # 1. Chama a Função do Motor 3D (Se houver algo selecionado, a interface escurece a tela)
    renderizar_leitor_nativo("aba6")
    
    # 2. Se nenhum documento estiver aberto no Leitor 3D, mostramos o Menu de Botões
    if st.session_state.get('leitor_ativo') is None:
        
        col_op1, col_op2 = st.columns(2)
        
        with col_op1:
            with st.expander("🚚 DOC-01: Guia do Motorista", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Conduta em barreiras fiscais e exigência de balança INMETRO.</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc1", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-01: Guia do Motorista"
                    st.rerun()
                    
            with st.expander("🦞 DOC-02: POP Triagem Lagosta", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Tolerância zero para tamanhos mínimos e fêmeas ovadas.</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc2", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-02: Triagem de Lagosta"
                    st.rerun()

        with col_op2:
            with st.expander("🐟 DOC-04: Guia VMS Pargo", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Zonas de exclusão costeira e monitoramento PREPS.</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc4", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-04: Guia VMS Pargo"
                    st.rerun()
                    
            with st.expander("🛑 DOC-07: Cartilha Petrechos", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Identificação visual de capturas ilegais (Rede de Caçoeira).</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc7", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-07: Cartilha de Petrechos"
                    st.rerun()


# ==========================================
# ABA 7: GOVERNANÇA & JURÍDICO
# ==========================================
with tab7:
    st.markdown(f"""
    <div class='painel-3d' style='border-left-color: {COR_DOURADO};'>
        <p style="margin: 0 0 5px 0; color: {COR_PRIMARIA}; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px;">Backoffice • Sistemas • Tribunais</p>
        <h2 style="margin: 0 0 10px 0; color: {COR_SECUNDARIA}; font-size: 1.6rem; font-weight: 800; text-transform: uppercase;">
            Governança Integrada & Inteligência Jurídica
        </h2>
        <p style="margin: 0; color: #475569; font-size: 11pt; text-align: justify; line-height: 1.6;">
            Este módulo concentra as <b>Barreiras Documentais e de Sistema</b>. Aqui estão hospedados os fluxogramas de Due Diligence para bloquear infrações na fonte, regras aduaneiras e o nosso arsenal de defesa (Teses e SLA de Urgência).
        </p>
        </div>
        <p style="margin: 0 0 5px 0; color: {COR_PRIMARIA}; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px;">Clique aqui para ver o Backoffice e Inteligência Ambiental para blindagem documental e contencioso administrativo</p>     

    """, unsafe_allow_html=True)
    
    # 1. Chama a Função do Motor 3D para a Aba 7
    renderizar_leitor_nativo("aba7")
    
    # 2. Mostra os botões de menu apenas se o leitor estiver fechado
    if st.session_state.get('leitor_ativo') is None:
        
        col_jur1, col_jur2 = st.columns(2)
        
        with col_jur1:
            with st.expander("❄️ DOC-03: Manual do Defeso", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Trava de ERP, inventário cego e declaração oficial de estoques.</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc3", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-03: Manual do Defeso"
                    st.rerun()
                    
            with st.expander("⚖️ DOC-05: Teses Defensivas", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Matriz de respostas rápidas (SLA 48h) e conversão via NUCAM.</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc5", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-05: Teses Defensivas"
                    st.rerun()
                    
            with st.expander("📊 DOC-09: Resumo Executivo", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Relatório de Governança para Board e Investidores.</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc9", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-09: Resumo Executivo"
                    st.rerun()

        with col_jur2:
            with st.expander("🔍 DOC-06: Due Diligence RGP", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Triagem rigorosa de fornecedores e armadores embargados.</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc6", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-06: Due Diligence RGP"
                    st.rerun()
                    
            with st.expander("🚢 DOC-08: Checklist Aduaneiro", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Liberação aduaneira (Sinal Verde) e controle de NCMs/LPCO.</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc8", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-08: Checklist Exportação"
                    st.rerun()
                    
            with st.expander("📘 DOC-10: E-book Institucional", expanded=True):
                st.markdown("<p style='font-size: 13px; color: #475569;'><b>Foco:</b> Apresentação da cultura ESG e Compliance da Prime Seafood.</p>", unsafe_allow_html=True)
                if st.button("👁️ ABRIR INFOGRÁFICO VIVO", key="btn_abrir_doc10", use_container_width=True):
                    st.session_state['leitor_ativo'] = "DOC-10: E-book Institucional"
                    st.rerun()
