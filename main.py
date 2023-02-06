import argparse
import os
import time

import requests
from dotenv import load_dotenv

import tools


#---------------------- HEADHUNTER ------------------------

def fetch_areas_ids_hh(area):
    """Возвращает результат поиска (словарь IDs) территорий России по справочнику hh.ru или None"""
    if area:
        hh_url = "https://api.hh.ru/areas"
        headers = {
            'User-Agent': 'App/1.0',
        }
        response = requests.get(url=hh_url, headers=headers)
        response.raise_for_status()
        rus_areas = response.json()[0]['areas']
        areas_ids = [row['id'] for row in rus_areas if area.lower() in row['name'].lower()]
        return areas_ids
    else:
        return None


def fetch_vacancy_hh(vacancy, area=None, period=None, page=None):
    """Возвращает ответ на запрос по словарю вакансий или вызывает исключение"""
    areas_ids = None
    if area:
        if area.isalpha():
            areas_ids = fetch_areas_ids_hh(area)

    hh_url = "https://api.hh.ru/vacancies"
    headers = {
        'User-Agent': 'App/1.0',
    }

    payload = {
        'host': 'hh.ru',
        'text': vacancy,
        'area': areas_ids,
        'period': period,
        'page': page,
        'only_with_salary': True,
        'currency': 'RUR',
    }
    response = requests.get(url=hh_url, params=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def predict_rub_salary_hh(vacancy, area=None, period=None):
    """Возвращает средний размер зарплаты по заданной вакансии на hh.ru"""
    vacancy_salaries = []
    first_response = fetch_vacancy_hh(vacancy, area=area, period=period)
    vacancies_found = first_response['found']
    pages_number = first_response['pages']
    if vacancies_found > 0:
        page = 0
        while page < int(pages_number):
            page_response = fetch_vacancy_hh(vacancy, area=area, period=period, page=page)
            if page_response:
                for salary in page_response['items']:
                    if salary['salary']['currency'] == 'RUR':
                        rub_salary = tools.compute_average_salary(salary_from=salary['salary']['from'],
                                                                  salary_to=salary['salary']['to'])
                        vacancy_salaries.append(rub_salary)
            page += 1
            time.sleep(1)
        vacancies_processed = len(vacancy_salaries)
        average_salary = int(sum(vacancy_salaries) / vacancies_processed)
    else:
        vacancies_processed = 0
        average_salary = 0

    predict = dict(vacancies_found=vacancies_found,
                   vacancies_processed=vacancies_processed,
                   average_salary=average_salary)
    return predict

#----------------------- SUPERJOB --------------------------

def fetch_vacancy_sj(vacancy, area=None, period=0, page=None):
    """Возвращает ответ сайта SuperJob.ru по заданным параметрам"""
    load_dotenv()
    sj_key = os.environ.get('SUPERJOB_SECRET_KEY')
    sj_url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {
        'X-Api-App-Id': sj_key,
    }
    payload = {
        'keyword': vacancy,
        'town': area,
        'period': period,
        'page': page,
        'no_agreement': 1,
    }
    response = requests.get(url=sj_url, params=payload, headers=headers)
    # response.raise_for_status()
    if response.status_code == 200:
        return response.json()
    else:
        return None


def predict_rub_salary_sj(vacancy, area=None, period=0):
    """Возвращает расчёт средней заработной платы по данным сайта SuperJob.ru"""
    vacancy_salaries = []
    first_response = fetch_vacancy_sj(vacancy, area=area, period=period)
    vacancies_found = first_response['total']
    pages_number = round(int(vacancies_found) / 20 + 0.5)
    if vacancies_found > 0:
        page = 0
        while page < int(pages_number):
            page_response = fetch_vacancy_sj(vacancy, area=area, period=period, page=page)
            if page_response:
                for salary in page_response['objects']:
                    if salary['currency'] == 'rub':
                        rub_salary = tools.compute_average_salary(salary_from=salary['payment_from'],
                                                                  salary_to=salary['payment_to'])
                        vacancy_salaries.append(rub_salary)
            page += 1
            time.sleep(1)
        vacancies_processed = len(vacancy_salaries)
        average_salary = int(sum(vacancy_salaries) / vacancies_processed)
    else:
        vacancies_processed = 0
        average_salary = 0

    predict = dict(vacancies_found=vacancies_found,
                   vacancies_processed=vacancies_processed,
                   average_salary=average_salary)
    return predict

#----------------------- MAIN ------------------------------

def main():
    vacancies = ['Python', 'С++', 'C#', 'Java', 'JavaScript', 'C',  'PHP', 'Swift', 'Go', 'Kotlin']

    parser = argparse.ArgumentParser(description='Поиск средней зарплаты по вакансиям')
    parser.add_argument('-a', '--area', default=None, help='Ввести наименование города')
    parser.add_argument('-p', '--period', type=int, default=None, help='Введите число - период поиска ')
    args = parser.parse_args()
    area = args.area
    period = args.period

    if area:
        area = area.capitalize()
        table_title_hh = f"HeadHunter {area}"
        table_title_sj = f"SuperJob {area}"
    else:
        table_title_hh = 'HeadHunter'
        table_title_sj = 'SuperJob'

    predict_hh = dict()
    predict_sj = dict()

    for vacancy in vacancies:
        print(vacancy)
        predict_hh[vacancy] = predict_rub_salary_hh(vacancy, area=area, period=period)
        predict_sj[vacancy] = predict_rub_salary_sj(vacancy, area=area, period=period)
        time.sleep(1)

    tools.print_terminal_table(predict_hh, table_title_hh)
    tools.print_terminal_table(predict_sj, table_title_sj)


if __name__ == '__main__':
    main()
