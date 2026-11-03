import pandas as pd
import os

# 1. Definir as colunas que vêm do ERP Bluesoft e as colunas do seu App
COLUNAS_ERP = [
    'Código Interno', 'GTIN', 'Descrição', 'Data de Validade', 
    'Data de Entrada', 'Qtde. Recebida', 'Última Venda', 
    'Estoque Atual', 'Qtde. Validade', 'Setor de Compra'
]

COLUNAS_APP = [
    'Chave_ID', 'Preço_Sistema', 'Preço_Oferta', # Campos que não vêm neste relatório
    'Qtde_Real_Vencer', 'Preco_Rebaixa', 'Acao_Tomada', 
    'Data_Inicio_Acao', 'Status' # Pendente, Em Andamento, Concluído
]

def processar_relatorio_bluesoft(caminho_arquivo):
    """Lê o arquivo bruto, limpa o cabeçalho e seleciona as colunas úteis."""
    # O cabeçalho real no Bluesoft começa na linha 28 (índice 27)
    df = pd.read_excel(caminho_arquivo, header=27)
    
    # Filtrar apenas as colunas que existem no relatório
    df = df[COLUNAS_ERP].copy()
    
    # Remover linhas vazias (totalizadores do Excel)
    df.dropna(subset=['Código Interno', 'Data de Validade'], inplace=True)
    
    # Criar a Chave Única: Código + Data de Validade (formatada como string)
    df['Código Interno'] = df['Código Interno'].astype(int).astype(str)
    df['Data de Validade'] = pd.to_datetime(df['Data de Validade']).dt.strftime('%Y-%m-%d')
    df['Chave_ID'] = df['Código Interno'] + "_" + df['Data de Validade']
    
    return df

def atualizar_base_cumulativa(caminhos_novos_arquivos, caminho_base_atual="base_validades.csv"):
    """Funde os novos relatórios com a base histórica sem perder os dados digitados."""
    
    # 1. Processar e consolidar os novos arquivos (ex: Mercearia e Perecíveis)
    lista_dfs = [processar_relatorio_bluesoft(arq) for arq in caminhos_novos_arquivos]
    df_novo = pd.concat(lista_dfs, ignore_index=True)
    
    # 2. Carregar a base atual do sistema (se já existir)
    if os.path.exists(caminho_base_atual):
        df_base = pd.read_csv(caminho_base_atual)
    else:
        # Se for o primeiro uso, cria a base vazia com as colunas do ERP + APP
        df_base = pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)
        df_base.set_index('Chave_ID', inplace=True)
    
    # Garantir que a Chave_ID seja o índice para facilitar a mesclagem
    if 'Chave_ID' in df_base.columns:
        df_base.set_index('Chave_ID', inplace=True)
    df_novo.set_index('Chave_ID', inplace=True)
    
    # 3. Lógica de Atualização (Update e Insert)
    # Atualiza dados do ERP nos itens que já existem na base (ex: Estoque Atual pode ter caído)
    df_base.update(df_novo)
    
    # Identifica os itens novos que estão na planilha enviada, mas não na base
    itens_novos = df_novo[~df_novo.index.isin(df_base.index)].copy()
    
    # Adiciona colunas do APP vazias ou com status padrão para os itens novos
    for col in COLUNAS_APP:
        if col not in itens_novos.columns and col != 'Chave_ID':
            itens_novos[col] = None
    if not itens_novos.empty:
        itens_novos['Status'] = 'Pendente'
    
    # Adiciona os itens novos à base principal
    df_atualizado = pd.concat([df_base, itens_novos])
    
    # Opcional: Se um item está na base com status 'Pendente' mas sumiu do novo relatório do ERP 
    # (porque foi vendido/descartado e zerou no Bluesoft), você pode automatizar a baixa:
    # df_atualizado.loc[(~df_atualizado.index.isin(df_novo.index)) & (df_atualizado['Status'] == 'Pendente'), 'Status'] = 'Baixa Automática ERP'
    
    # 4. Salvar a base atualizada
    df_atualizado.reset_index().to_csv(caminho_base_atual, index=False)
    
    return df_atualizado

# Exemplo de uso no seu Streamlit:
# arquivos_upados = ['Relatorio (49).xlsx', 'Relatorio (50).xlsx']
# base_pronta = atualizar_base_cumulativa(arquivos_upados)