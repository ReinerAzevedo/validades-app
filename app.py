import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gestão de Validades", layout="wide")
st.title("📋 Controle de Validades - Loja 10")
st.write("Faça o upload dos relatórios de validade do Bluesoft.")

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

def processar_relatorio_bluesoft(arquivo):
    try:
        # Lê a planilha assumindo que o cabeçalho real está na linha 28
        df = pd.read_excel(arquivo, header=27)
        df = df[COLUNAS_ERP].copy()
        
        # Limpeza e formatação
        df.dropna(subset=['Código Interno', 'Data de Validade'], inplace=True)
        
        # Tratamento robusto para remover casas decimais perdidas do Excel
        df['Código Interno'] = pd.to_numeric(df['Código Interno'], errors='coerce').fillna(0).astype(int).astype(str)
        
        df['Data de Validade'] = pd.to_datetime(df['Data de Validade']).dt.strftime('%Y-%m-%d')
        df['Chave_ID'] = df['Código Interno'] + "_" + df['Data de Validade']
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo {arquivo.name}. Verifique se é o relatório correto. Detalhe: {e}")
        return pd.DataFrame() 

def atualizar_base_cumulativa(arquivos_upados, caminho_base="base_validades.csv"):
    lista_dfs = [processar_relatorio_bluesoft(arq) for arq in arquivos_upados]
    
    # Remove planilhas que deram erro e retornaram vazias
    lista_dfs = [df for df in lista_dfs if not df.empty]
    
    if not lista_dfs:
        return None

    df_novo = pd.concat(lista_dfs, ignore_index=True)
    
    # Remove linhas duplicadas para não gerar o ValueError de indexação
    df_novo = df_novo.drop_duplicates(subset=['Chave_ID'], keep='first')
    
    if os.path.exists(caminho_base):
        df_base = pd.read_csv(caminho_base)
    else:
        df_base = pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)
    
    if 'Chave_ID' in df_base.columns:
        df_base.set_index('Chave_ID', inplace=True)
    df_novo.set_index('Chave_ID', inplace=True)
    
    # === A CORREÇÃO DE TIPOS ESTÁ AQUI ===
    # Convertendo colunas em comum para "object" para flexibilizar o Update
    for col in df_novo.columns:
        if col in df_base.columns:
            df_base[col] = df_base[col].astype(object)
            df_novo[col] = df_novo[col].astype(object)
            
    # Atualiza dados existentes e mantém o histórico de interações do aplicativo
    df_base.update(df_novo)
    
    # Separa apenas as linhas que são novidade
    itens_novos = df_novo[~df_novo.index.isin(df_base.index)].copy()
    for col in COLUNAS_APP:
        if col not in itens_novos.columns and col != 'Chave_ID':
            itens_novos[col] = None
            
    if not itens_novos.empty:
        itens_novos['Status'] = 'Pendente'
    
    # Junta o histórico com os itens novos
    df_atualizado = pd.concat([df_base, itens_novos])
    df_atualizado.reset_index().to_csv(caminho_base, index=False)
    
    return df_atualizado

# 2. Interface de Upload no Streamlit
arquivos = st.file_uploader("Selecione os relatórios exportados do ERP", accept_multiple_files=True)

if arquivos:
    if st.button("Processar e Atualizar Base"):
        with st.spinner("Consolidando dados..."):
            base = atualizar_base_cumulativa(arquivos)
            
            if base is not None:
                st.success("Base atualizada com sucesso!")
                
                # Filtra e exibe apenas as pendências na tela
                pendentes = base[base['Status'] == 'Pendente']
                st.subheader(f"Itens Pendentes de Ação: {len(pendentes)}")
                st.dataframe(pendentes)
            else:
                st.warning("Nenhum dado válido foi encontrado. Verifique os arquivos.")
