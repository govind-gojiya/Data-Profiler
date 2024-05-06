from sqlalchemy import text, update, Table, MetaData
import pendulum
import sys
sys.path.insert(0, "/home/bacancy/airflow/dags/config")
sys.path.insert(1, "/home/bacancy/airflow/dags/util")
from config.connection import Enginecreater
from util.postgres_tests import PostgresTests
from airflow.decorators import dag, task
import pandas as pd
from datetime import datetime, timezone
from airflow.exceptions import AirflowFailException
import psycopg2
import json


@dag(
    dag_id="test_pipline_postgres",
    schedule="@once",
    catchup=False,
    start_date=pendulum.datetime(2024, 4, 4, tz="UTC"),
    tags=["test"],
)
def test_pipline():
    
    @task(task_id="extract")
    def extract(ti, **kwargs):
        table_info = None
        try:
            data = kwargs['dag_run'].conf
            connection_data = json.loads(data["connection"])
            hostname = connection_data['hostname']
            portnumber = connection_data['portnumber']
            username = connection_data['username']
            password = connection_data['password']
            database_name = connection_data['database_name']
            test_info = data['test_info']
            ti.xcom_push(key='hostname', value=hostname)
            ti.xcom_push(key='portnumber', value=portnumber)
            ti.xcom_push(key='username', value=username)
            ti.xcom_push(key='password', value=password)
            ti.xcom_push(key='database_name', value=database_name)
            ti.xcom_push(key='test_id', value=test_info['test_id'])
            ti.xcom_push(key='test_type', value=test_info['test_type'])
            ti.xcom_push(key='test_purpose', value=test_info['test_purpose'])
            ti.xcom_push(key='test_purpose_value', value=test_info['test_purpose_value'])
            ti.xcom_push(key='test_table', value=test_info['table'])
            ti.xcom_push(key='test_column', value=test_info['column'])
            ti.xcom_push(key='any_error_extract', value=False)
            return True
        except Exception as e:
            print("Error in fetching connection data !!!", " \nError: ", e)
            ti.xcom_push(key='any_error_extract', value=True)
            return False

    @task(task_id="transform")
    def transform(data, ti):
        any_error = ti.xcom_pull(task_ids=['extract'], key='any_error_extract')
        if any_error != False:
            engine_object = Enginecreater()
            try:
                hostname = ti.xcom_pull(task_ids='extract', key='hostname')
                print("Hostname: ", hostname)
                portnumber = ti.xcom_pull(task_ids='extract', key='portnumber')
                print("portnumber: ", portnumber)
                username = ti.xcom_pull(task_ids='extract', key='username')
                print("username: ", username)
                password = ti.xcom_pull(task_ids='extract', key='password')
                database_name = ti.xcom_pull(task_ids='extract', key='database_name')
                print("database_name: ", database_name)
                test_type = ti.xcom_pull(task_ids='extract', key='test_type')
                test_name = ti.xcom_pull(task_ids='extract', key='test_purpose')
                value = ti.xcom_pull(task_ids='extract', key='test_purpose_value')
                value = json.loads(value)
                print("Test Purpose Values: ", value)
                table = ti.xcom_pull(task_ids='extract', key='test_table')
                column = ti.xcom_pull(task_ids='extract', key='test_column')

                conn = psycopg2.connect(user = username, 
                                host = hostname,
                                password = password,
                                port = int(portnumber),
                                database = database_name)
                
                print("connected successfully.")
                
                testobj = PostgresTests(conn)
                testobj = testobj.test_list()
                result = None

                if test_type == 1:
                    result = testobj[test_name](table, value)
                else:
                    result = testobj[test_name](table, column, value)

                ti.xcom_push(key="any_error_transform", value=False)
                return result

            except Exception as e:
                ti.xcom_push(key="any_error_transform", value=True)
                print("Error in performing test !!!", " \nError: ", e)
                return dict()
        else:
            print("in else ", any_error)
            return dict()

    @task()
    def load(test_result, ti):
        engine_object = Enginecreater()
        test_id = None
        try:
            any_error_of_extract = ti.xcom_pull(task_ids='extract', key='any_error_extract')
            test_id = ti.xcom_pull(task_ids='extract', key='test_id')
            any_error_of_transform = ti.xcom_pull(task_ids='transform', key='any_error_transform')

            if any_error_of_extract:
                print("Provided invalid data to extract task!")
                raise Exception("Provided invalid data to extract task!")

            if any_error_of_transform:
                print("Error in transformation task!")
                raise Exception("Error in transformation task!")

            if len(test_result) == 0:
                print("No metrics get from transform !")
                raise Exception("No data from transform task!")

            update_query = text("UPDATE connector_test SET status = :status, result = :result WHERE test_id = :test_id")
            success = 3
            with engine_object.engine.connect() as connection:
                connection.execute(update_query, status=success, result=json.dumps(test_result), test_id=test_id)

            engine_object.session.close()
        
        except Exception as e:
            print("====================================")
            print("Error: ", e)
            print("====================================")

            print("Test Id: ", test_id)
            test_info_data = Table('connector_test', MetaData(), autoload_with=engine_object.engine)
            update_query = (
                update(test_info_data)
                .where(test_info_data.columns.test_id == test_id)
                .values(status=4)
            )
            engine_object.session.execute(update_query)
            engine_object.session.commit()
            engine_object.session.close()
            raise AirflowFailException("Error: ", e)
    
    data = extract()
    test_result = transform(data)
    load(test_result)

test_pipline()
