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

tab_mapa, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Mapa Operacional", 
    "Auditoria de Objetos", 
    "Análise Regional", 
    "Tipologia e Sanções", 
    "Pesquisa Profunda", 
    "Base Consolidada",
    "Plano de Mitigação"
])

# CORREÇÃO: Deduplicar exclusivamente pela chave única do Auto de Infração
df_unicos = df.drop_duplicates(subset=['Nº A.I.'])

# =====================================================================
# 2. BLOCO DO MAPA AQUI 
# =====================================================================

with tab_mapa:
    st.markdown("## Mapeamento Operacional: Litoral Norte e Nordeste")
    st.markdown("Visão espacial interativa de alta resolução (Satélite Google) das unidades próprias e rede de prestadores de serviço terceirizados.")
    
    # 1. Base de dados com informações descritivas detalhadas para os Popups
    dados_mapa = [
        {"Nome": "Matriz / Escritório Central", "Cidade": "Fortaleza - CE", "Lat": -3.7172, "Lon": -38.5433, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "star", "Status": "Ativa / Regular", "Descricao": "Sede administrativa e coordenação jurídica/operacional da rede."},
        {"Nome": "Filial Indústria Icapuí", "Cidade": "Icapuí - CE", "Lat": -4.7119, "Lon": -37.3544, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "industry", "Status": "Alerta: Histórico de Defeso (Lagosta)", "Descricao": "Unidade industrial focada em processamento. Requer auditoria rigorosa de estoque no defeso."},
        {"Nome": "Filial Indústria Acaraú", "Cidade": "Acaraú - CE", "Lat": -2.8853, "Lon": -40.1200, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "industry", "Status": "Ativa / Regular", "Descricao": "Planta de processamento e congelamento de pescado costeiro."},
        {"Nome": "Filial Costeira São Gonçalo", "Cidade": "S. G. do Amarante - CE", "Lat": -3.6064, "Lon": -38.9717, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "anchor", "Status": "Atenção: Pesca (Pargo)", "Descricao": "Ponto de apoio costeiro. Monitorar relatórios de rastreamento de profundidade VMS."},
        {"Nome": "Filial Bragança", "Cidade": "Bragança - PA", "Lat": -1.0536, "Lon": -46.7656, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "anchor", "Status": "Histórico: Pesca < 50m (Pargo)", "Descricao": "Unidade estratégica no Pará. Atenção redobrada com autuações de frotas parceiras no pargo."},
        {"Nome": "Filial Belém", "Cidade": "Belém - PA", "Lat": -1.4558, "Lon": -48.5039, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "briefcase", "Status": "Atenção: Controle Aduaneiro", "Descricao": "Apoio logístico e aduaneiro para exportações saindo do Norte do país."},
        {"Nome": "Filial Luís Correia", "Cidade": "Luís Correia - PI", "Lat": -2.8856, "Lon": -41.6681, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "asterisk", "Status": "Câmaras Frias / Estoque", "Descricao": "Centro de armazenamento frigorífico. Risco focado na declaração de estoques de lagosta."},
        {"Nome": "Filial Touros", "Cidade": "Touros - RN", "Lat": -5.1989, "Lon": -35.4608, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "anchor", "Status": "Atenção: RGP de Filial", "Descricao": "Unidade costeira de recepção. Necessário checagem mensal de vigência do RGP."},
        {"Nome": "Filial Baía Formosa", "Cidade": "Baía Formosa - RN", "Lat": -6.3719, "Lon": -35.0053, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "anchor", "Status": "Histórico: Petrecho Proibido", "Descricao": "Recepção de lagosta. Foco em barrar entrada de pescado capturado por rede de caçoeira."},
        {"Nome": "Filial Alhandra", "Cidade": "Alhandra - PB", "Lat": -7.4328, "Lon": -34.9125, "Tipo": "Base Própria (Prime)", "Cor": "red", "Ícone": "road", "Status": "Ativa / Transporte", "Descricao": "Hub de apoio rodoviário e transporte de cargas interativado."},
        {"Nome": "Soene Pescados", "Cidade": "Santana / Macapá - AP", "Lat": -0.0583, "Lon": -51.1717, "Tipo": "Prestador de Serviço / Terceira", "Cor": "orange", "Ícone": "globe", "Status": "Apoio Logístico Extremo Norte", "Descricao": "Parceiro de serviços e apoio operacional logístico no extremo Norte (Amapá)."},
        {"Nome": "Carapitanga Pescados", "Cidade": "Goiana - PE", "Lat": -7.5617, "Lon": -34.9011, "Tipo": "Prestador de Serviço / Terceira", "Cor": "orange", "Ícone": "warning-sign", "Status": "Alerta: Alvo de Fiscalização Recente", "Descricao": "Parceiro de maricultura/processamento em PE. Requer due diligence nas NFs de transação."},
        {"Nome": "Cabel Frigorífico", "Cidade": "Salvador / Litoral - BA", "Lat": -12.9714, "Lon": -38.5014, "Tipo": "Prestador de Serviço / Terceira", "Cor": "orange", "Ícone": "globe", "Status": "Apoio Litoral Sul / Bahia", "Descricao": "Prestador de serviços de armazenagem e apoio logístico no litoral baiano."}
    ]
    
    df_mapa = pd.DataFrame(dados_mapa)
    
    # 2. Filtro de exibição por categoria
    tipo_filtro = st.radio("Filtrar visualização no mapa:", ["Todos os Pontos", "Apenas Bases Próprias (Prime)", "Apenas Terceirizados / Prestadores"], horizontal=True)
    
    if tipo_filtro == "Apenas Bases Próprias (Prime)":
        df_exibicao = df_mapa[df_mapa['Tipo'] == "Base Própria (Prime)"]
    elif tipo_filtro == "Apenas Terceirizados / Prestadores":
        df_exibicao = df_mapa[df_mapa['Tipo'] == "Prestador de Serviço / Terceira"]
    else:
        df_exibicao = df_mapa

    # 3. Criação do Mapa Base focado no Nordeste/Norte
    mapa = folium.Map(location=[-4.5, -40.0], zoom_start=5, tiles=None, control_scale=True)

    # Adicionando a camada nativa do Google Satellite Híbrido (Satélite + Nomes de Cidades/Estradas)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Maps / Satellite Hybrid',
        name='Google Satélite Híbrido',
        overlay=False,
        control=True
    ).add_to(mapa)

    # 4. Inserção dos Marcadores MAIORES e Ultra Descritivos
    for idx, row in df_exibicao.iterrows():
        html_popup = f"""
        <div style="font-family: Arial, sans-serif; width: 260px; padding: 5px;">
            <h4 style="margin: 0 0 5px 0; color: #333; border-bottom: 2px solid {'#7c1617' if row['Cor']=='red' else '#d97706'}; padding-bottom: 3px;">
                {row['Nome']}
            </h4>
            <p style="margin: 3px 0; font-size: 12px;"><b>📍 Cidade:</b> {row['Cidade']}</p>
            <p style="margin: 3px 0; font-size: 12px;"><b>🏢 Categoria:</b> <span style="color: {'#7c1617' if row['Cor']=='red' else '#d97706'}; font-weight: bold;">{row['Tipo']}</span></p>
            <p style="margin: 6px 0 3px 0; font-size: 12px; background-color: #f8fafc; padding: 4px; border-left: 3px solid #3b82f6;"><b>🚦 Status:</b> {row['Status']}</p>
            <p style="margin: 5px 0 0 0; font-size: 11px; color: #475569; font-style: italic;">"{row['Descricao']}"</p>
        </div>
        """
        
        folium.Marker(
            location=[row['Lat'], row['Lon']],
            popup=folium.Popup(html_popup, max_width=300),
            tooltip=f"📌 {row['Nome']} ({row['Cidade']}) - Clique para detalhes",
            icon=folium.Icon(color=row['Cor'], icon=row['Ícone'], prefix='glyphicon')
        ).add_to(mapa)
        
        folium.CircleMarker(
            location=[row['Lat'], row['Lon']],
            radius=14,
            color='#7c1617' if row['Cor']=='red' else '#d97706',
            fill=True,
            fill_color='#ff0000' if row['Cor']=='red' else '#ffae00',
            fill_opacity=0.3,
            weight=2
        ).add_to(mapa)

    # 5. Renderização do mapa dentro do Streamlit
    st_folium(mapa, width="100%", height=550)
    
    # 6. Tabela inferior para consulta rápida e auditoria
    st.markdown("### 📋 Detalhamento das Unidades e Prestadores Mapeados")
    st.dataframe(
        df_exibicao[['Nome', 'Cidade', 'Tipo', 'Status', 'Descricao']], 
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
# ABA 6: PLANO DE MITIGAÇÃO (PREVENÇÃO)
# ==========================================
with tab6:
    # 1. APRESENTAÇÃO EXECUTIVA (A Finalidade do Plano para a Diretoria)
    st.markdown(f"""
    <div style="background-color: #ffffff; padding: 25px 30px; border-left: 5px solid {COR_PRIMARIA}; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); margin-bottom: 25px;">
        <p style="margin: 0 0 4px 0; color: {COR_DOURADO}; font-size: 9.5pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
            Carvalho & Fadul Advocacia | Governança & Compliance Ambiental
        </p>
        <h2 style="margin: 0 0 10px 0; color: {COR_SECUNDARIA}; font-size: 1.5rem; font-weight: 700; text-transform: uppercase; letter-spacing: -0.5px;">
            Plano Diretor de Gerenciamento de Riscos e Mitigação
        </h2>
        <p style="margin: 0; color: #334155; font-size: 10.5pt; text-align: justify; line-height: 1.6;">
            Este painel representa a síntese estratégica da auditoria do contencioso administrativo do IBAMA, convertendo o histórico 
            de autuações em um <b>sistema ativo de prevenção de passivos e blindagem jurídica</b> para a Prime Seafood LTDA. 
            O plano está estruturado em <b>3 Pilares de Comando</b> (Operacional, Administrativo e Jurídico), cobrindo integralmente as 
            vulnerabilidades da empresa. Clique em qualquer um dos cards abaixo para expandir o enquadramento legal, auditar as regras 
            de compliance obrigatórias e fazer o download dos <b>Guias Operacionais e Manuais</b> diagramados para as filiais.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2. BARRA DE INDICADORES RÁPIDOS DO PLANO (Visual PowerBI)
    c_ind1, c_ind2, c_ind3 = st.columns(3, gap="medium")
    with c_ind1:
        st.markdown(f"<div style='background:#f8fafc; padding:12px; border-radius:4px; border:1px solid #e2e8f0; text-align:center;'><span style='font-size:11px; color:#64748b; font-weight:600; text-transform:uppercase;'>Frentes de Governança</span><br><b style='font-size:18px; color:{COR_PRIMARIA};'>3 Pilares Estratégicos</b></div>", unsafe_allow_html=True)
    with c_ind2:
        st.markdown(f"<div style='background:#f8fafc; padding:12px; border-radius:4px; border:1px solid #e2e8f0; text-align:center;'><span style='font-size:11px; color:#64748b; font-weight:600; text-transform:uppercase;'>Manuais Prioritários (Fase 1)</span><br><b style='font-size:18px; color:{COR_DOURADO};'>4 Guias Executivos</b></div>", unsafe_allow_html=True)
    with c_ind3:
        st.markdown(f"<div style='background:#f8fafc; padding:12px; border-radius:4px; border:1px solid #e2e8f0; text-align:center;'><span style='font-size:11px; color:#64748b; font-weight:600; text-transform:uppercase;'>Status de Conformidade</span><br><b style='font-size:18px; color:#15803d;'>Protocolos Ativos</b></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. MATRIZ DE RISCOS INTERATIVA (RESTAURANDO OS 3 PILARES COMPLETOS)
    col_op, col_adm, col_jur = st.columns(3, gap="large")

    # =================================================================
    # PILAR 1: GESTÃO OPERACIONAL (CAIS, FROTA E CAPTURA)
    # =================================================================
    with col_op:
        st.markdown(f"<h3 style='color: {COR_PRIMARIA}; font-size: 13pt; border-bottom: 2px solid {COR_PRIMARIA}; padding-bottom: 6px; margin-bottom: 12px;'>⚙️ 1. Pilar Operacional & Campo</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px; color:#64748b; margin-bottom:15px;'>Mitigação de riscos físicos em biometria, embarque e controle de mar.</p>", unsafe_allow_html=True)

        # CARD 1.1: TRIAGEM DE LAGOSTA (GUIA CANVA 1)
        with st.expander("🦞 Triagem e Biometria de Lagosta no Cais", expanded=False):
            st.markdown("""
            **Vulnerabilidade Mapeada:** Recepção de lagostas juvenis (abaixo do tamanho legal) ou capturadas por petrechos ilícitos (Rede de Caçoeira), gerando multas por quilograma e embargo de fábrica.
            
            **Enquadramento Legal:** Portaria Interministerial MPA/MMA nº 138/2014 e Lei nº 9.605/98. Tolerância zero para Vermelha < 13cm (cauda) e Verde < 11cm (cauda).
            
            **Protocolo de Mitigação (Diretriz Prime):**
            * Medição compulsória com gabarito em amostragem de 10% da descarga.
            * Veto de compra para lotes com marcas de emalhar/estrangulamento.
            * **Regra dos 70% Vivas:** Expedição rodoviária apenas para lotes com vitalidade ≥ 70%, prevenindo mortalidade no trânsito.
            """)
            st.markdown("---")
            st.markdown("##### 📥 Material Oficial (Fase 1 - Canva)")
            st.download_button(
                label="📄 Baixar POP-001: Triagem de Lagosta (PDF)",
                data=b"Placeholder_POP_Lagosta",
                file_name="POP_001_Triagem_Biometria_Lagosta.pdf",
                mime="application/pdf",
                key="dl_op_lagosta",
                use_container_width=True
            )

        # CARD 1.2: VMS E PARGO (GUIA CANVA 2)
        with st.expander("🐟 Monitoramento Digital VMS e Frota (Pargo)", expanded=False):
            st.markdown("""
            **Vulnerabilidade Mapeada:** Incursão de embarcações parceiras em zonas de exclusão costeira (profundidade < 50 metros) ou interrupção do sinal de rastreamento por satélite.
            
            **Enquadramento Legal:** Instruções Normativas do Plano de Gestão do Pargo (MAPA/IBAMA) e regras do Sistema PREPS/VMS.
            
            **Protocolo de Mitigação (Diretriz Prime):**
            * Auditoria diária de telemetria das frotas homologadas antes da recepção do pescado.
            * Alarme de aproximação de zonas proibidas georreferenciado pela matriz.
            * Obrigatoriedade de preenchimento milimétrico do Mapa de Bordo.
            """)
            st.markdown("---")
            st.markdown("##### 📥 Material Oficial (Fase 1 - Canva)")
            st.download_button(
                label="📄 Baixar Guia VMS e Navegação (PDF)",
                data=b"Placeholder_Guia_VMS",
                file_name="Guia_VMS_Controle_Frota_Pargo.pdf",
                mime="application/pdf",
                key="dl_op_vms",
                use_container_width=True
            )

    # =================================================================
    # PILAR 2: COMPLIANCE ADMINISTRATIVO (ESTOQUES, RGP E ADUANA)
    # =================================================================
    with col_adm:
        st.markdown(f"<h3 style='color: {COR_SECUNDARIA}; font-size: 13pt; border-bottom: 2px solid {COR_SECUNDARIA}; padding-bottom: 6px; margin-bottom: 12px;'>🏢 2. Pilar Administrativo</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px; color:#64748b; margin-bottom:15px;'>Trava sistêmica, conformidade documental e auditoria aduaneira.</p>", unsafe_allow_html=True)

        # CARD 2.1: DEFESO E ESTOQUES (GUIA CANVA 3)
        with st.expander("❄️ Declaração de Câmaras Frias no Defeso", expanded=False):
            st.markdown("""
            **Vulnerabilidade Mapeada:** Apreensão integral de estoques congelados por atraso na declaração ou divergência entre o volume físico e o sistema oficial do MAPA/IBAMA no início do defeso.
            
            **Enquadramento Legal:** Art. 35 do Decreto nº 6.514/08 e normas anuais de defeso (declaração obrigatória em até 7 dias após o fechamento da pesca).
            
            **Protocolo de Mitigação (Diretriz Prime):**
            * Trava no sistema ERP 5 dias antes do prazo final, impedindo novas entradas.
            * Inventário físico obrigatório auditado por dois responsáveis.
            * Afixação pública do recibo de declaração na porta da câmara frigorífica.
            """)
            st.markdown("---")
            st.markdown("##### 📥 Material Oficial (Fase 1 - Canva)")
            st.download_button(
                label="📄 Baixar Manual do Defeso e Estoques (PDF)",
                data=b"Placeholder_Manual_Defeso",
                file_name="Manual_Compliance_Defeso_Estoque.pdf",
                mime="application/pdf",
                key="dl_adm_defeso",
                use_container_width=True
            )

        # CARD 2.2: DUE DILIGENCE DE FORNECEDORES (RESTAURADO!)
        with st.expander("🔍 Due Diligence de Fornecedores e RGP", expanded=False):
            st.markdown("""
            **Vulnerabilidade Mapeada:** Aquisição de pescado de embarcações com Registro Geral da Atividade Pesqueira (RGP) suspenso, cancelado ou de armadores listados em embargos públicos do IBAMA.
            
            **Enquadramento Legal:** Lei nº 9.605/98 (Responsabilidade solidária e receptação de produto de infração ambiental).
            
            **Protocolo de Mitigação (Diretriz Prime):**
            * Consulta mensal automatizada da vigência do RGP das embarcações parceiras.
            * Bloqueio no sistema fiscal para emissão de Nota Fiscal de Entrada de fornecedores embargados ou irregulares.
            * Exigência de certidão negativa de débitos ambientais na homologação de frotas.
            """)
            st.markdown("---")
            st.markdown("##### 📥 Ancoragem de Procedimento Interno")
            st.download_button(
                label="📄 Baixar Checklist de Compra Segura (PDF)",
                data=b"Placeholder_Due_Diligence",
                file_name="Procedimento_Due_Diligence_RGP.pdf",
                mime="application/pdf",
                key="dl_adm_rgp",
                use_container_width=True
            )

    # =================================================================
    # PILAR 3: INTELIGÊNCIA JURÍDICA (TRANSPORTE E DEFESA)
    # =================================================================
    with col_jur:
        st.markdown(f"<h3 style='color: {COR_DOURADO}; font-size: 13pt; border-bottom: 2px solid {COR_DOURADO}; padding-bottom: 6px; margin-bottom: 12px;'>⚖️ 3. Pilar Jurídico & Resposta</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px; color:#64748b; margin-bottom:15px;'>Blindagem rodoviária, gestão de crise e contencioso administrativo.</p>", unsafe_allow_html=True)

        # CARD 3.1: ABORDAGEM FISCAL E TRANSPORTE (GUIA CANVA 4 - O QUE FIZEMOS!)
        with st.expander("🛡️ Protocolo de Abordagem Rodoviária e Fiscais", expanded=False):
            st.markdown("""
            **Vulnerabilidade Mapeada:** Autuações por divergência de peso estimada visualmente ("olhômetro") em barreiras e arbitramento de multas por mortalidade incidental de lagosta viva no trânsito.
            
            **Enquadramento Legal:** Instruções Normativas IBAMA/PRF e legislação metrológica do INMETRO.
            
            **Protocolo de Mitigação (Diretriz Prime):**
            * Proibição de rompimento de lacres sem a presença do agente fiscal.
            * Exigência inalienável de pesagem em balança rodoviária aferida pelo INMETRO.
            * **Assinatura com Ressalva:** Uso obrigatório de minutas de ressalva técnica no campo de observações do Auto de Infração no ato da lavratura.
            """)
            st.markdown("---")
            st.markdown("##### 📥 Material Oficial (Fase 1 - Canva)")
            st.download_button(
                label="📄 Baixar Guia de Bolso do Motorista (PDF)",
                data=b"Placeholder_Guia_Bolso_Motorista",
                file_name="Guia_Bolso_Motorista_Prime_Seafood.pdf",
                mime="application/pdf",
                key="dl_jur_guia_bolso",
                use_container_width=True
            )

        # CARD 3.2: TESES DE DEFESA E SLA 48H (RESTAURADO!)
        with st.expander("⏳ SLA 48h e Matriz de Teses Defensivas", expanded=False):
            st.markdown("""
            **Vulnerabilidade Mapeada:** Perda de prazos defensivos curtos (20 dias) e risco de doação sumária de pescado apreendido ou leilão de veículos frigoríficos por falta de medida judicial de urgência.
            
            **Enquadramento Legal:** Processo Administrativo Federal (Lei nº 9.784/99) e Instrução Normativa IBAMA nº 19/2023.
            
            **Protocolo de Mitigação (Diretriz Prime):**
            * **SLA 48 Horas:** Janela crítica pós-autuação para acionamento fotográfico e protocolo do Pedido de Fiel Depositário pela Carvalho & Fadul Advocacia.
            * Aplicação imediata de teses homologadas (Nulidade por falha de intimação no SEI e Adquirente de Boa-Fé).
            """)
            st.markdown("---")
            st.markdown("##### 📥 Ancoragem de Contencioso")
            st.download_button(
                label="📄 Baixar Matriz de Teses Homologadas (PDF)",
                data=b"Placeholder_Teses_Defesa",
                file_name="Matriz_Teses_Defensivas_IBAMA.pdf",
                mime="application/pdf",
                key="dl_jur_teses",
                use_container_width=True
            )
