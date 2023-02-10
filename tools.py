import pandas as pd
from terminaltables import AsciiTable


def compute_average_salary(salary_from=0, salary_to=0):
    """Возвращает результат расчёта среднего значения зарплаты"""
    if salary_from and salary_to:
        return (salary_from + salary_to)/2
    elif not salary_from:
        return salary_to * 0.8
    else:
        return salary_from * 1.2


def print_terminal_table(records, title):
    """Выводит на экран таблицу с результатами поиска в табличном виде"""
    vacancies = pd.DataFrame(records).T
    vacancies['programming_language'] = vacancies.index
    sorted_vacancies = vacancies[['programming_language', 'vacancies_found','vacancies_processed', 'average_salary']]\
        .sort_values(by=['average_salary'], ascending=False)
    sorted_vacancies = sort_vacancies.values.tolist()
    table_for_print = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for row in sorted_vacancies:
        table_for_print.append(row)
    terminal_table_instance = AsciiTable(table_for_print, title)
    print('\n', terminal_table_instance.table)
