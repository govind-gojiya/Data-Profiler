import os
import requests
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"
load_dotenv(ENV_FILE_PATH)
airflow_url = os.environ.get("AIRFLOW_URL", "http://localhost:8080/api/v1/dags/")
airflow_username = os.environ.get("AIRFLOW_USERNAME", "admin")
airflow_password = os.environ.get("AIRFLOW_PASSWORD", "")

def create_etl_dag(data, dag_id):
    try: 
        airflow_api_url = '{}{}/dagRuns'.format(airflow_url, dag_id)
        headers = {'Content-Type': 'application/json'}

        payload = {
            'conf': data
        }

        response = requests.post(airflow_api_url, json=payload, headers=headers, auth=(airflow_username, airflow_password))
        dag_run_id = response.json().get('dag_run_id')
        status=response.json().get('state')

        if response.status_code == 200:
            if response.status_code == 200:
                return True
            else:
                print("Error while running new dag of table !\nError: ", response.json())
                return None
        else:
            print(response.json())
            return None
    except Exception as e:
        print("Something not right with airflow server !\nError: ", e)
        return None

def trigger_etl_cycle(dag_id, data={}):
    try: 
        airflow_api_url = '{}{}/dagRuns'.format(airflow_url, dag_id)
        headers = {'Content-Type': 'application/json'}

        payload = {
            'conf': data
        }

        response = requests.post(airflow_api_url, json=payload, headers=headers, auth=(airflow_username, airflow_password))
        dag_run_id = response.json().get('dag_run_id')
        status=response.json().get('state')

        if response.status_code == 200:
            return dag_run_id, status
        else:
            print(response.json())
            return None, None
    except Exception as e:
        print("Something not right with airflow server !\nError: ", e)
        return None, None


def get_etl_status(dag_id, dag_run_id):
    if not dag_run_id or not dag_id:
        return None
    try:
        airflow_api_url = '{}{}/dagRuns/{}'.format(airflow_url, dag_id,dag_run_id)
        response=requests.get(airflow_api_url,auth=(airflow_username, airflow_password))
        status=response.json()['state']
        return status
    except Exception as e:
        print("Something not right with airflow server !\nError: ", e)
        return None

def generate_cron_expression(value, number):
    if value == 'Minutes':
        cron_expression = '*/{} * * * *'.format(number)
    elif value == 'Hour':
        cron_expression = '0 */{} * * *'.format(number)
    elif value == 'Day of Month':
        cron_expression = '0 0 */{} * *'.format(number)
    elif value == 'Month of Year':
        cron_expression = '0 0 1 */{} *'.format(number)
    elif value == 'Day of Week':
        cron_expression = '0 0 * * {}'.format(number)
    else:
        cron_expression = None

    return cron_expression