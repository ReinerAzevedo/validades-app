import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title="Gestão de Validades", layout="wide")

# CSS Estrutural Avançado
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: bold !important;
        border: none !important;
        padding: 6px 4px !important;
        font-size: 13px !important;
        width: 100%;
        transition: 0.2s;
    }
    
    div.element-container:has(.cor-marcador) { display: none !important; }
    
    div.element-container:has(.btn-limpar) + div.element-container button { background-color: #2c3e50 !important; color: white !important; margin-bottom: 5px; }
    
    div.element-container:has(.btn-todos) + div.element-container button { background-color: #7f8c8d !important; color: white !important; }
    div.element-container:has(.btn-vencidos) + div.element-container button { background-color: #e74c3c !important; color: white !important; }
    div.element-container:has(.btn-proximos) + div.element-container button { background-color: #f1c40f !important; color: black !important; }
    div.element-container:has(.btn-noprazo) + div.element-container button { background-color: #3498db !important; color: white !important; }
    
    div.element-container:has(.btn-pendentes) + div.element-container button { background-color: #e67e22 !important; color: white !important; }
    div.element-container:has(.btn-conferidos) + div.element-container button { background-color: #9b59b6 !important; color: white !important; }
    div.element-container:has(.btn-resolvidos) + div.element-container button { background-color: #2ecc71 !important; color: white !important; }
    
    div.element-container:has(.btn-reativar) + div.element-container button { background-color: #e67e22 !important; color: white !important; border: 1px solid #d35400 !important; }
    
    div.element-container:has(.btn-fab) + div.element-container button {
        background-color: #05cd9e !important;
        color: white !important;
        font-size: 24px !important;
        border-radius: 50px !important;
        box-shadow: 0px 4px 10px rgba(5, 205, 158, 0.4) !important;
        height: 50px !important;
    }
    
    div.stButton > button:active { opacity: 0.7 !important; }
</style>
""", unsafe_allow_html=True)

st.title("🟩 PRO - Validades Loja 10")

CAMINHO_BASE = "base_validades.csv"
COLUNAS_ERP = ['Código Interno', 'GTIN', 'Descrição', 'Data de Validade', 'Data de Entrada', 'Qtde. Recebida', 'Última Venda', 'Estoque Atual', 'Qtde. Validade', 'Setor de Compra']
COLUNAS_APP = ['Chave_ID', 'Preço_Sistema', 'Preço_Oferta', 'Qtde_Real_Vencer', 'Preco_Rebaixa', 'Acao_Tomada', 'Data_Inicio_Acao', 'Status', 'Origem', 'Data_Conferencia', 'Observacoes', 'Operador', 'Historico_Log']

def carregar_dados():
    if os.path.exists(CAMINHO_BASE):
        df = pd.read_csv(CAMINHO_BASE)
        if 'Código Interno' in df.columns:
            df['Código Interno'] = df['Código Interno'].astype(str).str.strip().str.replace('.0', '', regex=False)
        if 'GTIN' in df.columns:
            df['GTIN'] = df['GTIN'].astype(str).str.strip().str.replace('.0', '', regex=False)
    else:
        df = pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)
    
    if 'Origem' not in df.columns: df['Origem'] = 'Planilha'
    if 'Data_Conferencia' not in df.columns: df['Data_Conferencia'] = None
    if 'Observacoes' not in df.columns: df['Observacoes'] = None
    if 'Operador' not in df.columns: df['Operador'] = None
    if 'Historico_Log' not in df.columns: df['Historico_Log'] = None
        
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

def atualizar_base_cumulativa(arquivos_upados):
    try:
        lista_dfs = []
        for arq in arquivos_upados:
            df = pd.read_excel(arq, header=27)
            df = df[COLUNAS_ERP].copy()
            df.dropna(subset=['Código Interno', 'Data de Validade'], inplace=True)
            
            df['Código Interno'] = df['Código Interno'].astype(str).str.strip().str.replace('.0', '', regex=False)
            if 'GTIN' in df.columns:
                df['GTIN'] = df['GTIN'].astype(str).str.strip().str.replace('.0', '', regex=False)
                
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

if 'filtro_atual' not in st.session_state: st.session_state.filtro_atual = "Todos"
if 'funil_atual' not in st.session_state: st.session_state.funil_atual = "1️⃣ Pendentes"
if 'mostrar_add' not in st.session_state: st.session_state.mostrar_add = False

# --- TOP BAR: IDENTIFICAÇÃO DO OPERADOR ---
col_op1, col_op2 = st.columns([2, 3])
with col_op1:
    operador_atual = st.text_input("👤 Nome / Matrícula do Operador:", value=st.session_state.get('operador_nome', ''), placeholder="Ex: João / Matrícula")
    if operador_atual:
        st.session_state.operador_nome = operador_atual.strip()
    else:
        st.session_state.operador_nome = "Não Identificado"

# --- TOP BAR: UPLOAD DO ERP ---
with st.expander("📂 Importar Planilha do ERP (Bluesoft)"):
    arquivos = st.file_uploader("Relatórios Excel", accept_multiple_files=True)
    if arquivos and st.button("Carregar Dados"):
        with st.spinner("Consolidando dados do ERP..."):
            if atualizar_base_cumulativa(arquivos):
                st.success("Base de dados atualizada com sucesso!")
                st.rerun()

# --- TOP BAR: RELATÓRIOS E EXPORTAÇÃO DIÁRIA (COM BACKUP COMPLETO) ---
with st.expander("📥 Relatórios Diários e Backup"):
    hoje_str = pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y')
    if not st.session_state.df_base.empty:
        df_dia = st.session_state.df_base[
            (st.session_state.df_base['Data_Conferencia'].astype(str).str.startswith(hoje_str)) &
            (st.session_state.df_base['Status'].isin(['Conferido', 'Resolvido']))
        ].copy()
        
        st.metric(f"Itens Auditados Hoje ({hoje_str})", len(df_dia))
        
        if not df_dia.empty:
            col_ex1, col_ex2, col_ex3 = st.columns(3)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_dia.to_excel(writer, index=False, sheet_name='Validades_Hoje')
            excel_data = output.getvalue()
            
            with col_ex1:
                st.download_button(label="📊 Exportar Excel Hoje", data=excel_data, file_name=f"validades_conferidas_{hoje_str.replace('/','-')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            
            html_content = f"""
            <html><head><meta charset="utf-8"><style>
                body {{ font-family: 'Segoe UI', sans-serif; background-color: #f9f9f9; padding: 20px; }}
                .header {{ background-color: #0c1a15; color: white; padding: 20px; text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; background-color: white; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #05cd9e; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .codigo {{ font-weight: bold; color: #2c3e50; }}
            </style></head><body>
            <div class="header"><h2>📋 Relatório de Validades - {hoje_str}</h2></div>
            <table><tr><th>GTIN</th><th>Cód. Interno</th><th>Descrição</th><th>Vencimento</th><th>Qtd Sistema</th><th>Qtd Real</th><th>Ação</th><th>Preço Rebaixa</th><th>Operador</th><th>Obs</th></tr>
            """
            for _, row in df_dia.iterrows():
                obs_text = row['Observacoes'] if pd.notna(row['Observacoes']) and row['Observacoes'] else "-"
                op_text = row['Operador'] if pd.notna(row['Operador']) and row['Operador'] else "-"
                prec_reb_txt = f"R$ {float(row['Preco_Rebaixa']):.2f}" if pd.notna(row['Preco_Rebaixa']) and float(row['Preco_Rebaixa']) > 0 else "-"
                gtin_txt = row['GTIN'] if pd.notna(row['GTIN']) else "-"
                html_content += f"<tr><td class='codigo'>{gtin_txt}</td><td>{row['Código Interno']}</td><td>{row['Descrição']}</td><td>{row['Data de Validade']}</td><td>{row['Qtde. Validade']}</td><td>{row['Qtde_Real_Vencer']}</td><td>{row['Acao_Tomada']}</td><td>{prec_reb_txt}</td><td>{op_text}</td><td>{obs_text}</td></tr>"
            html_content += "</table></body></html>"
            
            with col_ex2:
                st.download_button(label="🌐 Exportar HTML Visual", data=html_content, file_name=f"relatorio_validades_{hoje_str.replace('/','-')}.html", mime="text/html", use_container_width=True)
                
            csv_backup = st.session_state.df_base.to_csv(index=False).encode('utf-8')
            with col_ex3:
                st.download_button(label="💾 Backup Completo (CSV)", data=csv_backup, file_name=f"backup_base_validades_{hoje_str.replace('/','-')}.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("Nenhum item finalizado hoje. Mas pode descarregar o backup completo da base se desejar.")
            csv_backup = st.session_state.df_base.to_csv(index=False).encode('utf-8')
            st.download_button(label="💾 Baixar Backup Completo da Base (CSV)", data=csv_backup, file_name=f"backup_base_validades_{hoje_str.replace('/','-')}.csv", mime="text/csv")
    else:
        st.info("A base de dados está vazia.")

# --- TOP BAR: PAINEL ADMINISTRATIVO (PROTEGIDO POR SENHA) ---
with st.expander("🔒 Painel Administrativo (Excluir Registros / Limpar Base)"):
    senha_adm = st.text_input("Digite a senha de administrador:", type="password")
    if senha_adm == "1010":
        st.success("🔓 Acesso Autorizado!")
        
        if st.button("🧹 Limpar Histórico e Manter Apenas o Cadastro de Produtos"):
            if not st.session_state.df_base.empty:
                df_atual = st.session_state.df_base.copy()
                df_mestre = df_atual[['Código Interno', 'GTIN', 'Descrição', 'Setor de Compra', 'Origem']].drop_duplicates(subset=['Código Interno']).copy()
                df_mestre['Data de Validade'] = pd.Timestamp.today().strftime('%Y-%m-%d')
                df_mestre['Chave_ID'] = df_mestre['Código Interno'].astype(str) + "_" + df_mestre['Data de Validade']
                df_mestre['Status'] = 'Pendente'
                df_mestre['Qtde. Validade'] = 1
                
                for col in COLUNAS_ERP + COLUNAS_APP:
                    if col not in df_mestre.columns:
                        df_mestre[col] = None
                
                st.session_state.df_base = df_mestre[COLUNAS_ERP + COLUNAS_APP]
                salvar_base()
                st.success("✅ Histórico limpo! Mantido apenas o cadastro mestre dos produtos.")
                st.rerun()
            else:
                st.warning("A base já está vazia.")

        st.divider()

        if st.button("🗑️ Apagar Toda a Base de Dados (Zero Absoluto)", type="primary"):
            st.session_state.df_base = pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)
            if os.path.exists(CAMINHO_BASE):
                os.remove(CAMINHO_BASE)
            st.success("Base de dados totalmente limpa!")
            st.rerun()
            
        st.divider()
        
        if not st.session_state.df_base.empty:
            st.write("Excluir item específico por Chave_ID:")
            item_para_apagar = st.selectbox("Selecione o item:", st.session_state.df_base['Chave_ID'].astype(str) + " | " + st.session_state.df_base['Descrição'].astype(str))
            if st.button("❌ Excluir Item Selecionado"):
                chave_alvo = item_para_apagar.split(" | ")[0]
                st.session_state.df_base = st.session_state.df_base[st.session_state.df_base['Chave_ID'] != chave_alvo]
                salvar_base()
                st.success(f"Item {chave_alvo} apagado com sucesso!")
                st.rerun()
    elif senha_adm != "":
        st.error("❌ Senha incorreta.")

# --- CÁLCULO DOS TOTAIS PARA OS BOTÕES ---
df_base_calc = st.session_state.df_base.copy()
hoje = pd.to_datetime('today').normalize()

if not df_base_calc.empty:
    df_base_calc['Data de Validade'] = pd.to_datetime(df_base_calc['Data de Validade'], errors='coerce')
    
    tot_pendentes = len(df_base_calc[df_base_calc['Status'] == 'Pendente'])
    tot_conferidos = len(df_base_calc[df_base_calc['Status'] == 'Conferido'])
    tot_resolvidos = len(df_base_calc[df_base_calc['Status'] == 'Resolvido'])
    
    tot_todos = len(df_base_calc)
    tot_vencidos = len(df_base_calc[df_base_calc['Data de Validade'] < hoje])
    tot_proximos = len(df_base_calc[(df_base_calc['Data de Validade'] >= hoje) & (df_base_calc['Data de Validade'] <= hoje + pd.Timedelta(days=30))])
    tot_noprazo = len(df_base_calc[df_base_calc['Data de Validade'] > hoje + pd.Timedelta(days=30)])
else:
    tot_pendentes = tot_conferidos = tot_resolvidos = tot_todos = tot_vencidos = tot_proximos = tot_noprazo = 0

# --- BOTÃO: LIMPAR FILTROS ---
col_limpar, col_vazia = st.columns([1, 1])
with col_limpar:
    st.markdown('<span class="cor-marcador btn-limpar"></span>', unsafe_allow_html=True)
    if st.button("🔄 Limpar Filtros", use_container_width=True):
        st.session_state.filtro_atual = "Todos"
        st.session_state.funil_atual = "1️⃣ Pendentes"
        st.rerun()

# --- FILTROS DE VALIDADE COM TOTAIS ---
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    st.markdown('<span class="cor-marcador btn-todos"></span>', unsafe_allow_html=True)
    if st.button(f"Todos ({tot_todos})", use_container_width=True): st.session_state.filtro_atual = "Todos"
with col_f2:
    st.markdown('<span class="cor-marcador btn-vencidos"></span>', unsafe_allow_html=True)
    if st.button(f"Vencidos ({tot_vencidos})", use_container_width=True): st.session_state.filtro_atual = "Vencidos"
with col_f3:
    st.markdown('<span class="cor-marcador btn-proximos"></span>', unsafe_allow_html=True)
    if st.button(f"Próximos ({tot_proximos})", use_container_width=True): st.session_state.filtro_atual = "Próximos"
with col_f4:
    st.markdown('<span class="cor-marcador btn-noprazo"></span>', unsafe_allow_html=True)
    if st.button(f"No Prazo ({tot_noprazo})", use_container_width=True): st.session_state.filtro_atual = "No Prazo"

# --- FILTROS DE STATUS / FUNIL COM TOTAIS ---
st.write("")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    st.markdown('<span class="cor-marcador btn-pendentes"></span>', unsafe_allow_html=True)
    if st.button(f"Pendentes ({tot_pendentes})", use_container_width=True): st.session_state.funil_atual = "1️⃣ Pendentes"
with col_c2:
    st.markdown('<span class="cor-marcador btn-conferidos"></span>', unsafe_allow_html=True)
    if st.button(f"Conferidos ({tot_conferidos})", use_container_width=True): st.session_state.funil_atual = "2️⃣ Conferidos"
with col_c3:
    st.markdown('<span class="cor-marcador btn-resolvidos"></span>', unsafe_allow_html=True)
    if st.button(f"Resolvidos ({tot_resolvidos})", use_container_width=True): st.session_state.funil_atual = "3️⃣ Resolvidos"

st.markdown(f"Exibindo: **{st.session_state.funil_atual[4:]}** | Validade: **{st.session_state.filtro_atual}**")

df_full = st.session_state.df_base

if not df_full.empty:
    status_map = {"1️⃣ Pendentes": "Pendente", "2️⃣ Conferidos": "Conferido", "3️⃣ Resolvidos": "Resolvido"}
    dados_filtrados = df_full[df_full['Status'] == status_map[st.session_state.funil_atual]].copy()
    dados_filtrados['Data de Validade'] = pd.to_datetime(dados_filtrados['Data de Validade'], errors='coerce')
    
    if st.session_state.filtro_atual == "Vencidos":
        dados_filtrados = dados_filtrados[dados_filtrados['Data de Validade'] < hoje]
    elif st.session_state.filtro_atual == "Próximos":
        dados_filtrados = dados_filtrados[(dados_filtrados['Data de Validade'] >= hoje) & (dados_filtrados['Data de Validade'] <= hoje + pd.Timedelta(days=30))]
    elif st.session_state.filtro_atual == "No Prazo":
        dados_filtrados = dados_filtrados[dados_filtrados['Data de Validade'] > hoje + pd.Timedelta(days=30)]

    # --- BARRA DE BUSCA PRIORIZANDO O GTIN E BOTÃO ADICIONAR (+) ---
    st.write("")
    col_busca, col_add = st.columns([4, 1])
    with col_busca:
        busca = st.text_input("Busca", placeholder="Bipe o GTIN (código de barras) ou digite a descrição...", label_visibility="collapsed")
    with col_add:
        st.markdown('<span class="cor-marcador btn-fab"></span>', unsafe_allow_html=True)
        if st.button("➕", use_container_width=True):
            st.session_state.mostrar_add = not st.session_state.mostrar_add
            st.rerun()

    # --- BLOCO DE ADIÇÃO MANUAL OTIMIZADO ---
    if st.session_state.mostrar_add:
        st.markdown("### ➕ Adicionar Nova Validade ou Produto")
        st.info("💡 **Dica:** Bipe o GTIN (código de barras). Se o produto já existir, a descrição e o código interno serão preenchidos automaticamente.")
        
        codigo_manual = st.text_input("1️⃣ Bipe o GTIN (Código de Barras):")
        
        desc_padrao, interno_padrao, setor_padrao, preco_padrao = "", "", "Mercearia", 0.0
        if codigo_manual:
            cod_limpo = str(codigo_manual).strip().replace('.0', '')
            df_encontrado = st.session_state.df_base[
                (st.session_state.df_base['GTIN'].astype(str) == cod_limpo) | 
                (st.session_state.df_base['Código Interno'].astype(str) == cod_limpo)
            ]
            if not df_encontrado.empty:
                desc_padrao = str(df_encontrado.iloc[0]['Descrição'])
                interno_padrao = str(df_encontrado.iloc[0]['Código Interno']) if pd.notna(df_encontrado.iloc[0]['Código Interno']) else cod_limpo
                setor_padrao = str(df_encontrado.iloc[0]['Setor de Compra']) if pd.notna(df_encontrado.iloc[0]['Setor de Compra']) else "Mercearia"
                preco_padrao = float(df_encontrado.iloc[0]['Preço_Sistema']) if pd.notna(df_encontrado.iloc[0]['Preço_Sistema']) else 0.0
                st.success(f"✅ Produto reconhecido: **{desc_padrao}**")
        
        with st.form("modal_add"):
            c_gtin = st.text_input("GTIN (Código de Barras Principal):", value=str(codigo_manual).strip().replace('.0', '') if codigo_manual else "")
            c_interno = st.text_input("Código Interno (Complemento):", value=interno_padrao if interno_padrao else (str(codigo_manual).strip().replace('.0', '') if codigo_manual else ""))
            descricao_manual = st.text_input("Descrição do Produto:", value=desc_padrao)
            
            val_manual = st.date_input("2️⃣ Nova Data de Validade")
            q_manual = st.number_input("Quantidade Real (Un)", min_value=0, step=1)
            p_manual = st.number_input("Preço Atual (R$)", min_value=0.0, format="%.2f", value=preco_padrao)
            
            setores = ["Mercearia", "Perecíveis", "Açougue", "Padaria", "FLV", "Outros"]
            idx = setores.index(setor_padrao) if setor_padrao in setores else 0
            setor_m = st.selectbox("Setor", setores, index=idx)
            
            acao_m = st.selectbox("Ação a Tomar", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"])
            preco_reb_manual = st.number_input("Preço da Rebaixa (R$)", min_value=0.0, format="%.2f", value=0.0)
            obs_m = st.text_area("Anotações / Observações (Opcional)")
            
            if st.form_submit_button("Gravar Produto na Base"):
                if acao_m == "Rebaixa" and preco_reb_manual <= 0:
                    st.error("⚠️ Para a ação 'Rebaixa', o preço promocional deve ser maior que zero!")
                elif c_gtin and descricao_manual:
                    c_gtin_limpo = str(c_gtin).strip().replace('.0', '')
                    c_int_limpo = str(c_interno).strip().replace('.0', '') if c_interno else c_gtin_limpo
                    chave = f"{c_int_limpo}_{val_manual.strftime('%Y-%m-%d')}"
                    
                    df_b = st.session_state.df_base.set_index('Chave_ID') if 'Chave_ID' in st.session_state.df_base.columns else st.session_state.df_base
                    
                    if q_manual == 0 or acao_m in ["Nenhuma - OK", "Resolvido - Sem Estoque Físico"]:
                        status_m = "Resolvido"
                        if q_manual == 0: acao_m = "Resolvido - Sem Estoque Físico"
                    else:
                        status_m = "Conferido"
                        
                    data_conf_m = pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y %H:%M')
                    op_nome = st.session_state.get('operador_nome', 'Não Identificado')
                    log_msg = f"[{data_conf_m}] Criado/Auditado por {op_nome} - Ação: {acao_m}"

                    novo_item = {
                        'Chave_ID': chave, 'Código Interno': c_int_limpo, 'GTIN': c_gtin_limpo,
                        'Descrição': descricao_manual, 'Data de Validade': val_manual.strftime('%Y-%m-%d'),
                        'Qtde. Validade': 1, 'Qtde_Real_Vencer': q_manual,
                        'Preço_Sistema': p_manual, 'Setor de Compra': setor_m, 
                        'Acao_Tomada': acao_m, 'Preco_Rebaixa': preco_reb_manual,
                        'Status': status_m, 'Origem': 'Manual', 'Data_Conferencia': data_conf_m, 'Observacoes': obs_m, 'Operador': op_nome, 'Historico_Log': log_msg
                    }
                    
                    df_nova_linha = pd.DataFrame([novo_item]).set_index('Chave_ID')
                    
                    if chave in df_b.index:
                        df_b.update(df_nova_linha)
                        st.session_state.df_base = df_b.reset_index()
                        st.success("⚠️ Este lote já existia na base. Dados atualizados com sucesso!")
                    else:
                        df_b = pd.concat([df_b, df_nova_linha]).reset_index()
                        st.session_state.df_base = df_b
                        st.success("✅ Produto adicionado e encaminhado para conferência!")
                        
                    salvar_base()
                    st.session_state.mostrar_add = False 
                    st.rerun()
                else:
                    st.error("Preencha o GTIN e a Descrição.")
                    
        st.divider()

    # --- LISTAGEM DOS CARDS COM BUSCA PRIORIZANDO GTIN E PAGINAÇÃO ---
    if not dados_filtrados.empty:
        if busca:
            busca_limpa = str(busca).strip().replace('.0', '')
            dados_filtrados = dados_filtrados[
                (dados_filtrados['GTIN'].astype(str) == busca_limpa) | 
                (dados_filtrados['Código Interno'].astype(str) == busca_limpa) |
                (dados_filtrados['Descrição'].astype(str).str.contains(busca_limpa, case=False))
            ]

        codigos_unicos = dados_filtrados['Código Interno'].unique()
        total_produtos = len(codigos_unicos)
        
        itens_por_pagina = 20
        total_paginas = max(1, (total_produtos + itens_por_pagina - 1) // itens_por_pagina)
        
        col_pag1, col_pag2, col_pag3 = st.columns([2, 3, 2])
        with col_pag2:
            pagina_atual = st.number_input("Página", min_value=1, max_value=total_paginas, value=1, step=1, label_visibility="collapsed")
        
        st.caption(f"Mostrando página {pagina_atual} de {total_paginas} (Total de produtos: {total_produtos})")
        
        inicio_idx = (pagina_atual - 1) * itens_por_pagina
        fim_idx = inicio_idx + itens_por_pagina
        codigos_pagina = codigos_unicos[inicio_idx:fim_idx]

        for cod in codigos_pagina:
            lotes_produto = dados_filtrados[dados_filtrados['Código Interno'].astype(str) == str(cod)]
            primeiro_item = lotes_produto.iloc[0]
            
            status_principal = primeiro_item['Status']
            total_lotes = len(lotes_produto)
            
            if status_principal == 'Pendente':
                data_val_prim = pd.to_datetime(primeiro_item['Data de Validade']).normalize()
                if total_lotes == 1 and data_val_prim < hoje:
                    card_bg, text_color = "#e74c3c", "white"
                else:
                    card_bg, text_color = "#e67e22", "white"
            elif status_principal == 'Conferido': 
                card_bg, text_color = "#9b59b6", "white"
            else: 
                card_bg, text_color = "#2ecc71", "white"

            badge_lotes = f"📦 **{total_lotes} lote(s) com datas diferentes**" if total_lotes > 1 else f"📅 Vencimento: {pd.to_datetime(primeiro_item['Data de Validade']).strftime('%d/%m/%Y')}"

            if total_lotes == 1:
                item_u = lotes_produto.iloc[0]
                q_sis = int(item_u['Qtde. Validade']) if pd.notna(item_u['Qtde. Validade']) else 0
                if pd.notna(item_u.get('Qtde_Real_Vencer')) and str(item_u.get('Qtde_Real_Vencer')).strip() != "":
                    q_real_txt = f"{int(float(item_u['Qtde_Real_Vencer']))} un"
                else:
                    q_real_txt = "Pendente contagem física"
                info_qtd_card = f"📊 Qtd Sistema: {q_sis} un | 🔍 Qtd Real: {q_real_txt}"
            else:
                info_qtd_card = f"📦 Múltiplos lotes (ver detalhes abaixo)"

            gtin_card = primeiro_item['GTIN'] if pd.notna(primeiro_item['GTIN']) else "-"
            cod_int_card = primeiro_item['Código Interno']

            st.markdown(f"""
            <div style="background-color: {card_bg}; color: {text_color}; padding: 15px; border-radius: 10px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-size: 16px; font-weight: bold; color: {text_color};">{primeiro_item['Descrição']}</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px; font-weight: 500;">{badge_lotes}</p>
                <p style="margin: 3px 0 0 0; font-size: 13px; font-weight: bold; opacity: 0.95;">{info_qtd_card}</p>
                <p style="margin: 2px 0 0 0; font-size: 12px; opacity: 0.9;">GTIN: <b>{gtin_card}</b> | Cód. Int: {cod_int_card} | Setor: {primeiro_item['Setor de Compra']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"🔍 Gerenciar Lotes / Validades ({total_lotes}) para: {primeiro_item['Descrição'][:30]}..."):
                for _, item in lotes_produto.iterrows():
                    qtd_sistema = int(item['Qtde. Validade']) if pd.notna(item['Qtde. Validade']) else 0
                    
                    if pd.notna(item.get('Qtde_Real_Vencer')) and str(item.get('Qtde_Real_Vencer')).strip() != "":
                        qtd_real_str = f"<b>{int(float(item['Qtde_Real_Vencer']))} un</b>"
                    else:
                        qtd_real_str = "<span style='color: #d9534f; font-weight: bold;'>Pendente contagem física</span>"

                    st.markdown(f"--- **Lote Validade: {pd.to_datetime(item['Data de Validade']).strftime('%d/%m/%Y')}**")
                    st.markdown(f"📊 **Qtd Sistema:** {qtd_sistema} un   |   🔍 **Qtd Real Conferida:** {qtd_real_str}", unsafe_allow_html=True)
                    
                    if pd.notna(item.get('Data_Conferencia')) and item.get('Data_Conferencia'):
                        op_reg = item['Operador'] if pd.notna(item.get('Operador')) else 'Não Identificado'
                        st.caption(f"✅ Auditado por: {op_reg} em {item['Data_Conferencia']} | Ação: {item['Acao_Tomada']}")
                        
                    if pd.notna(item.get('Historico_Log')) and str(item.get('Historico_Log')).strip() != "":
                        with st.expander("📜 Ver trilha de auditoria (Histórico)"):
                            st.text(item['Historico_Log'])

                    if st.session_state.funil_atual != "3️⃣ Resolvidos":
                        with st.form(key=f"form_auditar_{item['Chave_ID']}"):
                            qt_real = st.number_input("Quantidade Real", value=int(item['Qtde_Real_Vencer']) if pd.notna(item.get('Qtde_Real_Vencer')) and str(item.get('Qtde_Real_Vencer')).strip() != "" else int(item['Qtde. Validade']) if pd.notna(item['Qtde. Validade']) else 0, key=f"q_{item['Chave_ID']}")
                            acao = st.selectbox("Ação Tomada", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"], key=f"ac_{item['Chave_ID']}")
                            preco_reb = st.number_input("Preço da Rebaixa (R$)", value=float(item['Preco_Rebaixa']) if pd.notna(item.get('Preco_Rebaixa')) else 0.0, key=f"p_{item['Chave_ID']}")
                            obs_audit = st.text_area("Anotações / Observações (Opcional)", key=f"ob_{item['Chave_ID']}")
                            foto = st.file_uploader("Foto Evidência (Opcional)", type=['jpg', 'jpeg', 'png'], key=f"ft_{item['Chave_ID']}")
                            
                            if st.form_submit_button(f"Confirmar Lote {item['Data de Validade']}"):
                                if acao == "Rebaixa" and preco_reb <= 0:
                                    st.error("⚠️ Atenção: Para a ação 'Rebaixa', o preço promocional deve ser preenchido e maior que zero!")
                                else:
                                    if qt_real == 0:
                                        acao = "Resolvido - Sem Estoque Físico"
                                        preco_reb = 0.0

                                    idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == item['Chave_ID']].tolist()[0]
                                    
                                    data_agora = pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y %H:%M')
                                    op_nome = st.session_state.get('operador_nome', 'Não Identificado')
                                    novo_log = f"[{data_agora}] Auditado por {op_nome} - Ação: {acao} (Qtd: {qt_real})"
                                    
                                    log_antigo = str(item['Historico_Log']) if pd.notna(item.get('Historico_Log')) else ""
                                    log_atualizado = f"{log_antigo}\n{novo_log}" if log_antigo else novo_log

                                    st.session_state.df_base.at[idx, 'Qtde_Real_Vencer'] = qt_real
                                    st.session_state.df_base.at[idx, 'Acao_Tomada'] = acao
                                    st.session_state.df_base.at[idx, 'Preco_Rebaixa'] = preco_reb
                                    st.session_state.df_base.at[idx, 'Observacoes'] = obs_audit
                                    st.session_state.df_base.at[idx, 'Status'] = 'Resolvido' if acao in ["Nenhuma - OK", "Resolvido - Sem Estoque Físico"] else 'Conferido'
                                    st.session_state.df_base.at[idx, 'Data_Conferencia'] = data_agora
                                    st.session_state.df_base.at[idx, 'Operador'] = op_nome
                                    st.session_state.df_base.at[idx, 'Historico_Log'] = log_atualizado
                                    
                                    salvar_base()
                                    st.success(f"Lote {item['Data de Validade']} atualizado com sucesso!")
                                    st.rerun()
                    else:
                        if st.button(f"↩️ Reativar Lote {item['Data de Validade']}", key=f"reativar_{item['Chave_ID']}", use_container_width=True):
                            idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == item['Chave_ID']].tolist()[0]
                            
                            data_agora = pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y %H:%M')
                            op_nome = st.session_state.get('operador_nome', 'Não Identificado')
                            novo_log = f"[{data_agora}] Reativado por {op_nome} (Voltou para Pendente)"
                            log_antigo = str(item['Historico_Log']) if pd.notna(item.get('Historico_Log')) else ""
                            log_atualizado = f"{log_antigo}\n{novo_log}" if log_antigo else novo_log

                            st.session_state.df_base.at[idx, 'Status'] = 'Pendente'
                            st.session_state.df_base.at[idx, 'Acao_Tomada'] = None
                            st.session_state.df_base.at[idx, 'Data_Conferencia'] = None
                            st.session_state.df_base.at[idx, 'Operador'] = None
                            st.session_state.df_base.at[idx, 'Historico_Log'] = log_atualizado
                            salvar_base()
                            st.rerun()
    else:
        st.info("Nenhum produto encontrado nesta categoria de filtros.")
else:
    st.info("A base de dados encontra-se vazia.")
