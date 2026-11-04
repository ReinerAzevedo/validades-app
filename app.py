import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gestão de Validades", layout="wide")
st.title("📋 Controle de Validades - Loja 10")

CAMINHO_BASE = "base_validades.csv"
# Adicionada a coluna "Origem" e "Setor de Compra" nativo
COLUNAS_ERP = ['Código Interno', 'GTIN', 'Descrição', 'Data de Validade', 'Data de Entrada', 'Qtde. Recebida', 'Última Venda', 'Estoque Atual', 'Qtde. Validade', 'Setor de Compra']
COLUNAS_APP = ['Chave_ID', 'Preço_Sistema', 'Preço_Oferta', 'Qtde_Real_Vencer', 'Preco_Rebaixa', 'Acao_Tomada', 'Data_Inicio_Acao', 'Status', 'Origem']

def carregar_dados():
    if os.path.exists(CAMINHO_BASE):
        df = pd.read_csv(CAMINHO_BASE)
    else:
        df = pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)
    
    # Preenche a origem de produtos antigos que não tinham essa coluna
    if 'Origem' not in df.columns:
        df['Origem'] = 'Planilha'
        
    # FORÇA AS COLUNAS A ACEITAREM TEXTO (OBJECT) PARA EVITAR ERRO DE TIPAGEM
    for col in COLUNAS_APP + ['Setor de Compra']:
        if col in df.columns:
            df[col] = df[col].astype(object)
            
    return df

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
            itens_novos['Origem'] = 'Planilha'
        
        df_atualizado = pd.concat([df_base, itens_novos]).reset_index()
        
        for col in COLUNAS_APP:
            if col in df_atualizado.columns:
                df_atualizado[col] = df_atualizado[col].astype(object)
                
        df_atualizado.to_csv(CAMINHO_BASE, index=False)
        st.session_state.df_base = df_atualizado 
        return True
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return False

# --- SEÇÃO 1: UPLOAD DE PLANILHAS ---
with st.expander("📂 Atualizar Base via ERP (Upload)"):
    arquivos = st.file_uploader("Selecione os relatórios", accept_multiple_files=True)
    if arquivos and st.button("Processar e Atualizar Base"):
        with st.spinner("Consolidando dados..."):
            if atualizar_base_cumulativa(arquivos):
                st.success("Base atualizada! Pode fechar esta aba.")
                st.rerun()

# --- SEÇÃO 2: ADIÇÃO MANUAL DE PRODUTOS ---
with st.expander("➕ Adicionar Produto Manual (Fora do Sistema)"):
    st.info("💡 **Dica para múltiplas validades:** Bipe o produto, preencha os dados e clique em salvar. Depois, basta alterar apenas a data e a quantidade e clicar em salvar novamente para registrar o outro lote!")
    
    with st.form("form_manual", clear_on_submit=False):
        codigo_manual = st.text_input("Bipe o Código de Barras (Teclado) ou digite o Código Interno:")
        descricao_manual = st.text_input("Descrição do Produto:")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            validade_manual = st.date_input("Data de Validade")
            qtde_manual = st.number_input("Quantidade na Gôndola", min_value=1, step=1)
            preco_atual_manual = st.number_input("Preço Atual (R$)", min_value=0.0, format="%.2f")
            
        with col_m2:
            setor_manual = st.selectbox("Setor", ["Mercearia", "Perecíveis", "Açougue", "Padaria", "FLV", "Outros"])
            acao_manual = st.selectbox("Ação a Tomar", ["Registrar como Pendente", "Rebaixa", "Descarte", "Troca", "Nenhuma - OK"])
            preco_rebaixa_manual = st.number_input("Preço Rebaixa (Se houver)", min_value=0.0, format="%.2f")
            
        foto_manual = st.file_uploader("📸 Foto (Opcional)", type=['jpg', 'jpeg', 'png'], key="foto_manual")
        
        btn_salvar_manual = st.form_submit_button("Salvar Produto na Base")
        
        if btn_salvar_manual:
            if not codigo_manual or not descricao_manual:
                st.error("⚠️ Código e Descrição são obrigatórios!")
            else:
                cod_limpo = codigo_manual.strip()
                data_val_str = validade_manual.strftime('%Y-%m-%d')
                chave_manual = f"{cod_limpo}_{data_val_str}"
                
                status_final_manual = "Pendente" if acao_manual == "Registrar como Pendente" else ("Em Andamento" if acao_manual == "Rebaixa" else "Concluído")
                
                novo_item = {
                    'Chave_ID': chave_manual,
                    'Código Interno': cod_limpo,
                    'GTIN': cod_limpo,
                    'Descrição': descricao_manual,
                    'Data de Validade': data_val_str,
                    'Qtde. Validade': qtde_manual, 
                    'Qtde_Real_Vencer': qtde_manual,
                    'Preço_Sistema': preco_atual_manual,
                    'Preco_Rebaixa': preco_rebaixa_manual,
                    'Setor de Compra': setor_manual,
                    'Acao_Tomada': acao_manual if acao_manual != "Registrar como Pendente" else None,
                    'Status': status_final_manual,
                    'Origem': 'Manual'
                }
                
                df_nova_linha = pd.DataFrame([novo_item])
                df_nova_linha.set_index('Chave_ID', inplace=True)
                
                df_b = st.session_state.df_base.copy()
                if 'Chave_ID' in df_b.columns:
                    df_b.set_index('Chave_ID', inplace=True)
                
                # Atualiza se a chave já existir ou anexa no final se for nova
                if chave_manual in df_b.index:
                    df_b.update(df_nova_linha)
                else:
                    df_b = pd.concat([df_b, df_nova_linha])
                    
                df_b.reset_index().to_csv(CAMINHO_BASE, index=False)
                st.session_state.df_base = carregar_dados() 
                st.success("✅ Produto adicionado à base com sucesso!")
                st.rerun()

# --- SEÇÃO 3: AÇÃO NO CHÃO DE LOJA ---
st.divider()
st.header("📱 Ação no Chão de Loja")

df_full = st.session_state.df_base

if not df_full.empty:
    pendentes = df_full[df_full['Status'] == 'Pendente']
    st.metric("Itens Pendentes de Ação", len(pendentes))
    
    if not pendentes.empty:
        with st.expander("Ver Tabela de Pendências"):
            # Agora mostra a origem para a equipe saber se veio do ERP ou foi digitado
            st.dataframe(pendentes[['Código Interno', 'Descrição', 'Data de Validade', 'Qtde. Validade', 'Origem']])
        
        st.markdown("### 🔍 Localizar Produto para Auditar")
        
        busca = st.text_input("Bipe o GTIN com o teclado do celular ou digite o Código Interno:")
        
        if busca:
            busca_limpa = busca.strip()
            mask_codigo = pendentes['Código Interno'].astype(str) == busca_limpa
            mask_gtin = pendentes['GTIN'].astype(str).str.replace('.0', '', regex=False) == busca_limpa
            pendentes_filtrado = pendentes[mask_codigo | mask_gtin]
        else:
            pendentes_filtrado = pendentes.head(30)
            if len(pendentes) > 30:
                st.caption("Mostrando apenas os 30 itens mais urgentes.")
            
        if pendentes_filtrado.empty and busca != "":
            st.warning("Nenhum produto pendente encontrado com este código.")
        elif not pendentes_filtrado.empty:
            opcoes_produtos = pendentes_filtrado['Chave_ID'].astype(str) + " | " + pendentes_filtrado['Descrição'].astype(str)
            produto_selecionado = st.selectbox("Selecione o vencimento para auditar:", opcoes_produtos.tolist())
            
            if produto_selecionado:
                chave_atual = produto_selecionado.split(" | ")[0]
                item_atual = pendentes_filtrado[pendentes_filtrado['Chave_ID'] == chave_atual].iloc[0]
                
                origem_tag = "🎯 ERP" if item_atual['Origem'] == 'Planilha' else "✋ Manual"
                st.info(f"**Vencimento:** {item_atual['Data de Validade']} | **Saldo Projetado:** {item_atual['Qtde. Validade']} un | **Origem:** {origem_tag}")
                
                with st.form(key="form_acao"):
                    col1, col2 = st.columns(2)
                    with col1:
                        qtde_projetada = int(item_atual['Qtde. Validade']) if pd.notna(item_atual['Qtde. Validade']) else 0
                        qtde_real = st.number_input("Qtd Física Real", min_value=0, step=1, value=qtde_projetada)
                        acao = st.selectbox("Ação a Tomar", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"])
                    with col2:
                        preco_rebaixa = st.number_input("Preço Rebaixa (R$)", min_value=0.0, format="%.2f")
                        data_acao = st.date_input("Data de Início")
                    
                    foto = st.file_uploader("📸 Capturar Imagem da Ação (Opcional)", type=['jpg', 'jpeg', 'png'])
                    btn_salvar = st.form_submit_button("Salvar Ação")
                    
                    if btn_salvar:
                        for col in ['Acao_Tomada', 'Status', 'Data_Inicio_Acao']:
                            st.session_state.df_base[col] = st.session_state.df_base[col].astype(object)

                        if acao == "Resolvido - Sem Estoque Físico":
                            qtde_real = 0
                            status_final = "Concluído"
                        else:
                            status_final = "Em Andamento" if acao == "Rebaixa" else "Concluído"
                        
                        idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == chave_atual].tolist()[0]
                        st.session_state.df_base.at[idx, 'Qtde_Real_Vencer'] = qtde_real
                        st.session_state.df_base.at[idx, 'Preco_Rebaixa'] = preco_rebaixa
                        st.session_state.df_base.at[idx, 'Acao_Tomada'] = acao
                        st.session_state.df_base.at[idx, 'Data_Inicio_Acao'] = data_acao.strftime('%Y-%m-%d')
                        st.session_state.df_base.at[idx, 'Status'] = status_final
                        
                        st.session_state.df_base.to_csv(CAMINHO_BASE, index=False)
                        st.success("Ação registada com sucesso!")
                        st.rerun()
    else:
        st.success("🎉 Tudo limpo! Não há itens pendentes.")
else:
    st.info("A base de dados está vazia. Expanda o menu superior para fazer o upload dos arquivos ou adicione produtos manualmente.")
