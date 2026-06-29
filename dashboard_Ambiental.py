import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import base64
import re

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS CORPORATIVO
# ==========================================
st.set_page_config(page_title="Gestão de Riscos e Processos IBAMA", layout="wide", initial_sidebar_state="expanded")

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
    
    .stApp {{
        background-color: {COR_FUNDO_APP};
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
    elif 'atum' in desc or 'demersal' in desc: return 'Atuns e Demersais'
    elif 'garoupa' in desc or 'badejo' in desc: return 'Garoupa e Badejo (Ameaçados)'
    else: return 'Administrativo / Diversos'

ESTADOS_VALIDOS = {'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'}

def limpar_e_separar_ufs(val):
    val_str = str(val).upper()
    encontrados = []
    for token in re.split(r'[^A-Z]', val_str):
        if token in ESTADOS_VALIDOS and token not in encontrados:
            encontrados.append(token)
    return encontrados if encontrados else ['N/D']

@st.cache_data(ttl=600)
def carregar_dados():
    # Link direto da sua planilha publicada como CSV
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmM6tv0bqBxxx4Rc9pAYGPDXDAfWCV3fnv6mZAwoAYfaXBn_jhVNadrlsALWsyFvSYai-oD7QHk_VD/pub?output=csv"
    df = pd.read_csv(url)
    
    # MOTOR DE LIMPEZA E DEDUPLICAÇÃO (MANTIDO)
    colunas_chave = ['Nº Processo', 'Tipo Infração', 'Nº A.I.', 'Data Infração']
    
    df['Valor Multa'] = pd.to_numeric(df['Valor Multa'], errors='coerce').fillna(0)
    df['Objeto Identificado'] = df['Descrição das Autuações'].apply(classificar_objeto)
    df['Data Infração'] = pd.to_datetime(df['Data Infração'], errors='coerce')
    df['Descrição das Autuações'] = df['Descrição das Autuações'].fillna('-')
    df['Sanções Aplicadas'] = df['Sanções Aplicadas'].fillna('-')
    df['Data Infração'] = pd.to_datetime(df['Data Infração'], errors='coerce')
    
    df['Objeto Identificado'] = df['Descrição das Autuações'].apply(classificar_objeto)
    
    df['Apreensão'] = df['Sanções Aplicadas'].str.contains('apreensão', case=False)
    df['Depósito'] = df['Sanções Aplicadas'].str.contains('depósito', case=False)
    df['Embargo/Interdição'] = df['Sanções Aplicadas'].str.contains('embargo|interdição', case=False)
    df['Suspensão'] = df['Sanções Aplicadas'].str.contains('suspensão', case=False)
    
    df['UF_Lista'] = df['UF'].apply(limpar_e_separar_ufs)
    df['UF_Clean'] = df['UF_Lista'].apply(lambda x: ' / '.join(x))
    
    return df

def renderizar_kpis(df_filtrado):
    df_unicos = df_filtrado.drop_duplicates(subset=['Nº Processo', 'Nº A.I.'])
    
    valor_total = df_unicos['Valor Multa'].sum()
    valor_formatado = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    qtd_apreensoes = df_unicos['Apreensão'].sum() + df_unicos['Depósito'].sum()
    
    html = f"""
    <div style="display: flex; gap: 20px; margin-bottom: 25px; margin-top: 10px;">
        <div style="flex: 1; background: #fff; padding: 22px; border-radius: 6px; border-left: 4px solid {COR_PRIMARIA}; box-shadow: 0 2px 5px rgba(0,0,0,0.04);">
            <div style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Autos de Infração Auditados</div>
            <div style="font-size: 30px; color: {COR_SECUNDARIA}; font-weight: 700; margin-top: 4px;">{len(df_unicos)}</div>
        </div>
        <div style="flex: 1; background: #fff; padding: 22px; border-radius: 6px; border-left: 4px solid {COR_DOURADO}; box-shadow: 0 2px 5px rgba(0,0,0,0.04);">
            <div style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Passivo Financeiro Consolidado</div>
            <div style="font-size: 30px; color: {COR_SECUNDARIA}; font-weight: 700; margin-top: 4px; white-space: nowrap;">{valor_formatado}</div>
        </div>
        <div style="flex: 1; background: #fff; padding: 22px; border-radius: 6px; border-left: 4px solid #475569; box-shadow: 0 2px 5px rgba(0,0,0,0.04);">
            <div style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Medidas Acautelatórias (Físicas)</div>
            <div style="font-size: 30px; color: {COR_SECUNDARIA}; font-weight: 700; margin-top: 4px;">{qtd_apreensoes}</div>
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

df_base = carregar_dados()

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
st.markdown("<p style='font-size: 14px; color: #64748b; margin-bottom: 5px;'>Ferramenta analítica de contencioso administrativo, mapeamento de passivo e medidas acautelatórias do IBAMA.</p>", unsafe_allow_html=True)

renderizar_kpis(df)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Auditoria de Objetos", 
    "Análise Regional", 
    "Tipologia e Sanções", 
    "Pesquisa Profunda (Filtros)", 
    "Base de Dados Consolidada"
])

df_unicos = df.drop_duplicates(subset=['Nº Processo', 'Nº A.I.'])

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
        
        # INCLUSÃO DO ITEM "TODOS" NA LISTA DE OBJETOS
        lista_opcoes_objetos = ['Todos'] + df_obj['Objeto'].tolist()
        objeto_alvo = st.selectbox("", lista_opcoes_objetos, label_visibility="collapsed")
        
        if objeto_alvo == 'Todos':
            df_focado = df_unicos
            titulo_caixa_kpi = "Total Geral Mapeado"
        else:
            df_focado = df_unicos[df_unicos['Objeto Identificado'] == objeto_alvo]
            titulo_caixa_kpi = "Total Mapeado na Categoria"
        
        # KPI Dinâmico específico do Objeto selecionado
        st.markdown(f"""
        <div style="background-color: {COR_PRIMARIA}; padding: 15px 20px; border-radius: 6px; margin-bottom: 20px; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div style="font-size: 11px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; opacity: 0.9;">{titulo_caixa_kpi}</div>
            <div style="font-size: 22px; font-weight: 700; margin-top: 2px;">{len(df_focado)} Auto(s) de Infração</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Lista em formato de Sanfona para detalhamento completo da categorização
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
    df_uf_unique = df.drop_duplicates(subset=['UF_Filtro', 'Nº Processo', 'Nº A.I.'])
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
