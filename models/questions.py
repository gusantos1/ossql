from dataclasses import dataclass
from typing import List


@dataclass
class Question:
    id: str
    text: str
    query_result: str
    mandatory: List[str] = None
    hint: str = None

class QuestionBank:
    def __init__(self):
        self.questions = {}
    
    def add_question(self, id: str, path: str, query_result:str = None, mandatory:List[str] = None, hint = None) -> Question:
        question = Question(
            id, 
            self.open_file(path), 
            self.open_file(query_result).replace('\n', ''), 
            mandatory, 
            hint)
        self.questions[id] = question
        return question
    
    @staticmethod
    def open_file(path) -> str:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()

question_bank = QuestionBank()
# question_bank.add_question('Apresentação', 'static\questions\home.md')
question_bank.add_question('Exercício 1', 'static/questions/question1.md', 'static/results/question1.sql', ['SELECT'], 'Selecione todas as colunas da tabela')
question_bank.add_question('Exercício 2', 'static/questions/question2.md', 'static/results/question2.sql', ['SELECT', 'WHERE'], 'Selecione as colunas da tabela aplicando um filtro')