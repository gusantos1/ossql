import streamlit as st
import pandas as pd
from streamlit_ace import st_ace
from models.questions import question_bank, Question
from models.database import SQLiteAdapter, DuckDBAdapter

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
    database = (st.session_state.sqlite_db, st.session_state.duckdb_db)
    for database in database:
        database.create_table('data/atletas.csv', 'atletas')
    st.session_state.database_selected = st.session_state.sqlite_db

def select_question(question_id: str):
    """Callback para atualizar o exercício selecionado e limpar resultados antigos."""
    st.session_state.question_selected = question_id
    st.session_state.pop('result_df', None)
    st.session_state.pop('query_error', None)
   
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
col1, col2 = st.columns(2)

# Coluna da Esquerda: Enunciado e Resultado
with col1:
    question: Question = question_bank.questions.get(st.session_state.question_selected)
    st.markdown(question.text, unsafe_allow_html=True)
    
    if st.session_state.question_selected != 'Apresentação':
        with st.expander("Precisa de uma dica?"):
            st.info(question.hint)
        st.markdown("### Resultado da Execução")
        output_placeholder = st.empty()
        
        with output_placeholder.container():
            if 'query_error' in st.session_state:
                st.error(st.session_state.query_error)
            elif 'result_df' in st.session_state:
                st.success("Query executada com sucesso!")
                st.dataframe(st.session_state.result_df, use_container_width=True)
            else:
                st.info("O resultado da sua query aparecerá aqui.")

# Coluna da Direita: Editor de SQL
with col2:
    if st.session_state.question_selected != 'Apresentação':
        st.markdown("### Editor de Código SQL")
        
        query = st_ace(
            placeholder="-- Digite seu código SQL aqui...",
            language="sql",
            theme="github",
            keybinding="vscode",
            font_size=14,
            key=f"ace_editor_{st.session_state.question_selected}",
            auto_update=True
        )

        if st.button("Executar Query", use_container_width=True, type="primary"):
            if query:
                if st.session_state.query_validator(query, question.mandatory):
                    try:
                        client_result = st.session_state.database_selected.select_query(query)
                        question_result = st.session_state.database_selected.select_query(question.query_result)
                        if client_result.equals(question_result):
                            st.session_state.result_df = client_result
                            st.session_state.pop('query_error', None)
                    except Exception as e:
                        st.session_state.query_error = f"Erro de SQL: {e}"
                        st.session_state.pop('result_df', None)
                    
                    st.rerun()
                else:
                    with output_placeholder.container():
                        st.error(f"Sua query não contém as clausulas obrigatórias.")
            else:
                 with output_placeholder.container():
                    st.warning("Por favor, digite uma query para executar.")
