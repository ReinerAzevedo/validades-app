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
                st.divider()
                st.header("📱 Ação no Chão de Loja")
                
                # Cria uma lista amigável para o usuário selecionar o produto pendente
                opcoes_produtos = pendentes['Chave_ID'].astype(str) + " | " + pendentes['Descrição'].astype(str)
                produto_selecionado = st.selectbox("Selecione o produto para auditar:", opcoes_produtos.tolist())
                
                if produto_selecionado:
                    # Extrai a Chave_ID da string selecionada
                    chave_atual = produto_selecionado.split(" | ")[0]
                    item_atual = pendentes[pendentes['Chave_ID'] == chave_atual].iloc[0]
                    
                    st.info(f"**Vencimento ERP:** {item_atual['Data de Validade']} | **Saldo ERP:** {item_atual['Qtde. Validade']} un")
                    
                    # Formulário de Ação Rápida
                    with st.form(key=f"form_acao"):
                        col1, col2 = st.columns(2)
                        with col1:
                            qtde_real = st.number_input("Qtd Real na Gôndola", min_value=0, step=1)
                            acao = st.selectbox("Ação a Tomar", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK"])
                        with col2:
                            preco_rebaixa = st.number_input("Preço Rebaixa (R$)", min_value=0.0, format="%.2f")
                            data_acao = st.date_input("Data de Início")
                        
                        # Ativa a câmera nativa do smartphone
                        foto = st.camera_input("Capturar Imagem (Opcional)")
                        
                        btn_salvar = st.form_submit_button("Salvar Ação")
                        
                        if btn_salvar:
                            # Carrega a base, atualiza os dados inseridos e salva
                            df_full = pd.read_csv("base_validades.csv", index_col="Chave_ID")
                            
                            df_full.at[chave_atual, 'Qtde_Real_Vencer'] = qtde_real
                            df_full.at[chave_atual, 'Preco_Rebaixa'] = preco_rebaixa
                            df_full.at[chave_atual, 'Acao_Tomada'] = acao
                            df_full.at[chave_atual, 'Data_Inicio_Acao'] = data_acao
                            df_full.at[chave_atual, 'Status'] = "Em Andamento" if acao == "Rebaixa" else "Concluído"
                            
                            # (Opcional) A foto fica em memória no objeto 'foto'. 
                            # Para salvar no disco ou banco, implementaríamos a rotina do Pillow (PIL) aqui.
                            
                            df_full.reset_index().to_csv("base_validades.csv", index_col=False)
                            st.success("Ação registrada com sucesso!")
                            st.rerun() # Atualiza a tela para remover o item da lista de pendentes
