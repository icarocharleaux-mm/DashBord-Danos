import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Dashboard Logístico", layout="wide", page_icon="🚚")

# --- INJEÇÃO DE CSS ---
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        color: #1f77b4; 
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        color: #555555;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 2. Carregamento de Dados
@st.cache_data
def load_data():
    df = pd.read_csv("dados_danos.csv.csv", sep=";", encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    
    if 'Transportadora' in df.columns:
        df = df.rename(columns={'Transportadora': 'Motorista'})
        
    return df

try:
    df_base = load_data()

    st.title("📊 Painel de Ocorrências e Danos")
    st.markdown("Acompanhamento interativo de manifestações operacionais.")
    st.divider()

    # --- CRIANDO ABAS PARA VISÕES ESPECÍFICAS ---
    aba1, aba2 = st.tabs(["📈 Visão Geral", "🏢 Comparativo de Filiais"])

    # 3. ÁREA DE FILTROS
    with st.sidebar:
        st.header("🔍 Filtros Globais")
        st.write("Estes filtros afetam todas as abas.")
        
        opcoes_motorista = ["Todos"] + sorted(df_base["Motorista"].unique().tolist())
        motorista_sel = st.selectbox("Motorista:", opcoes_motorista)

        opcoes_filial = ["Todas"] + sorted(df_base["filial"].unique().tolist())
        filial_sel = st.selectbox("Filial:", opcoes_filial)

        opcoes_cat = ["Todas"] + sorted(df_base["categoria"].unique().tolist())
        cat_sel = st.selectbox("Categoria:", opcoes_cat)

    # APLICANDO OS FILTROS
    df_filtrado = df_base.copy()

    if motorista_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Motorista"] == motorista_sel]
    if filial_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["filial"] == filial_sel]
    if cat_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["categoria"] == cat_sel]

    # ==========================================
    # CONTEÚDO DA ABA 1: VISÃO GERAL
    # ==========================================
    with aba1:
        # 4. KPIs DINÂMICOS
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Ocorrências Totais", len(df_filtrado))
        k2.metric("Motoristas Envolvidos", df_filtrado["Motorista"].nunique())
        k3.metric("Filiais Afetadas", df_filtrado["filial"].nunique())
        
        if "qtd_reclamada" in df_filtrado.columns:
            total_reclamado = int(df_filtrado["qtd_reclamada"].fillna(0).sum())
            k4.metric("Itens Reclamados", total_reclamado)
        else:
            k4.metric("Itens Reclamados", "N/A")

        st.write("---") 

        # 5. GRÁFICOS
        col_esq, col_dir = st.columns(2)

        with col_esq:
            st.subheader("🚛 Top 10 Motoristas (Danos)")
            contagem_motorista = df_filtrado["Motorista"].value_counts().head(10).reset_index()
            contagem_motorista.columns = ['Motorista', 'Ocorrências'] 
            
            # --- LÓGICA PARA DESTACAR OS TOP 5 ---
            # Criamos uma coluna 'Cor' que classifica os 5 primeiros como "Top 5" e o restante como "Outros"
            contagem_motorista['Classificação'] = ['Top 5 (Atenção)'] * min(5, len(contagem_motorista)) + ['Outros'] * max(0, len(contagem_motorista) - 5)
            
            # Mapeamos as cores: Vermelho para os Top 5, Azul para os outros
            mapa_cores = {'Top 5 (Atenção)': '#d62728', 'Outros': '#1f77b4'}
            
            fig1 = px.bar(contagem_motorista, x="Ocorrências", y="Motorista", orientation='h',
                          color='Classificação', color_discrete_map=mapa_cores) 
            
            fig1.update_layout(
                showlegend=False, # Escondemos a legenda para ficar limpo
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="", 
                yaxis_title="",
                yaxis={'categoryorder':'total ascending'} 
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_dir:
            st.subheader("📦 Tipos de Manifestação")
            contagem_dano = df_filtrado["tipo_manifestacao_sistema"].value_counts().reset_index()
            contagem_dano.columns = ['Tipo', 'Quantidade']
            
            fig2 = px.pie(contagem_dano, names="Tipo", values="Quantidade", hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(
                showlegend=False, 
                plot_bgcolor="rgba(0,0,0,0)", 
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig2, use_container_width=True)

        # 6. TABELA E EXPORTAÇÃO
        st.subheader("📋 Detalhes dos Registros Filtrados")
        
        # --- BOTÃO DE EXPORTAÇÃO PARA EXCEL/CSV ---
        # Convertendo o DataFrame filtrado para formato CSV, usando o separador ; e formato compatível com Excel no Brasil
        csv_export = df_filtrado.to_csv(index=False, sep=';').encode('latin-1')
        
        st.download_button(
            label="📥 Baixar Tabela Filtrada (Excel/CSV)",
            data=csv_export,
            file_name='dados_filtrados_operacao.csv',
            mime='text/csv',
        )
        
        st.dataframe(df_filtrado, use_container_width=True, height=250)

    # ==========================================
    # CONTEÚDO DA ABA 2: COMPARATIVO DE FILIAIS
    # ==========================================
    with aba2:
        st.subheader("🏢 Análise de Volume por Filial")
        st.markdown("Compare o volume de ocorrências e identifique quais bases exigem maior atenção.")
        
        # Agrupando os dados por filial
        contagem_filial = df_filtrado["filial"].value_counts().reset_index()
        contagem_filial.columns = ['Filial', 'Total de Ocorrências']
        
        col_grafico, col_tabela = st.columns([2, 1])
        
        with col_grafico:
            # Gráfico de barras verticais comparando as filiais
            fig3 = px.bar(contagem_filial, x="Filial", y="Total de Ocorrências", text="Total de Ocorrências",
                          color="Filial", color_discrete_sequence=px.colors.qualitative.Set2)
            
            fig3.update_traces(textposition='outside') # Coloca o número em cima da barra
            fig3.update_layout(
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="",
                yaxis_title="Qtd de Ocorrências"
            )
            st.plotly_chart(fig3, use_container_width=True)
            
        with col_tabela:
            st.write("Resumo Numérico:")
            st.dataframe(contagem_filial, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao processar o Dashboard: {e}")
    st.info("Verifique se o arquivo 'dados_danos.csv.csv' está na pasta e se as colunas estão corretas.")