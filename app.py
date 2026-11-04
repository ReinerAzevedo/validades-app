import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gestão de Validades", layout="wide")

# CSS Estrutural Avançado (Uso de marcadores adjacentes para forçar a cor)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Configuração base dos botões */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: bold !important;
        border: none !important;
        padding: 6px 4px !important;
        font-size: 13px !important;
        width: 100%;
        transition: 0.2s;
    }
    
    /* Ocultar os blocos dos marcadores HTML invisíveis para não gerar espaços em branco */
    div.element-container:has(.cor-marcador) {
        display: none !important;
    }
    
    /* APLICAÇÃO DAS CORES EXATAS SOLICITADAS */
    /* Botão Limpar Filtros */
    div.element-container:has(.btn-limpar) + div.element-container button { background-color: #2c3e50 !important; color: white !important; margin-bottom: 5px; }
    
    /* Cores das Datas (Vermelho, Amarelo, Azul, Cinzento) */
    div.element-container:has(.btn-todos) + div.element-container button { background-color: #7f8c8d !important; color: white !important; }
    div.element-container:has(.btn-vencidos) + div.element-container button { background-color: #e74c3c !important; color: white !important; }
    div.element-container:has(.btn-proximos) + div.element-container button { background-color: #f1c40f !important; color: black !important; }
    div.element-container:has(.btn-noprazo) + div.element-container button { background-color: #3498db !important; color: white !important; }
    
    /* Cores do Funil (Laranja, Roxo, Verde) */
    div.element-container:has(.btn-pendentes) + div.element-container button { background-color: #e67e22 !important; color: white !important; }
    div.element-container:has(.btn-conferidos) + div.element-container button { background-color: #9b59b6 !important; color: white !important; }
    div.element-container:has(.btn-resolvidos) + div.element-container button { background-color: #2ecc71 !important; color: white !important; }
    
    /* Botão Central (FAB) */
    div.element-container:has(.btn-fab) + div.element-container button {
        background-color: #05cd9e !important;
        color: white !important;
        font-size: 24px !important;
        border-radius: 50px !important;
        box-shadow: 0px 4px 10px rgba(5, 205, 158, 0.4) !important;
        height: 50px !important;
    }
    
    /* Efeito ao clicar */
    div.stButton > button:active { opacity: 0.7 !important; }
</style>
""", unsafe_allow_html=True)

st.title("🟩 PRO - Validades Loja 10")

CAMINHO_BASE = "base_validades.csv"
COLUNAS_ERP = ['Código Interno', 'GTIN', 'Descrição', 'Data de Validade', 'Data de Entrada', 'Qtde. Recebida', 'Última Venda', 'Estoque Atual', 'Qtde. Validade', 'Setor de Compra']
COLUNAS_APP = ['Chave_ID', 'Preço_Sistema', 'Preço_Oferta', 'Qtde_Real_Vencer', 'Preco_Rebaixa', 'Acao_Tomada', 'Data_Inicio_Acao', 'Status', 'Origem', 'Data_Conferencia']

def carregar_dados():
    if os.path.exists(CAMINHO_BASE):
        df = pd.read_csv(CAMINHO_BASE)
    else:
        df = pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)
    
    if 'Origem' not in df.columns:
        df['Origem'] = 'Planilha'
    if 'Data_Conferencia' not in df.columns:
        df['Data_Conferencia'] = None
        
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

# --- ESTADOS PADRÃO (LIMPOS) ---
if 'filtro_atual' not in st.session_state:
    st.session_state.filtro_atual = "Todos"
if 'funil_atual' not in st.session_state:
    st.session_state.funil_atual = "1️⃣ Pendentes"

# --- BOTÃO: LIMPAR FILTROS ---
col_limpar, col_vazia = st.columns([1, 1])
with col_limpar:
    st.markdown('<span class="cor-marcador btn-limpar"></span>', unsafe_allow_html=True)
    if st.button("🔄 Limpar Filtros", use_container_width=True):
        st.session_state.filtro_atual = "Todos"
        st.session_state.funil_atual = "1️⃣ Pendentes"
        st.rerun()

# --- FILTROS DE VALIDADE (Cinzento, Vermelho, Amarelo, Azul) ---
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    st.markdown('<span class="cor-marcador btn-todos"></span>', unsafe_allow_html=True)
    if st.button("Todos", use_container_width=True): st.session_state.filtro_atual = "Todos"
with col_f2:
    st.markdown('<span class="cor-marcador btn-vencidos"></span>', unsafe_allow_html=True)
    if st.button("Vencidos", use_container_width=True): st.session_state.filtro_atual = "Vencidos"
with col_f3:
    st.markdown('<span class="cor-marcador btn-proximos"></span>', unsafe_allow_html=True)
    if st.button("Próximos", use_container_width=True): st.session_state.filtro_atual = "Próximos"
with col_f4:
    st.markdown('<span class="cor-marcador btn-noprazo"></span>', unsafe_allow_html=True)
    if st.button("No Prazo", use_container_width=True): st.session_state.filtro_atual = "No Prazo"

# --- FILTROS DE STATUS / FUNIL (Laranja, Roxo, Verde) ---
st.write("")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    st.markdown('<span class="cor-marcador btn-pendentes"></span>', unsafe_allow_html=True)
    if st.button("Pendentes", use_container_width=True): st.session_state.funil_atual = "1️⃣ Pendentes"
with col_c2:
    st.markdown('<span class="cor-marcador btn-conferidos"></span>', unsafe_allow_html=True)
    if st.button("Conferidos", use_container_width=True): st.session_state.funil_atual = "2️⃣ Conferidos"
with col_c3:
    st.markdown('<span class="cor-marcador btn-resolvidos"></span>', unsafe_allow_html=True)
    if st.button("Resolvidos", use_container_width=True): st.session_state.funil_atual = "3️⃣ Resolvidos"

st.markdown(f"Exibindo: **{st.session_state.funil_atual[4:]}** | Validade: **{st.session_state.filtro_atual}**")

df_full = st.session_state.df_base

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
    elif st.session_state.filtro_atual == "No Prazo":
        dados_filtrados = dados_filtrados[dados_filtrados['Data de Validade'] > hoje + pd.Timedelta(days=30)]

    # --- BARRA DE BUSCA E BOTÃO ADICIONAR (+) ---
    st.write("")
    col_busca, col_add = st.columns([4, 1])
    with col_busca:
        busca = st.text_input("Busca", placeholder="Bipe o código ou digite a descrição...", label_visibility="collapsed")
    with col_add:
        st.markdown('<span class="cor-marcador btn-fab"></span>', unsafe_allow_html=True)
        add_manual = st.button("➕", use_container_width=True)

    # Modal Adicionar Produto Manual
    if add_manual:
        st.dialog("➕ Novo Produto Manual")
        with st.form("modal_add"):
            codigo_manual = st.text_input("Código de Barras:")
            descricao_manual = st.text_input("Descrição do Produto:")
            val_manual = st.date_input("Data de Validade")
            q_manual = st.number_input("Quantidade (Un)", min_value=1, step=1)
            p_manual = st.number_input("Preço Atual (R$)", min_value=0.0, format="%.2f")
            setor_m = st.selectbox("Setor", ["Mercearia", "Perecíveis", "Açougue", "Padaria", "FLV", "Outros"])
            acao_m = st.selectbox("Ação a Tomar", ["Registrar como Pendente", "Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"])
            
            if st.form_submit_button("Gravar Produto na Base"):
                if codigo_manual and descricao_manual:
                    chave = f"{codigo_manual.strip()}_{val_manual.strftime('%Y-%m-%d')}"
                    
                    if acao_m == "Registrar como Pendente":
                        status_m = "Pendente"
                        data_conf_m = None
                    else:
                        status_m = "Resolvido" if acao_m in ["Nenhuma - OK", "Resolvido - Sem Estoque Físico"] else "Conferido"
                        data_conf_m = pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y %H:%M')

                    novo_item = {
                        'Chave_ID': chave, 'Código Interno': codigo_manual.strip(), 'GTIN': codigo_manual.strip(),
                        'Descrição': descricao_manual, 'Data de Validade': val_manual.strftime('%Y-%m-%d'),
                        'Qtde. Validade': q_manual, 'Qtde_Real_Vencer': q_manual,
                        'Preço_Sistema': p_manual, 'Setor de Compra': setor_m, 
                        'Acao_Tomada': acao_m if acao_m != "Registrar como Pendente" else None,
                        'Status': status_m, 'Origem': 'Manual', 'Data_Conferencia': data_conf_m
                    }
                    
                    df_nova_linha = pd.DataFrame([novo_item]).set_index('Chave_ID')
                    df_b = st.session_state.df_base.set_index('Chave_ID') if 'Chave_ID' in st.session_state.df_base.columns else st.session_state.df_base
                    df_b = pd.concat([df_b, df_nova_linha]).reset_index()
                    st.session_state.df_base = df_b
                    salvar_base()
                    st.success("✅ Produto Adicionado!")
                    st.rerun()
                else:
                    st.error("Preencha o Código e a Descrição.")

    # --- LISTAGEM DOS CARDS VISUAIS ---
    if not dados_filtrados.empty:
        if busca:
            busca_limpa = busca.strip()
            dados_filtrados = dados_filtrados[
                (dados_filtrados['Código Interno'].astype(str) == busca_limpa) | 
                (dados_filtrados['GTIN'].astype(str).str.replace('.0', '', regex=False) == busca_limpa) |
                (dados_filtrados['Descrição'].astype(str).str.contains(busca_limpa, case=False))
            ]

        for index, item in dados_filtrados.iterrows():
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

            tag_auditoria = ""
            if pd.notna(item.get('Data_Conferencia')) and item.get('Data_Conferencia'):
                tag_auditoria = f"<br><span style='color: {'#e0e0e0' if card_bg == '#c94c4c' else '#4a4a4a'};'>✅ Auditado em: {item['Data_Conferencia']}</span>"

            st.markdown(f"""
            <div style="background-color: {card_bg}; color: {text_color}; padding: 15px; border-radius: 10px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-size: 16px; font-weight: bold; color: {text_color};">{item['Descrição']}</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px;">{badge_text}</p>
                <p style="margin: 2px 0 0 0; font-size: 12px; opacity: 0.8;">Cód: {item['Código Interno']} | Saldo ERP: {item['Qtde. Validade']} un {tag_auditoria}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.funil_atual != "3️⃣ Resolvidos":
                with st.expander(f"Ação para: {item['Código Interno']}"):
                    with st.form(key=f"form_auditar_{item['Chave_ID']}"):
                        qt_real = st.number_input("Quantidade Real", value=int(item['Qtde. Validade']) if pd.notna(item['Qtde. Validade']) else 0)
                        acao = st.selectbox("Ação Tomada", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"])
                        preco_reb = st.number_input("Preço da Rebaixa (R$)", value=0.0)
                        foto = st.file_uploader("Foto Evidência (Opcional)", type=['jpg', 'jpeg', 'png'])
                        
                        if st.form_submit_button("Confirmar Auditoria"):
                            idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == item['Chave_ID']].tolist()[0]
                            st.session_state.df_base.at[idx, 'Qtde_Real_Vencer'] = qt_real
                            st.session_state.df_base.at[idx, 'Acao_Tomada'] = acao
                            st.session_state.df_base.at[idx, 'Preco_Rebaixa'] = preco_reb
                            st.session_state.df_base.at[idx, 'Status'] = 'Resolvido' if acao in ["Nenhuma - OK", "Resolvido - Sem Estoque Físico"] else 'Conferido'
                            st.session_state.df_base.at[idx, 'Data_Conferencia'] = pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y %H:%M')
                            
                            salvar_base()
                            st.success("Auditoria Registada com Sucesso!")
                            st.rerun()
    else:
        st.info("Nenhum produto encontrado nesta categoria de filtros.")
else:
    st.info("A base de dados encontra-se vazia.")
