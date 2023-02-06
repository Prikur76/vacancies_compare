import pandas as pd
from terminaltables import AsciiTable


def compute_average_salary(salary_from=None, salary_to=None):
    """Возвращает результат расчёта среднего значения зарплаты или None"""
    if salary_from is not None and salary_to is not None:
        return (salary_from + salary_to)/2
    elif salary_from is None:
        return salary_to * 0.8
    elif salary_to is None:
        return salary_from * 1.2
    else:
        return None


def print_terminal_table(predict_data, title):
    """Выводит на экран таблицу с результатами поиска в табличном виде"""
    if predict_data:
        vacancies = pd.DataFrame(predict_data).T
        vacancies['programming_language'] = vacancies.index
        sort_vacancies = vacancies[['programming_language', 'vacancies_found','vacancies_processed', 'average_salary']]\
            .sort_values(by=['average_salary'], ascending=False)
        sort_vacancies = sort_vacancies.values.tolist()
        table_for_print = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
        for row in sort_vacancies:
            table_for_print.append(row)
        terminal_table_instance = AsciiTable(table_for_print, title)
        print('\n', terminal_table_instance.table)
    else:
        return None
