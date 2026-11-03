import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gestão de Validades", layout="wide")
st.title("📋 Controle de Validades - Loja 10")

CAMINHO_BASE = "base_validades.csv"
COLUNAS_ERP = ['Código Interno', 'GTIN', 'Descrição', 'Data de Validade', 'Data de Entrada', 'Qtde. Recebida', 'Última Venda', 'Estoque Atual', 'Qtde. Validade', 'Setor de Compra']
COLUNAS_APP = ['Chave_ID', 'Preço_Sistema', 'Preço_Oferta', 'Qtde_Real_Vencer', 'Preco_Rebaixa', 'Acao_Tomada', 'Data_Inicio_Acao', 'Status']

# --- OTIMIZAÇÃO 1: CARREGAMENTO EM MEMÓRIA ---
def carregar_dados():
    if os.path.exists(CAMINHO_BASE):
        return pd.read_csv(CAMINHO_BASE)
    return pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)

if 'df_base' not in st.session_state:
    st.session_state.df_base = carregar_dados()

def atualizar_base_cumulativa(arquivos_upados):
    try:
        lista_dfs = []
        for arq in arquivos_upados:
            df = pd.read_excel(arq, header=27)
            df = df[COLUNAS_ERP].copy()
            df.dropna(subset=['Código Interno', 'Data de Validade'], inplace=True)
            df['Código Interno'] = pd.to_numeric(df['Código Interno'], errors='coerce').fillna(0).astype(int).astype(str)
            df['Data de Validade'] = pd.to_datetime(df['Data de Validade']).dt.strftime('%Y-%m-%d')
            df['Chave_ID'] = df['Código Interno'] + "_" + df['Data de Validade']
            lista_dfs.append(df)
            
        if not lista_dfs:
            return False

        df_novo = pd.concat(lista_dfs, ignore_index=True).drop_duplicates(subset=['Chave_ID'], keep='first')
        df_base = st.session_state.df_base.copy()
        
        if 'Chave_ID' in df_base.columns:
            df_base.set_index('Chave_ID', inplace=True)
        df_novo.set_index('Chave_ID', inplace=True)
        
        for col in df_novo.columns:
            if col in df_base.columns:
                df_base[col] = df_base[col].astype(object)
                df_novo[col] = df_novo[col].astype(object)
                
        df_base.update(df_novo)
        
        itens_novos = df_novo[~df_novo.index.isin(df_base.index)].copy()
        for col in COLUNAS_APP:
            if col not in itens_novos.columns and col != 'Chave_ID':
                itens_novos[col] = None
        if not itens_novos.empty:
            itens_novos['Status'] = 'Pendente'
        
        df_atualizado = pd.concat([df_base, itens_novos]).reset_index()
        df_atualizado.to_csv(CAMINHO_BASE, index=False)
        st.session_state.df_base = df_atualizado # Atualiza a memória
        return True
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return False

# --- SEÇÃO 1: UPLOAD ---
with st.expander("📂 Atualizar Base de Dados (Upload do ERP)"):
    arquivos = st.file_uploader("Selecione os relatórios", accept_multiple_files=True)
    if arquivos and st.button("Processar e Atualizar Base"):
        with st.spinner("Consolidando dados..."):
            if atualizar_base_cumulativa(arquivos):
                st.success("Base atualizada! Pode fechar esta aba.")
                st.rerun()

# --- SEÇÃO 2: AÇÃO NO CHÃO DE LOJA ---
st.divider()
st.header("📱 Ação no Chão de Loja")

df_full = st.session_state.df_base

if not df_full.empty:
    pendentes = df_full[df_full['Status'] == 'Pendente']
    
    st.metric("Itens Pendentes de Ação", len(pendentes))
    
    if not pendentes.empty:
        # --- OTIMIZAÇÃO 2: TABELA ESCONDIDA ---
        with st.expander("Ver Tabela Completa (Pode ser lento no celular)"):
            st.dataframe(pendentes[['Código Interno', 'Descrição', 'Data de Validade', 'Qtde. Validade']])
        
        st.markdown("### 🔍 Localizar Produto")
        busca = st.text_input("Bipe o GTIN ou digite o Código Interno:")
        
        if busca:
            busca_limpa = busca.strip()
            mask_codigo = pendentes['Código Interno'].astype(str) == busca_limpa
            mask_gtin = pendentes['GTIN'].astype(str).str.replace('.0', '', regex=False) == busca_limpa
            pendentes_filtrado = pendentes[mask_codigo | mask_gtin]
        else:
            # --- OTIMIZAÇÃO 3: LIMITE DE EXIBIÇÃO NO SELECTBOX ---
            pendentes_filtrado = pendentes.head(30)
            if len(pendentes) > 30:
                st.caption("Mostrando apenas os 30 itens mais urgentes. Use a busca acima para encontrar outros produtos.")
            
        if pendentes_filtrado.empty:
            st.warning("Nenhum produto encontrado com este código.")
        else:
            opcoes_produtos = pendentes_filtrado['Chave_ID'].astype(str) + " | " + pendentes_filtrado['Descrição'].astype(str)
            produto_selecionado = st.selectbox("Selecione o vencimento para auditar:", opcoes_produtos.tolist())
            
            if produto_selecionado:
                chave_atual = produto_selecionado.split(" | ")[0]
                item_atual = pendentes_filtrado[pendentes_filtrado['Chave_ID'] == chave_atual].iloc[0]
                
                st.info(f"**Vencimento:** {item_atual['Data de Validade']} | **Saldo ERP:** {item_atual['Qtde. Validade']} un")
                
                with st.form(key="form_acao"):
                    col1, col2 = st.columns(2)
                    with col1:
                        qtde_projetada = int(item_atual['Qtde. Validade']) if pd.notna(item_atual['Qtde. Validade']) else 0
                        qtde_real = st.number_input("Qtd Física Real", min_value=0, step=1, value=qtde_projetada)
                        acao = st.selectbox("Ação a Tomar", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"])
                    with col2:
                        preco_rebaixa = st.number_input("Preço Rebaixa (R$)", min_value=0.0, format="%.2f")
                        data_acao = st.date_input("Data de Início")
                    
                    foto = st.camera_input("Capturar Imagem (Opcional)")
                    btn_salvar = st.form_submit_button("Salvar Ação")
                    
                    if btn_salvar:
                        if acao == "Resolvido - Sem Estoque Físico":
                            qtde_real = 0
                            status_final = "Concluído"
                        else:
                            status_final = "Em Andamento" if acao == "Rebaixa" else "Concluído"
                        
                        # Atualiza direto na memória e salva em background
                        idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == chave_atual].tolist()[0]
                        st.session_state.df_base.at[idx, 'Qtde_Real_Vencer'] = qtde_real
                        st.session_state.df_base.at[idx, 'Preco_Rebaixa'] = preco_rebaixa
                        st.session_state.df_base.at[idx, 'Acao_Tomada'] = acao
                        st.session_state.df_base.at[idx, 'Data_Inicio_Acao'] = data_acao.strftime('%Y-%m-%d')
                        st.session_state.df_base.at[idx, 'Status'] = status
