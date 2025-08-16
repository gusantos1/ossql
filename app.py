import pickle
import streamlit as st
import pandas as pd
from streamlit_ace import st_ace
from models.questions import question_bank, Question
from models.database import SQLiteAdapter, DuckDBAdapter


def select_question(question_id: str):
    """Callback para atualizar o exercício selecionado e limpar resultados antigos."""
    st.session_state.question_selected = question_id
    # Limpa o estado da questão anterior para evitar mostrar resultados antigos
    st.session_state.pop('result_df', None)
    st.session_state.pop('query_error', None)
    st.session_state.pop('correct_question', None)

def result_execution():
    """Função para exibir o resultado da query, erros ou mensagens de status."""
    # Esta função agora apenas lê o st.session_state, sem modificá-lo.
    # A lógica de exibição é clara e hierárquica.
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


# --- INICIALIZAÇÃO DA APLICAÇÃO ---
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
    for db in database:
        db.create_table('data/atletas.csv', 'atletas')
    st.session_state.database_selected = st.session_state.duckdb_db

# --- SIDEBAR (MENU DE EXERCÍCIOS) ---
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
        # O placeholder é preenchido pela função que agora apenas exibe o estado
        with st.container():
            result_execution()

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
            auto_update=False
        )

        if st.button("Executar Query", use_container_width=True, type="primary"):
            # 1. Limpa o estado anterior antes de uma nova execução
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
                    
                    # 2. Define o novo estado com base no resultado
                    st.session_state.result_df = client_result
                    if client_result.equals(question_result):
                        st.session_state.correct_question = True
                    else:
                        st.session_state.correct_question = False
                except Exception as e:
                    st.session_state.query_error = f"Ocorreu um erro na execução da query: {e}"
            
            # 3. Força a re-renderização para exibir o novo estado imediatamente
            st.rerun()