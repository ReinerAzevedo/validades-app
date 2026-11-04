import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gestão de Validades", layout="wide")
st.title("📋 Controle de Validades - Loja 10")

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
    # Garante a flexibilidade antes de gravar no disco
    for col in COLUNAS_APP:
        if col in st.session_state.df_base.columns:
            st.session_state.df_base[col] = st.session_state.df_base[col].astype(object)
    st.session_state.df_base.to_csv(CAMINHO_BASE, index=False)

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
            itens_novos['Origem'] = 'Planilha'
        
        df_atualizado = pd.concat([df_base, itens_novos]).reset_index()
        
        for col in COLUNAS_APP:
            if col in df_atualizado.columns:
                df_atualizado[col] = df_atualizado[col].astype(object)
                
        st.session_state.df_base = df_atualizado
        salvar_base()
        return True
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return False

# --- SEÇÕES OCULTAS DE ADMINISTRAÇÃO ---
with st.expander("📂 Atualizar Base via ERP (Upload)"):
    arquivos = st.file_uploader("Selecione os relatórios", accept_multiple_files=True)
    if arquivos and st.button("Processar e Atualizar Base"):
        with st.spinner("Consolidando dados..."):
            if atualizar_base_cumulativa(arquivos):
                st.success("Base atualizada! Pode fechar esta aba.")
                st.rerun()

with st.expander("➕ Adicionar Produto Manual (Fora do Sistema)"):
    with st.form("form_manual", clear_on_submit=False):
        codigo_manual = st.text_input("Bipe o Código de Barras ou digite o Código Interno:")
        descricao_manual = st.text_input("Descrição do Produto:")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            validade_manual = st.date_input("Data de Validade")
            qtde_manual = st.number_input("Qtd na Gôndola", min_value=1, step=1)
            preco_atual_manual = st.number_input("Preço Atual (R$)", min_value=0.0, format="%.2f")
            
        with col_m2:
            setor_manual = st.selectbox("Setor", ["Mercearia", "Perecíveis", "Açougue", "Padaria", "FLV", "Outros"])
            acao_manual = st.selectbox("Ação a Tomar", ["Registrar como Pendente", "Rebaixa", "Descarte", "Troca", "Nenhuma - OK"])
            preco_rebaixa_manual = st.number_input("Preço Rebaixa", min_value=0.0, format="%.2f")
            
        foto_manual = st.file_uploader("📸 Foto (Opcional)", type=['jpg', 'jpeg', 'png'], key="foto_manual")
        btn_salvar_manual = st.form_submit_button("Salvar Produto na Base")
        
        if btn_salvar_manual:
            if not codigo_manual or not descricao_manual:
                st.error("⚠️ Código e Descrição são obrigatórios!")
            else:
                cod_limpo = codigo_manual.strip()
                data_val_str = validade_manual.strftime('%Y-%m-%d')
                chave_manual = f"{cod_limpo}_{data_val_str}"
                
                # Inteligência do Funil na adição manual
                if acao_manual == "Registrar como Pendente":
                    status_final_manual = "Pendente"
                elif acao_manual in ["Nenhuma - OK", "Resolvido - Sem Estoque Físico"]:
                    status_final_manual = "Resolvido"
                else:
                    status_final_manual = "Conferido" # Vai pra gerência aprovar
                
                novo_item = {
                    'Chave_ID': chave_manual, 'Código Interno': cod_limpo, 'GTIN': cod_limpo,
                    'Descrição': descricao_manual, 'Data de Validade': data_val_str,
                    'Qtde. Validade': qtde_manual, 'Qtde_Real_Vencer': qtde_manual,
                    'Preço_Sistema': preco_atual_manual, 'Preco_Rebaixa': preco_rebaixa_manual,
                    'Setor de Compra': setor_manual, 
                    'Acao_Tomada': acao_manual if acao_manual != "Registrar como Pendente" else None,
                    'Status': status_final_manual, 'Origem': 'Manual'
                }
                
                df_nova_linha = pd.DataFrame([novo_item]).set_index('Chave_ID')
                df_b = st.session_state.df_base.copy()
                if 'Chave_ID' in df_b.columns:
                    df_b.set_index('Chave_ID', inplace=True)
                
                if chave_manual in df_b.index:
                    df_b.update(df_nova_linha)
                else:
                    df_b = pd.concat([df_b, df_nova_linha])
                    
                st.session_state.df_base = df_b.reset_index()
                salvar_base()
                st.success("✅ Produto adicionado!")
                st.rerun()

st.divider()

# --- FUNIL OPERACIONAL (ABAS) ---
tab_pendente, tab_conferido, tab_resolvido = st.tabs(["1️⃣ Pendentes", "2️⃣ Conferidos (Ação)", "3️⃣ Resolvidos"])

df_full = st.session_state.df_base

if not df_full.empty:
    
    # ---------------------------------------------------------
    # ABA 1: PENDENTES (Chão de Loja)
    # ---------------------------------------------------------
    with tab_pendente:
        pendentes = df_full[df_full['Status'] == 'Pendente']
        st.metric("Total para Auditar na Gôndola", len(pendentes))
        
        if not pendentes.empty:
            busca = st.text_input("Bipe o GTIN ou digite o Código (Pendentes):", key="busca_pendente")
            
            if busca:
                busca_limpa = busca.strip()
                mask_codigo = pendentes['Código Interno'].astype(str) == busca_limpa
                mask_gtin = pendentes['GTIN'].astype(str).str.replace('.0', '', regex=False) == busca_limpa
                pend_filtro = pendentes[mask_codigo | mask_gtin]
            else:
                pend_filtro = pendentes.head(30)
                
            if not pend_filtro.empty:
                opcoes = pend_filtro['Chave_ID'].astype(str) + " | " + pend_filtro['Descrição'].astype(str)
                prod_sel = st.selectbox("Selecione o vencimento para auditar:", opcoes.tolist(), key="sel_pend")
                
                if prod_sel:
                    chave = prod_sel.split(" | ")[0]
                    item = pend_filtro[pend_filtro['Chave_ID'] == chave].iloc[0]
                    
                    origem_tag = "🎯 ERP" if item['Origem'] == 'Planilha' else "✋ Manual"
                    st.info(f"**Vencimento:** {item['Data de Validade']} | **Saldo ERP:** {item['Qtde. Validade']} un | **Origem:** {origem_tag}")
                    
                    with st.form(key="form_pendente"):
                        c1, c2 = st.columns(2)
                        with c1:
                            qtde_proj = int(item['Qtde. Validade']) if pd.notna(item['Qtde. Validade']) else 0
                            qtde_real = st.number_input("Qtd Física Real", min_value=0, step=1, value=qtde_proj)
                            acao = st.selectbox("Ação a Tomar", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"])
                        with c2:
                            preco_rebaixa = st.number_input("Preço Rebaixa (R$)", min_value=0.0, format="%.2f")
                            data_acao = st.date_input("Data de Início")
                        
                        foto = st.file_uploader("📸 Capturar Imagem", type=['jpg', 'jpeg', 'png'])
                        if st.form_submit_button("Salvar Auditoria"):
                            
                            # Inteligência: Via Expressa
                            if acao in ["Nenhuma - OK", "Resolvido - Sem Estoque Físico"]:
                                status_final = "Resolvido"
                                if acao == "Resolvido - Sem Estoque Físico": qtde_real = 0
                            else:
                                status_final = "Conferido" # Passa para a Aba 2
                                
                            idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == chave].tolist()[0]
                            st.session_state.df_base.at[idx, 'Qtde_Real_Vencer'] = qtde_real
                            st.session_state.df_base.at[idx, 'Preco_Rebaixa'] = preco_rebaixa
                            st.session_state.df_base.at[idx, 'Acao_Tomada'] = acao
                            st.session_state.df_base.at[idx, 'Data_Inicio_Acao'] = data_acao.strftime('%Y-%m-%d')
                            st.session_state.df_base.at[idx, 'Status'] = status_final
                            salvar_base()
                            st.rerun()

    # ---------------------------------------------------------
    # ABA 2: CONFERIDOS (Retaguarda / Ação Sistêmica)
    # ---------------------------------------------------------
    with tab_conferido:
        conferidos = df_full[df_full['Status'] == 'Conferido']
        st.metric("Itens aguardando ação no ERP (Rebaixa/Troca/Descarte)", len(conferidos))
        
        if not conferidos.empty:
            # Mostra a tabela para o gerente ver tudo de uma vez
            st.dataframe(conferidos[['Código Interno', 'Descrição', 'Data de Validade', 'Qtde_Real_Vencer', 'Acao_Tomada', 'Preco_Rebaixa']])
            
            st.markdown("### ⚡ Finalizar Ação")
            opcoes_conf = conferidos['Chave_ID'].astype(str) + " | " + conferidos['Descrição'].astype(str) + " (" + conferidos['Acao_Tomada'].astype(str) + ")"
            prod_conf_sel = st.selectbox("Marcar como resolvido:", opcoes_conf.tolist(), key="sel_conf")
            
            if prod_conf_sel:
                chave_conf = prod_conf_sel.split(" | ")[0]
                if st.button("✅ Confirmar Ação Realizada (Mover para Resolvidos)", type="primary"):
                    idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == chave_conf].tolist()[0]
                    st.session_state.df_base.at[idx, 'Status'] = 'Resolvido'
                    salvar_base()
                    st.success("Item finalizado com sucesso!")
                    st.rerun()

    # ---------------------------------------------------------
    # ABA 3: RESOLVIDOS (Histórico)
    # ---------------------------------------------------------
    with tab_resolvido:
        resolvidos = df_full[df_full['Status'] == 'Resolvido']
        st.metric("Total de Itens Resolvidos", len(resolvidos))
        
        if not resolvidos.empty:
            st.dataframe(resolvidos[['Código Interno', 'Descrição', 'Data de Validade', 'Acao_Tomada', 'Origem']])
            
            st.caption("Estes itens já foram auditados e processados. O histórico permanece salvo na base de dados para consultas e auditorias futuras.")
            
            # Botão de emergência caso o gerente tenha finalizado sem querer
            with st.expander("Desfazer / Retornar item"):
                opcoes_res = resolvidos['Chave_ID'].astype(str) + " | " + resolvidos['Descrição'].astype(str)
                prod_res_sel = st.selectbox("Selecione um item para voltar:", opcoes_res.tolist(), key="sel_res")
                if prod_res_sel and st.button("↩️ Voltar para Pendente"):
                    chave_res = prod_res_sel.split(" | ")[0]
                    idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == chave_res].tolist()[0]
                    st.session_state.df_base.at[idx, 'Status'] = 'Pendente'
                    salvar_base()
                    st.rerun()
