import pickle
import streamlit as st
import pandas as pd
from streamlit_ace import st_ace
from models.questions import question_bank, Question
from models.database import SQLiteAdapter, DuckDBAdapter

# --- FUNÇÕES CALLBACK E DE LÓGICA (sem alterações) ---

def select_question(question_id: str):
    """Callback para atualizar o exercício selecionado e limpar resultados antigos."""
    st.session_state.question_selected = question_id
    st.session_state.pop('result_df', None)
    st.session_state.pop('query_error', None)
    st.session_state.pop('correct_question', None)

def update_database():
    """Callback para trocar o banco de dados e limpar o estado."""
    db_map = {'DuckDB': st.session_state.duckdb_db, 'SQLite': st.session_state.sqlite_db}
    st.session_state.database_selected = db_map[st.session_state.db_choice]
    st.session_state.pop('result_df', None)
    st.session_state.pop('query_error', None)
    st.session_state.pop('correct_question', None)
    st.toast(f"Banco de dados alterado para {st.session_state.db_choice}")

def result_execution():
    """Função para exibir o resultado da query, erros ou mensagens de status."""
    if 'query_error' in st.session_state:
        st.error(st.session_state.query_error)
    elif 'result_df' in st.session_state:
        st.dataframe(st.session_state.result_df, use_container_width=True)
        if st.session_state.get('correct_question'):
            st.success("Parabéns! Sua query está correta. 🥳")
        else:
            st.error("Sua query foi executada, mas não retornou o resultado esperado. Tente novamente!")
    else:
        st.info("O resultado da sua query aparecerá aqui.")

# --- INICIALIZAÇÃO DA APLICAÇÃO (sem alterações) ---
if 'application_started' not in st.session_state:
    st.set_page_config(
        page_title="OSSql - Aprenda SQL com Jiu-jitsu",
        page_icon="🥋",
        layout="wide",
    )
    st.session_state.application_started = True
    st.session_state.question_selected = 'Apresentação'
    st.session_state.correct_answers = 1
    st.session_state.questions_keys = list(question_bank.questions.keys())
    st.session_state.query_validator = lambda query, mandatory_list: all([word in query for word in mandatory_list])
    
    st.session_state.sqlite_db = SQLiteAdapter()
    st.session_state.duckdb_db = DuckDBAdapter()
    for db in (st.session_state.sqlite_db, st.session_state.duckdb_db):
        db.create_table('data/atletas.csv', 'atletas')
    
    st.session_state.db_choice = 'DuckDB'
    st.session_state.database_selected = st.session_state.duckdb_db

# --- SIDEBAR (MENU DE EXERCÍCIOS) ---
# A sidebar agora conterá apenas a navegação dos exercícios.
st.sidebar.title("Menu exercícios")
for index in range(0, st.session_state.correct_answers + 1):
    question_id = st.session_state.questions_keys[index]
    st.sidebar.button(
        question_id,
        use_container_width=True,
        type="primary" if question_id == st.session_state.question_selected else "secondary",
        on_click=select_question,
        args=(question_id,)
    )

# --- LAYOUT PRINCIPAL ---

# NOVO: Layout para o canto superior direito
# Criamos colunas no topo da página para posicionar o popover
top_cols = st.columns([5, 1]) # Divide o espaço em 6 partes, 5 para o título e 1 para o botão

with top_cols[1]: # Usando a coluna da direita
    with st.popover("Gerenciar Progresso", use_container_width=True):
        st.markdown("##### Salvar/Carregar")
        
        # LÓGICA PARA SALVAR (movida para dentro do popover)
        progress_data = {'correct_answers': st.session_state.correct_answers}
        pickled_progress = pickle.dumps(progress_data)
        st.download_button(
            label="💾 Salvar Progresso",
            data=pickled_progress,
            file_name="progresso_osql.pkl",
            mime="application/octet-stream",
            use_container_width=True
        )

        # LÓGICA PARA CARREGAR (movida para dentro do popover)
        uploaded_file = st.file_uploader(
            "Carregar progresso (.pkl)", type="pkl", label_visibility="collapsed"
        )
        if uploaded_file is not None:
            try:
                loaded_data = pickle.load(uploaded_file)
                if 'correct_answers' in loaded_data:
                    st.session_state.correct_answers = loaded_data['correct_answers']
                    st.toast("Sucesso! Seu progresso foi restaurado. ✅", icon="🎉")
                    st.rerun() 
                else:
                    st.error("Arquivo inválido.")
            except Exception as e:
                st.error(f"Erro ao carregar.")


# Layout principal com as duas colunas de conteúdo
col1, col2 = st.columns(2)

with col1:
    question: Question = question_bank.questions.get(st.session_state.question_selected)
    st.markdown(question.text, unsafe_allow_html=True)

    if st.session_state.question_selected != 'Apresentação':
        with st.expander("Precisa de uma dica?"):
            st.info(question.hint)
        st.markdown("### Resultado da Execução")
        with st.container():
            result_execution()

with col2:
    if st.session_state.question_selected != 'Apresentação':
        
        # ALTERADO: Seletor de Banco de Dados com st.selectbox
        st.selectbox(
            "Banco de Dados:",
            ('DuckDB', 'SQLite'),
            key='db_choice',
            on_change=update_database,
        )
        
        st.markdown("### Editor de Código SQL")
        query = st_ace(
            placeholder="-- Digite seu código SQL aqui...",
            language="sql",
            theme="github",
            keybinding="vscode",
            font_size=14,
            key=f"ace_editor_{st.session_state.question_selected}",
            auto_update=False)
        
        if st.button("Executar Query", use_container_width=True, type="primary"):
            st.session_state.pop('result_df', None)
            st.session_state.pop('query_error', None)
            st.session_state.pop('correct_question', None)

            if not query:
                st.toast("Por favor, digite uma query para executar.", icon="⚠️")
            elif not st.session_state.query_validator(query.upper(), question.mandatory + ['FROM']):
                st.session_state.query_error = "Sua query não contém as cláusulas obrigatórias."
            else:
                try:
                    client_result = st.session_state.database_selected.select_query(query)
                    question_result = st.session_state.database_selected.select_query(question.query_result)
                    
                    st.session_state.result_df = client_result
                    if client_result.equals(question_result):
                        st.session_state.correct_question = True
                    else:
                        st.session_state.correct_question = False
                except Exception as e:
                    st.session_state.query_error = f"Ocorreu um erro na execução da query: {e}"
            
            st.rerun()