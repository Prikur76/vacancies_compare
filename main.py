import argparse
import os
import time

import requests
from dotenv import load_dotenv

import tools


def fetch_area_id_hh(area):
    """Возвращает результат поиска (словарь IDs) территорий России по справочнику hh.ru или None"""
    hh_url = "https://api.hh.ru/areas"
    headers = {
        'User-Agent': 'App/1.0',
    }
    response = requests.get(url=hh_url, headers=headers)
    response.raise_for_status()
    rus_areas = response.json()[0]['areas']
    area_id = [row['id'] for row in rus_areas if area.lower() in row['name'].lower()]
    return area_id


def fetch_vacancy_hh(language, area=None, period=None, page=None):
    """Возвращает ответ на запрос по словарю вакансий или вызывает исключение"""
    hh_url = "https://api.hh.ru/vacancies"
    headers = {
        'User-Agent': 'App/1.0',
    }
    payload = {
        'host': 'hh.ru',
        'text': language,
        'area': area,
        'period': period,
        'page': page,
        'only_with_salary': True,
        'currency': 'RUR',
    }
    response = requests.get(url=hh_url, params=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_hh(language, area=None, period=None):
    """Возвращает средний размер зарплаты по заданной вакансии на hh.ru"""
    vacancy_salaries = []
    page = 0
    pages_count = 1
    while page < pages_count:
        try:
            page_response = fetch_vacancy_hh(language, area=area, period=period, page=page)
            vacancies_found = page_response['found']
            pages_count = int(page_response['pages'])
            for vacancy in page_response['items']:
                currency = vacancy['salary']['currency']
                salary_from = vacancy['salary']['from']
                salary_to = vacancy['salary']['to']
                if currency == 'RUR' and (salary_from or salary_to):
                    rub_salary = tools.compute_average_salary(salary_from, salary_to)
                    vacancy_salaries.append(rub_salary)
        except requests.exceptions.HTTPError as err:
            print(f"Page {page}: {err}")
        page += 1
        time.sleep(1)

    average_salary = 0
    vacancies_processed = 0

    if len(vacancy_salaries):
        vacancies_processed = len(vacancy_salaries)
        average_salary = int(sum(vacancy_salaries) / vacancies_processed)

    dataset = dict(vacancies_found=vacancies_found,
                   vacancies_processed=vacancies_processed,
                   average_salary=average_salary)
    return dataset


def fetch_vacancy_sj(sj_key, language, area=None, period=0, page=None):
    """Возвращает ответ сайта SuperJob.ru по заданным параметрам"""
    sj_url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {
        'X-Api-App-Id': sj_key,
    }
    payload = {
        'keyword': language,
        'town': area,
        'period': period,
        'page': page,
        'no_agreement': 1,
    }
    response = requests.get(url=sj_url, params=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_sj(sj_key, language, area=None, period=0):
    """Возвращает расчёт средней заработной платы по данным сайта SuperJob.ru"""
    vacancy_salaries = []
    vacancies_found = 0
    page = 0
    pages_count = 1
    while page < pages_count:
        try:
            page_response = fetch_vacancy_sj(sj_key, language, area=area, period=period, page=page)
            if page_response['total'] > vacancies_found:
                vacancies_found = page_response['total']
            if len(page_response['objects']):
                pages_count = round(int(vacancies_found)/len(page_response['objects']) + 0.5)
                for vacancy in page_response['objects']:
                    currency = vacancy['currency']
                    salary_from = vacancy['payment_from']
                    salary_to = vacancy['payment_to']
                    if currency == 'rub' and (salary_from or salary_to):
                        rub_salary = tools.compute_average_salary(salary_from, salary_to)
                        print(language, vacancies_found, rub_salary)
                        vacancy_salaries.append(rub_salary)
        except requests.exceptions.HTTPError as err:
            print(f"Page {page}: {err}")
        page += 1
        time.sleep(1)

    average_salary = 0
    vacancies_processed = 0

    if len(vacancy_salaries):
        vacancies_processed = len(vacancy_salaries)
        average_salary = int(sum(vacancy_salaries) / vacancies_processed)

    dataset = dict(vacancies_found=vacancies_found,
                   vacancies_processed=vacancies_processed,
                   average_salary=average_salary)
    return dataset


def main():
    load_dotenv()
    sj_key = os.environ.get('SUPERJOB_SECRET_KEY')

    parser = argparse.ArgumentParser(description='Поиск средней зарплаты по вакансиям')
    parser.add_argument('-a', '--area', default=None, help='Ввести наименование города')
    parser.add_argument('-p', '--period', type=int, default=None, help='Введите число - период поиска ')
    args = parser.parse_args()
    area = args.area
    period = args.period

    table_title_hh = 'HeadHunter'
    table_title_sj = 'SuperJob'

    if area:
        area = area.capitalize()
        area_id = fetch_area_id_hh(area)
        table_title_hh = f'HeadHunter {area}'
        table_title_sj = f'SuperJob {area}'

    dataset_hh = dict()
    dataset_sj = dict()

    # programming_languages = ['Python', 'С++', 'C#', 'Java', 'JavaScript', 'C', 'PHP', 'Swift', 'Go', 'Kotlin']

    programming_languages = ['Python', 'C', 'Kotlin']

    for language in programming_languages:
        dataset_hh[language] = predict_rub_salary_hh(language, area=area_id, period=period)
        dataset_sj[language] = predict_rub_salary_sj(sj_key, language, area=area, period=period)
        time.sleep(1)

    tools.print_terminal_table(dataset_hh, table_title_hh)
    tools.print_terminal_table(dataset_sj, table_title_sj)


if __name__ == '__main__':
    main()
