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
COLUNAS_APP = ['Chave_ID', 'Preço_Sistema', 'Preço_Oferta', 'Qtde_Real_Vencer', 'Preco_Rebaixa', 'Acao_Tomada', 'Data_Inicio_Acao', 'Status', 'Origem', 'Data_Conferencia', 'Observacoes']

def carregar_dados():
    if os.path.exists(CAMINHO_BASE):
        df = pd.read_csv(CAMINHO_BASE)
    else:
        df = pd.DataFrame(columns=COLUNAS_ERP + COLUNAS_APP)
    
    if 'Origem' not in df.columns: df['Origem'] = 'Planilha'
    if 'Data_Conferencia' not in df.columns: df['Data_Conferencia'] = None
    if 'Observacoes' not in df.columns: df['Observacoes'] = None
        
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

if 'filtro_atual' not in st.session_state: st.session_state.filtro_atual = "Todos"
if 'funil_atual' not in st.session_state: st.session_state.funil_atual = "1️⃣ Pendentes"
if 'mostrar_add' not in st.session_state: st.session_state.mostrar_add = False

# --- TOP BAR: UPLOAD DO ERP ---
with st.expander("📂 Importar Planilha do ERP (Bluesoft)"):
    arquivos = st.file_uploader("Relatórios Excel", accept_multiple_files=True)
    if arquivos and st.button("Carregar Dados"):
        st.success("Função de upload ativada na retaguarda.")

# --- TOP BAR: RELATÓRIOS E EXPORTAÇÃO DIÁRIA ---
with st.expander("📥 Relatórios Diários (Exportar)"):
    hoje_str = pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y')
    if not st.session_state.df_base.empty:
        df_dia = st.session_state.df_base[
            (st.session_state.df_base['Data_Conferencia'].astype(str).str.startswith(hoje_str)) &
            (st.session_state.df_base['Status'].isin(['Conferido', 'Resolvido']))
        ].copy()
        
        st.metric(f"Itens Auditados Hoje ({hoje_str})", len(df_dia))
        
        if not df_dia.empty:
            col_ex1, col_ex2 = st.columns(2)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_dia.to_excel(writer, index=False, sheet_name='Validades_Hoje')
            excel_data = output.getvalue()
            
            with col_ex1:
                st.download_button(label="📊 Exportar para Excel", data=excel_data, file_name=f"validades_conferidas_{hoje_str.replace('/','-')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            
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
            <table><tr><th>Código</th><th>Descrição</th><th>Vencimento</th><th>Qtd</th><th>Ação</th><th>Obs</th></tr>
            """
            for _, row in df_dia.iterrows():
                obs_text = row['Observacoes'] if pd.notna(row['Observacoes']) and row['Observacoes'] else "-"
                html_content += f"<tr><td class='codigo'>{row['Código Interno']}</td><td>{row['Descrição']}</td><td>{row['Data de Validade']}</td><td>{row['Qtde_Real_Vencer']}</td><td>{row['Acao_Tomada']}</td><td>{obs_text}</td></tr>"
            html_content += "</table></body></html>"
            
            with col_ex2:
                st.download_button(label="🌐 Exportar HTML Visual", data=html_content, file_name=f"relatorio_validades_{hoje_str.replace('/','-')}.html", mime="text/html", use_container_width=True)
        else:
            st.info("Nenhum item finalizado hoje.")
    else:
        st.info("A base de dados está vazia.")

# --- CÁLCULO DOS TOTAIS PARA OS BOTÕES ---
df_base_calc = st.session_state.df_base.copy()
if not df_base_calc.empty:
    df_base_calc['Data de Validade'] = pd.to_datetime(df_base_calc['Data de Validade'], errors='coerce')
    hoje = pd.to_datetime('today').normalize()
    
    # Totais de Funil
    tot_pendentes = len(df_base_calc[df_base_calc['Status'] == 'Pendente'])
    tot_conferidos = len(df_base_calc[df_base_calc['Status'] == 'Conferido'])
    tot_resolvidos = len(df_base_calc[df_base_calc['Status'] == 'Resolvido'])
    
    # Totais de Validade
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
        if st.button("➕", use_container_width=True):
            st.session_state.mostrar_add = not st.session_state.mostrar_add
            st.rerun()

    # --- NOVO BLOCO DE ADIÇÃO MANUAL ---
    if st.session_state.mostrar_add:
        st.markdown("### ➕ Adicionar Nova Validade ou Produto")
        st.info("💡 **Dica:** Bipe o código. Se o produto já existir, a descrição será preenchida automaticamente.")
        
        codigo_manual = st.text_input("1️⃣ Bipe o Código de Barras (e pressione Enter):")
        
        desc_padrao, preco_padrao, setor_padrao = "", 0.0, "Mercearia"
        if codigo_manual:
            cod_limpo = codigo_manual.strip()
            df_encontrado = st.session_state.df_base[
                (st.session_state.df_base['Código Interno'].astype(str) == cod_limpo) | 
                (st.session_state.df_base['GTIN'].astype(str).str.replace('.0', '', regex=False) == cod_limpo)
            ]
            if not df_encontrado.empty:
                desc_padrao = str(df_encontrado.iloc[0]['Descrição'])
                preco_padrao = float(df_encontrado.iloc[0]['Preço_Sistema']) if pd.notna(df_encontrado.iloc[0]['Preço_Sistema']) else 0.0
                setor_padrao = str(df_encontrado.iloc[0]['Setor de Compra']) if pd.notna(df_encontrado.iloc[0]['Setor de Compra']) else "Mercearia"
                st.success(f"✅ Produto reconhecido: **{desc_padrao}**")
        
        with st.form("modal_add"):
            descricao_manual = st.text_input("Descrição do Produto:", value=desc_padrao)
            val_manual = st.date_input("2️⃣ Nova Data de Validade")
            q_manual = st.number_input("Quantidade Real (Un)", min_value=0, step=1)
            p_manual = st.number_input("Preço Atual (R$)", min_value=0.0, format="%.2f", value=preco_padrao)
            
            setores = ["Mercearia", "Perecíveis", "Açougue", "Padaria", "FLV", "Outros"]
            idx = setores.index(setor_padrao) if setor_padrao in setores else 0
            setor_m = st.selectbox("Setor", setores, index=idx)
            
            acao_m = st.selectbox("Ação a Tomar", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"])
            obs_m = st.text_area("Anotações / Observações (Opcional)")
            
            if st.form_submit_button("Gravar Produto na Base"):
                if codigo_manual and descricao_manual:
                    chave = f"{codigo_manual.strip()}_{val_manual.strftime('%Y-%m-%d')}"
                    
                    if q_manual == 0 or acao_m in ["Nenhuma - OK", "Resolvido - Sem Estoque Físico"]:
                        status_m = "Resolvido"
                        if q_manual == 0: acao_m = "Resolvido - Sem Estoque Físico"
                    else:
                        status_m = "Conferido"
                        
                    data_conf_m = pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y %H:%M')

                    novo_item = {
                        'Chave_ID': chave, 'Código Interno': codigo_manual.strip(), 'GTIN': codigo_manual.strip(),
                        'Descrição': descricao_manual, 'Data de Validade': val_manual.strftime('%Y-%m-%d'),
                        'Qtde. Validade': q_manual, 'Qtde_Real_Vencer': q_manual,
                        'Preço_Sistema': p_manual, 'Setor de Compra': setor_m, 
                        'Acao_Tomada': acao_m,
                        'Status': status_m, 'Origem': 'Manual', 'Data_Conferencia': data_conf_m, 'Observacoes': obs_m
                    }
                    
                    df_nova_linha = pd.DataFrame([novo_item]).set_index('Chave_ID')
                    df_b = st.session_state.df_base.set_index('Chave_ID') if 'Chave_ID' in st.session_state.df_base.columns else st.session_state.df_base
                    df_b = pd.concat([df_b, df_nova_linha]).reset_index()
                    st.session_state.df_base = df_b
                    salvar_base()
                    
                    st.session_state.mostrar_add = False 
                    st.success("✅ Produto adicionado e encaminhado para conferência!")
                    st.rerun()
                else:
                    st.error("Preencha o Código e a Descrição.")
                    
        st.divider()

    # --- LISTAGEM DOS CARDS AGRUPADOS POR CÓDIGO ---
    if not dados_filtrados.empty:
        if busca:
            busca_limpa = busca.strip()
            dados_filtrados = dados_filtrados[
                (dados_filtrados['Código Interno'].astype(str) == busca_limpa) | 
                (dados_filtrados['GTIN'].astype(str).str.replace('.0', '', regex=False) == busca_limpa) |
                (dados_filtrados['Descrição'].astype(str).str.contains(busca_limpa, case=False))
            ]

        codigos_unicos = dados_filtrados['Código Interno'].unique()

        for cod in codigos_unicos:
            lotes_produto = dados_filtrados[dados_filtrados['Código Interno'].astype(str) == str(cod)]
            primeiro_item = lotes_produto.iloc[0]
            
            status_principal = primeiro_item['Status']
            if status_principal == 'Pendente': card_bg, text_color = "#e67e22", "white"
            elif status_principal == 'Conferido': card_bg, text_color = "#9b59b6", "white"
            else: card_bg, text_color = "#2ecc71", "white"

            total_lotes = len(lotes_produto)
            badge_lotes = f"📦 **{total_lotes} lote(s) com datas diferentes**" if total_lotes > 1 else f"📅 Vencimento: {pd.to_datetime(primeiro_item['Data de Validade']).strftime('%d/%m/%Y')}"

            st.markdown(f"""
            <div style="background-color: {card_bg}; color: {text_color}; padding: 15px; border-radius: 10px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-size: 16px; font-weight: bold; color: {text_color};">{primeiro_item['Descrição']}</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px; font-weight: 500;">{badge_lotes}</p>
                <p style="margin: 2px 0 0 0; font-size: 12px; opacity: 0.9;">Cód: {primeiro_item['Código Interno']} | Setor: {primeiro_item['Setor de Compra']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"🔍 Gerenciar Lotes / Validades ({total_lotes}) para: {primeiro_item['Descrição'][:30]}..."):
                for _, item in lotes_produto.iterrows():
                    st.markdown(f"--- **Lote Validade: {pd.to_datetime(item['Data de Validade']).strftime('%d/%m/%Y')}** | Saldo ERP: {item['Qtde. Validade']} un")
                    
                    if pd.notna(item.get('Data_Conferencia')) and item.get('Data_Conferencia'):
                        st.caption(f"✅ Auditado em: {item['Data_Conferencia']} | Ação: {item['Acao_Tomada']} | Qtd Real: {item['Qtde_Real_Vencer']}")

                    if st.session_state.funil_atual != "3️⃣ Resolvidos":
                        with st.form(key=f"form_auditar_{item['Chave_ID']}"):
                            qt_real = st.number_input("Quantidade Real", value=int(item['Qtde. Validade']) if pd.notna(item['Qtde. Validade']) else 0, key=f"q_{item['Chave_ID']}")
                            acao = st.selectbox("Ação Tomada", ["Rebaixa", "Descarte", "Troca", "Nenhuma - OK", "Resolvido - Sem Estoque Físico"], key=f"ac_{item['Chave_ID']}")
                            preco_reb = st.number_input("Preço da Rebaixa (R$)", value=0.0, key=f"p_{item['Chave_ID']}")
                            obs_audit = st.text_area("Anotações / Observações (Opcional)", key=f"ob_{item['Chave_ID']}")
                            foto = st.file_uploader("Foto Evidência (Opcional)", type=['jpg', 'jpeg', 'png'], key=f"ft_{item['Chave_ID']}")
                            
                            if st.form_submit_button(f"Confirmar Lote {item['Data de Validade']}"):
                                if qt_real == 0:
                                    acao = "Resolvido - Sem Estoque Físico"
                                    preco_reb = 0.0

                                idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == item['Chave_ID']].tolist()[0]
                                st.session_state.df_base.at[idx, 'Qtde_Real_Vencer'] = qt_real
                                st.session_state.df_base.at[idx, 'Acao_Tomada'] = acao
                                st.session_state.df_base.at[idx, 'Preco_Rebaixa'] = preco_reb
                                st.session_state.df_base.at[idx, 'Observacoes'] = obs_audit
                                st.session_state.df_base.at[idx, 'Status'] = 'Resolvido' if acao in ["Nenhuma - OK", "Resolvido - Sem Estoque Físico"] else 'Conferido'
                                st.session_state.df_base.at[idx, 'Data_Conferencia'] = pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y %H:%M')
                                
                                salvar_base()
                                st.success(f"Lote {item['Data de Validade']} atualizado com sucesso!")
                                st.rerun()
                    else:
                        if st.button(f"↩️ Reativar Lote {item['Data de Validade']}", key=f"reativar_{item['Chave_ID']}", use_container_width=True):
                            idx = st.session_state.df_base.index[st.session_state.df_base['Chave_ID'] == item['Chave_ID']].tolist()[0]
                            st.session_state.df_base.at[idx, 'Status'] = 'Pendente'
                            st.session_state.df_base.at[idx, 'Acao_Tomada'] = None
                            st.session_state.df_base.at[idx, 'Data_Conferencia'] = None
                            salvar_base()
                            st.rerun()
    else:
        st.info("Nenhum produto encontrado nesta categoria de filtros.")
else:
    st.info("A base de dados encontra-se vazia.")
