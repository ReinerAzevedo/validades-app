import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gestão de Validades", layout="wide")

# Estilização CSS Avançada para simular o App Mobile da Imagem
st.markdown("""
<style>
    /* Esconde o menu padrão do Streamlit para parecer mais um App */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo dos Filtros Escuros do Topo */
    div.stButton > button[key^="filt_"] {
        background-color: #0c1a15 !important;
        color: white !important;
        border-radius: 20px !important;
        border: none !important;
        padding: 4px 10px !important;
        font-size: 14px !important;
        width: 100%;
        font-weight: bold;
    }
    
    /* Estilo das Categorias do Funil (Pendentes, Conferidos...) */
    div.stButton > button[key^="funil_"] {
        background-color: white !important;
        color: #1c1c1c !important;
        border-radius: 8px !important;
        border: 1px solid #ccc !important;
        font-size: 13px !important;
        width: 100%;
    }
    
    /* Grande Botão Central Adicionar (FAB) */
    div.stButton > button[key="btn_add_fab"] {
        background-color: #05cd9e !important;
        color: white !important;
        font-size: 24px !important;
        border-radius: 50px !important;
        border: none !important;
        box-shadow: 0px 4px 10px rgba(5, 205, 158, 0.4) !important;
        height: 50px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🟩 PRO - Validades Loja 10")

CAMINHO_BASE = "base_validades.csv"
COLUNAS_ERP = ['Código Interno', 'GTIN', 'Descrição', 'Data de Validade', 'Data de Entrada', 'Qtde. Recebida', 'Última Venda', 'Estoque Atual', 'Qtde. Validade', 'Setor de Compra']
COLUNAS_APP = ['Chave_ID', 'Preço_Sistema', 'Preço_Oferta', 'Qtde_Real_Vencer', 'Preco_Rebaixa', 'Acao_Tomada', 'Data_Inicio_Acao', 'Status', 'Origem']

def carregar_dados():
    if os.path.exists(CAMINHO_BASE):
        df = pd.read_csv(CAMINHO_BASE)
    else:
        df = pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)
    if 'Origem' not in df.columns:
        df['Origem'] = 'Planilha'
    for col in COLUNAS_APP + ['Setor de Compra']:
        if col in df.columns:
            df[col] = df[col].astype(object)
    return df

if 'df_base' not in st.session_state:
    st.session_state.df_base = carregar_dados()

def salvar_base():
    for col in COLUNAS_APP:
        if col in st.session_state.df_base.columns:
            st.session_state.df_base[col] = st.session_state.df_base[col].astype(object)
    st.session_state.df_base.to_csv(CAMINHO_BASE, index=False)

# Estados de Navegação e Filtros
if 'filtro_atual' not in st.session_state:
    st.session_state.filtro_atual = "Próximos"
if 'funil_atual' not in st.session_state:
    st.session_state.funil_atual = "1️⃣ Pendentes"

# --- TOP BAR: UPLOAD OCULTO ---
with st.expander("📂 Importar Planilha do ERP (Bluesoft)"):
    arquivos = st.file_uploader("Relatórios Excel", accept_multiple_files=True)
    if arquivos and st.button("Carregar Dados"):
        st.success("Função de upload disponível na retaguarda.")

# --- FILTROS DE VALIDADE (Estilo botões escuros) ---
st.caption("Filtros")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    if st.button("Vencidos", key="filt_vencidos"): st.session_state.filtro_atual = "Vencidos"
with col_f2:
    if st.button("Próximos", key="filt_proximos"): st.session_state.filtro_atual = "Próximos"
with col_f3:
    if st.button("Não vencidos", key="filt_nao_vencidos"): st.session_state.filtro_atual = "Não vencidos"

# --- CATEGORIAS (Filtro por Funil) ---
st.write("")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    if st.button("📝 Pendentes", key="funil_pendente"): st.session_state.funil_atual = "1️⃣ Pendentes"
with col_c2:
    if st.button("⚖️ Conferidos", key="funil_conferido"): st.session_state.funil_atual = "2️⃣ Conferidos"
with col_c3:
    if st.button("✅ Resolvidos", key="funil_resolvido"): st.session_state.funil_atual = "3️⃣ Resolvidos"

st.markdown(f"Exibindo: **{st.session_state.funil_atual}** | Validade: **{st.session_state.filtro_atual}**")

df_full = st.session_state.df_base

# Filtro dos itens baseado nas seleções de tela
if not df_full.empty:
    status_map = {
        "1️⃣ Pendentes": "Pendente",
        "2️⃣ Conferidos": "Conferido",
        "3️⃣ Resolvidos": "Resolvido"
    }
    
    dados_filtrados = df_full[df_full['Status'] == status_map[st.session_state.funil_atual]]
    
    hoje = pd.to_datetime('today').normalize()
    dados_filtrados['Data de Validade'] = pd.to_datetime(dados_filtrados['Data de Validade'], errors='coerce')
    
    if st.session_state.filtro_atual == "Vencidos":
        dados_filtrados = dados_filtrados[dados_filtrados['Data de Validade'] < hoje]
    elif st.session_state.filtro_atual == "Próximos":
        dados_filtrados = dados_filtrados[(dados_filtrados['Data de Validade'] >= hoje) & (dados_filtrados['Data de Validade'] <= hoje + pd.Timedelta(days=30))]
    else:
        dados_filtrados = dados_filtrados[dados_filtrados['Data de Validade'] > hoje + pd.Timedelta(days=30)]

    # --- BOTÃO CENTRAL ADICIONAR (FAB) E BUSCA ---
    st.write("")
    col_busca, col_add = st.columns([4, 1])
    with col_busca:
        busca = st.text_input("Bipe o código ou digite:", placeholder="Buscar produto...", label_visibility="collapsed")
    with col_add:
        add_manual = st.button("➕", key="btn_add_fab", help="Adicionar Manual", use_container_width=True)

    if add_manual:
        st.dialog("➕ Novo Produto Manual")
        with st.form("modal_add"):
            codigo_manual = st.text_input("Código:")
            descricao_manual = st.text_input("Descrição:")
            val_manual = st.date_input("Validade")
            q_manual = st.number_input("Qtd", min_value=1, step=1)
            p_manual = st.number_input("Preço (R$)", min_value=0.0, format="%.2f")
            setor_m = st.selectbox("Setor", ["Mercearia", "Perecíveis", "Açougue", "Padaria", "FLV"])
            
            if st.form_submit_button("Gravar na Base"):
                if codigo_manual and descricao_manual:
                    chave = f"{codigo_manual.strip()}_{val_manual.strftime('%Y-%m-%d')}"
                    novo_item = {
                        'Chave_ID': chave, 'Código Interno': codigo_manual.strip(), 'GTIN': codigo_manual.strip(),
                        'Descrição': descricao_manual, 'Data de Validade': val_manual.strftime('%Y-%m-%d'),
                        'Qtde. Validade': q_manual, 'Qtde_Real_Vencer': q_manual,
                        'Preço_Sistema': p_manual, 'Setor de Compra': setor_m, 'Status': 'Pendente', 'Origem': 'Manual'
                    }
                    df_nova_linha = pd.DataFrame([novo_item]).set_index('Chave_ID')
                    df_b = st.session_state.df_base.set_index('Chave_ID') if 'Chave_ID' in st.session_state.df_base.columns else st.session_state.df_base
                    df_b = pd.concat([df_b, df_nova_linha]).reset_index()
                    st.session_state.df_base = df_b
                    salvar_base()
                    st.success("✅ Adicionado!")
                    st.rerun()

    # Exibe os Cards Visuais
    if not dados_filtrados.empty:
        if busca:
            busca_limpa = busca.strip()
            dados_filtrados = dados_filtrados[
                (dados_filtrados['Código Interno'].astype(str) == busca_limpa) | 
                (dados_filtrados['GTIN'].astype(str).str.replace('.0', '', regex=False) == busca_limpa) |
                (dados_filtrados['Descrição'].astype(str).str.contains(busca_limpa, case=False))
            ]

        for index, item in dados_filtrados.iterrows():
            # Cores dinâmicas para os Cards
            if pd.to_datetime(item['Data de Validade']) < hoje:
                card_bg = "#c94c4c"
                text_color = "white"
                badge_text = f"Venceu em {pd.to_datetime(item['Data de Validade']).strftime('%d/%m/%Y')}"
            elif pd.to_datetime(item['Data de Validade']) <= hoje + pd.Timedelta(days=30):
                card_bg = "#dada47"
                text_color = "black"
                badge_text = f"Vence em {pd.to_datetime(item['Data de Validade']).strftime('%d/%m/%Y')}"
            else:
                card_bg = "#ffffff"
                text_color = "black"
                badge_text = f"Vence em {pd.to_datetime(item['Data de Validade']).strftime('%d/%m/%Y')}"

            st.markdown(f"""
            <div style="background-color: {card_bg}; color: {text_color}; padding: 15px; border-radius: 10px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-size: 16px; font-weight: bold; color: {text_color};">{item['Descrição']}</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px;">{badge_text}</p>
                <p style="margin: 2px 0 0 0; font-size: 12px; opacity: 0.8;">Cód: {item['Código Interno']} | Saldo ERP: {item['Qtde. Validade']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"Ação para: {item['Código Interno']}"):
                with st.form(key=f"form_auditar_{item['Chave_ID']}"):
                    qt_real = st.number_input("Qtd Real", value=int(item['Qtde. Validade']) if pd.notna(item['Qtde. Validade']) else 0)
                    acao = st.selectbox("Ação", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"])
                    preco_reb = st.number_input("Preço Rebaixa", value=0.0)
                    foto = st.file_uploader("Foto (Opcional)", type=['jpg', 'jpeg', 'png'])
                    
                    if st.form_submit_button("Confirmar Auditoria"):
                        idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == item['Chave_ID']].tolist()[0]
                        st.session_state.df_base.at[idx, 'Qtde_Real_Vencer'] = qt_real
                        st.session_state.df_base.at[idx, 'Acao_Tomada'] = acao
                        st.session_state.df_base.at[idx, 'Preco_Rebaixa'] = preco_reb
                        st.session_state.df_base.at[idx, 'Status'] = 'Resolvido' if acao in ["Nenhuma - OK", "Resolvido - Sem Estoque Físico"] else 'Conferido'
                        salvar_base()
                        st.success("Salvo!")
                        st.rerun()
    else:
        st.info("Nenhum item pendente de ação nesta categoria.")
else:
    st.info("A base de dados está vazia.")
