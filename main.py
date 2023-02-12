import argparse
import os
import time

import requests
from dotenv import load_dotenv

import tools


def fetch_area_id_hh(area):
    """Возвращает результат поиска (словарь IDs) территорий России"""
    hh_url = "https://api.hh.ru/areas"
    headers = {
        'User-Agent': 'App/1.0',
    }
    response = requests.get(url=hh_url, headers=headers)
    response.raise_for_status()
    rus_areas = response.json()[0]['areas']
    area_id = [row['id'] for row in rus_areas if area.lower() in row['name'].lower()]
    return area_id


def fetch_vacancy_hh(language, area=None, period=None, page=None, only_with_salary=False):
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
        'only_with_salary': only_with_salary,
        'currency': 'RUR',
    }
    response = requests.get(url=hh_url, params=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_hh(language, area=None, period=None, only_with_salary=False):
    """Возвращает средний размер зарплаты по заданной вакансии на hh.ru"""
    vacancies_found = 0
    vacancies_processed = 0
    average_salary = 0

    vacancy_salaries = []
    page = 0
    pages_count = 1
    while page < pages_count:
        try:
            page_response = fetch_vacancy_hh(language, area=area, period=period,
                                             page=page, only_with_salary=only_with_salary)
            pages_count = page_response['pages']
            vacancies_total = page_response['found']

            if vacancies_total:
                vacancies_found = vacancies_total

            for vacancy in page_response['items']:
                if vacancy['salary']:
                    currency = vacancy['salary']['currency']
                    salary_from = vacancy['salary']['from']
                    salary_to = vacancy['salary']['to']

                    if currency == 'RUR' and (salary_from or salary_to):
                        rub_salary = tools.compute_average_salary(salary_from, salary_to)
                        if rub_salary:
                            vacancy_salaries.append(rub_salary)
            page += 1

        except requests.exceptions.HTTPError as err:
            print(f"Page {page} from {pages_count}.\nError: {err}")

        time.sleep(1)

    if vacancy_salaries:
        vacancies_processed = len(vacancy_salaries)
        average_salary = int(sum(vacancy_salaries)/vacancies_processed)

    vacancies_content = {
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary
    }
    return vacancies_content


def fetch_vacancy_sj(sj_key, language, area=None, period=0, page=None, no_agreement=0):
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
        'no_agreement': no_agreement,
    }
    response = requests.get(url=sj_url, params=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_sj(sj_key, language, area=None, period=0, no_agreement=0):
    """Возвращает расчёт средней заработной платы по данным сайта SuperJob.ru"""
    vacancies_found = 0
    vacancies_processed = 0
    average_salary = 0

    vacancy_salaries = []
    page = 0
    pages_count = 1
    while page < pages_count:
        try:
            page_response = fetch_vacancy_sj(sj_key, language, area=area, period=period,
                                             page=page, no_agreement=no_agreement)
            vacancies_total = page_response['total']
            vacancies_count_on_page = len(page_response['objects'])

            if vacancies_total:
                vacancies_found = vacancies_total

            if vacancies_count_on_page:
                pages_count = round(vacancies_found/vacancies_count_on_page + 0.5)

                for vacancy in page_response['objects']:
                    if not vacancy['agreement']:
                        currency = vacancy['currency']
                        salary_from = vacancy['payment_from']
                        salary_to = vacancy['payment_to']

                        if currency == 'rub' and (salary_from or salary_to):
                            rub_salary = tools.compute_average_salary(salary_from, salary_to)
                            if rub_salary:
                                vacancy_salaries.append(rub_salary)
                page += 1
            else:
                page = pages_count

        except requests.exceptions.HTTPError as err:
            print(f"Page {page} from {pages_count}: end of fetch limits.\n{err}")
            page = pages_count

        time.sleep(1)

    if vacancy_salaries:
        vacancies_processed = len(vacancy_salaries)
        average_salary = int(sum(vacancy_salaries)/vacancies_processed)

    vacancies_content = {
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary
    }
    return vacancies_content


def main():
    load_dotenv()
    sj_key = os.environ.get('SUPERJOB_SECRET_KEY')

    parser = argparse.ArgumentParser(description='Поиск средней зарплаты по вакансиям')
    parser.add_argument('-a', '--area', default=None,
                        help='Ввести наименование города')
    parser.add_argument('-p', '--period', type=int, default=None,
                        help='Введите число - период поиска')
    parser.add_argument('-ws', '--with_salaries', type=int, default=0,
                        help='Введите 1 для включения фильтра вакансий с зарплатами')
    args = parser.parse_args()
    area = args.area.capitalize()
    period = args.period
    no_agreement = args.with_salaries
    only_with_salary = bool(no_agreement)

    table_title_hh = 'HeadHunter'
    table_title_sj = 'SuperJob'

    area_id = None
    if area:
        area_id = fetch_area_id_hh(area)
        table_title_hh = f'HeadHunter {area}'
        table_title_sj = f'SuperJob {area}'

    vacancies_hh = dict()
    vacancies_sj = dict()

    programming_languages = ['Python', 'С++', 'C#', 'Java', 'JavaScript', 'C', 'PHP', 'Swift', 'Go', 'Kotlin']

    for language in programming_languages:
        vacancies_hh[language] = predict_rub_salary_hh(language, area=area_id, period=period,
                                                       only_with_salary=only_with_salary)
        vacancies_sj[language] = predict_rub_salary_sj(sj_key, language, area=area, period=period,
                                                       no_agreement=no_agreement)
        time.sleep(1)

    tools.print_terminal_table(vacancies_hh, table_title_hh)
    tools.print_terminal_table(vacancies_sj, table_title_sj)


if __name__ == '__main__':
    main()
