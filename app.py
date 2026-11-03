import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gestão de Validades", layout="wide")
st.title("📋 Controle de Validades - Loja 10")

# 1. Definir as colunas
COLUNAS_ERP = [
    'Código Interno', 'GTIN', 'Descrição', 'Data de Validade', 
    'Data de Entrada', 'Qtde. Recebida', 'Última Venda', 
    'Estoque Atual', 'Qtde. Validade', 'Setor de Compra'
]

COLUNAS_APP = [
    'Chave_ID', 'Preço_Sistema', 'Preço_Oferta',
    'Qtde_Real_Vencer', 'Preco_Rebaixa', 'Acao_Tomada', 
    'Data_Inicio_Acao', 'Status'
]

CAMINHO_BASE = "base_validades.csv"

def processar_relatorio_bluesoft(arquivo):
    try:
        df = pd.read_excel(arquivo, header=27)
        df = df[COLUNAS_ERP].copy()
        
        df.dropna(subset=['Código Interno', 'Data de Validade'], inplace=True)
        df['Código Interno'] = pd.to_numeric(df['Código Interno'], errors='coerce').fillna(0).astype(int).astype(str)
        df['Data de Validade'] = pd.to_datetime(df['Data de Validade']).dt.strftime('%Y-%m-%d')
        df['Chave_ID'] = df['Código Interno'] + "_" + df['Data de Validade']
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo {arquivo.name}. Detalhe: {e}")
        return pd.DataFrame() 

def atualizar_base_cumulativa(arquivos_upados):
    lista_dfs = [processar_relatorio_bluesoft(arq) for arq in arquivos_upados]
    lista_dfs = [df for df in lista_dfs if not df.empty]
    
    if not lista_dfs:
        return None

    df_novo = pd.concat(lista_dfs, ignore_index=True)
    df_novo = df_novo.drop_duplicates(subset=['Chave_ID'], keep='first')
    
    if os.path.exists(CAMINHO_BASE):
        df_base = pd.read_csv(CAMINHO_BASE)
    else:
        df_base = pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)
    
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
    
    df_atualizado = pd.concat([df_base, itens_novos])
    df_atualizado.reset_index().to_csv(CAMINHO_BASE, index=False)
    
    return df_atualizado


# --- SEÇÃO 1: UPLOAD (Fica dentro de um menu expansível para não poluir o telemóvel) ---
with st.expander("📂 Atualizar Base de Dados (Upload do ERP)"):
    st.write("Faça o upload dos relatórios de validade do Bluesoft.")
    arquivos = st.file_uploader("Selecione os relatórios", accept_multiple_files=True)
    
    if arquivos:
        if st.button("Processar e Atualizar Base"):
            with st.spinner("Consolidando dados..."):
                base = atualizar_base_cumulativa(arquivos)
                if base is not None:
                    st.success("Base atualizada com sucesso! Pode fechar esta aba.")
                else:
                    st.warning("Nenhum dado válido foi encontrado.")

# --- SEÇÃO 2: AÇÃO NO CHÃO DE LOJA (Carrega automaticamente se a base existir) ---
st.divider()
st.header("📱 Ação no Chão de Loja")

if os.path.exists(CAMINHO_BASE):
    df_full = pd.read_csv(CAMINHO_BASE)
    
    # Filtra apenas os pendentes para exibir na tela
    pendentes = df_full[df_full['Status'] == 'Pendente']
    
    st.subheader(f"Itens Pendentes de Ação: {len(pendentes)}")
    
    if not pendentes.empty:
        # Exibe a tabela
        st.dataframe(pendentes)
        
        # Menu de seleção
        opcoes_produtos = pendentes['Chave_ID'].astype(str) + " | " + pendentes['Descrição'].astype(str)
        produto_selecionado = st.selectbox("Selecione o produto para auditar:", opcoes_produtos.tolist())
        
        if produto_selecionado:
            chave_atual = produto_selecionado.split(" | ")[0]
            item_atual = pendentes[pendentes['Chave_ID'] == chave_atual].iloc[0]
            
            st.info(f"**Vencimento ERP:** {item_atual['Data de Validade']} | **Saldo ERP:** {item_atual['Qtde. Validade']} un")
            
            # Formulário isolado
            with st.form(key="form_acao"):
                col1, col2 = st.columns(2)
                with col1:
                    qtde_real = st.number_input("Qtd Real na Gôndola", min_value=0, step=1)
                    acao = st.selectbox("Ação a Tomar", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK"])
                with col2:
                    preco_rebaixa = st.number_input("Preço Rebaixa (R$)", min_value=0.0, format="%.2f")
                    data_acao = st.date_input("Data de Início")
                
                foto = st.camera_input("Capturar Imagem (Opcional)")
                btn_salvar = st.form_submit_button("Salvar Ação")
                
                if btn_salvar:
                    # Carrega a base limpa para atualizar e salvar
                    df_atualizar = pd.read_csv(CAMINHO_BASE, index_col="Chave_ID")
                    
                    df_atualizar.at[chave_atual, 'Qtde_Real_Vencer'] = qtde_real
                    df_atualizar.at[chave_atual, 'Preco_Rebaixa'] = preco_rebaixa
                    df_atualizar.at[chave_atual, 'Acao_Tomada'] = acao
                    df_atualizar.at[chave_atual, 'Data_Inicio_Acao'] = data_acao.strftime('%Y-%m-%d')
                    df_atualizar.at[chave_atual, 'Status'] = "Em Andamento" if acao == "Rebaixa" else "Concluído"
                    
                    df_atualizar.reset_index().to_csv(CAMINHO_BASE, index_col=False)
                    st.success("Ação registada com sucesso!")
                    st.rerun() # Atualiza a tela instantaneamente
    else:
        st.success("🎉 Tudo limpo! Não há itens pendentes.")
else:
    st.info("A base de dados está vazia. Expanda o menu superior para fazer o upload dos arquivos.")
