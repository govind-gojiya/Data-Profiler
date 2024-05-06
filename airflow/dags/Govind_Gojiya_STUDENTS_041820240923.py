from sqlalchemy import text, update, Table, MetaData
import pendulum
import sys
sys.path.insert(0, "/home/govind/airflow/dags/config")
sys.path.insert(1, "/home/govind/airflow/dags/util")
from config.connection import Enginecreater
from util.matrics_calculation import get_metric_json
from airflow.decorators import dag, task
import snowflake.connector as sf
import pandas as pd
from datetime import datetime, timezone
from airflow.exceptions import AirflowFailException
import json


def get_table_size(connection, schema_name, table_name):

    query = f"SELECT bytes FROM INFORMATION_SCHEMA.tables WHERE TABLE_NAME='{0}';".format(str(table_name).upper())

    try:
        with connection.cursor() as cursor:
            result = cursor.execute(query)
            row = result.fetchone()
            if row[0] is not None:
                total_size_bytes = row[0]
                return total_size_bytes
            else:
                return 0
    except Exception as e:
        print("Error while getting bytes size: ", e)
        return 0    

@dag(
    dag_id="Govind_Gojiya_STUDENTS_041820240923",
    schedule="0 0 * * 6",
    catchup=False,
    start_date=pendulum.datetime(2024, 4, 4, tz="UTC"),
    is_paused_upon_creation=False,
    tags=["etl", "snowflake"],
)
def etl_pipline():
    
    @task(task_id="extract")
    def extract(ti, **kwargs):
        try:
            engine_object = Enginecreater()
            dag_run_id = kwargs["run_id"]
            update_dag_run_query = text("UPDATE connector_tabledata SET dag_run_id = :dag_run_id WHERE table_id = :table_id")
            with engine_object.engine.connect() as connection:
                connection.execute(update_dag_run_query, dag_run_id=dag_run_id, table_id=36)
            
            account = 'wglocal-bk45434'
            username = 'VTOMASUTHAR'
            password = '123Vyoma'
            database_name = 'newdb'
            
            ti.xcom_push(key='account', value=account)
            ti.xcom_push(key='username', value=username)
            ti.xcom_push(key='password', value=password)
            ti.xcom_push(key='database_name', value=database_name)
            ti.xcom_push(key='table_name', value='STUDENTS')
            ti.xcom_push(key='table_id', value=36)
            ti.xcom_push(key='any_error_extract', value=False)
            return True
        except Exception as e:
            print("Error in fetching connection data !!!", " \nError: ", e)
            ti.xcom_push(key='any_error_extract', value=True)
            return False

    @task(task_id="transform")
    def transform(table_info, ti):
        any_error = ti.xcom_pull(task_ids=['extract'], key='any_error_extract')
        if any_error != False:
            engine_object = Enginecreater()
            try:
                account = ti.xcom_pull(task_ids='extract', key='account')
                print("Account: ", account)
                username = ti.xcom_pull(task_ids='extract', key='username')
                print("Username: ", username)
                password = ti.xcom_pull(task_ids='extract', key='password')
                database_name = ti.xcom_pull(task_ids='extract', key='database_name')
                print("Database name: ", database_name)
                table_name = ti.xcom_pull(task_ids='extract', key='table_name')
                print("Table name: ", table_name)

                conn = sf.connect(user = username,
                                password = password,
                                account = account,
                                database = database_name)
                
                print("connected successfully.")
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                print("successfully get all data.\nData: ", rows)
                columns = [desc[0] for desc in cursor.description]
                data = pd.DataFrame(rows, columns=columns)

                table_size = get_table_size(conn, 'public', table_name)

                metric = get_metric_json(data)
                metric['table_columns'] = columns
                metric['table_size_bytes'] = table_size
                ti.xcom_push(key="any_error_transform", value=False)
                return metric

            except Exception as e:
                ti.xcom_push(key="any_error_transform", value=True)
                print("Error in fetching details !!!", " \nError: ", e)
                return dict()
        else:
            return dict()

    @task()
    def load(metric_data, ti):
        engine_object = Enginecreater()
        table_id = None
        try:
            any_error_of_extract = ti.xcom_pull(task_ids='extract', key='any_error_extract')
            table_id = ti.xcom_pull(task_ids='extract', key='table_id')
            any_error_of_transform = ti.xcom_pull(task_ids='transform', key='any_error_transform')

            if any_error_of_extract:
                print("Provided invalid data to extract task!")
                raise Exception("Provided invalid data to extract task!")

            if any_error_of_transform:
                print("Error in transformation task!")
                raise Exception("Error in transformation task!")

            if len(metric_data) == 0:
                print("No metrics get from transform !")
                raise Exception("No data from transform task!")
            
            table_cols = metric_data.get('table_columns')
            row_count = metric_data.get('row_count')
            col_count = metric_data.get('col_count')
            table_size_bytes = metric_data.get('table_size_bytes')

            del metric_data['table_columns']
            del metric_data['row_count']
            del metric_data['col_count']
            del metric_data['table_size_bytes']

            timestamp_value = datetime.now(timezone.utc)

            insert_query = text("INSERT INTO connector_metric (row_count, col_count, size, metric_value, table_id, timestamp) VALUES (:row_count, :col_count, :size, :metric_value, :table_id, :timestamp)")
            with engine_object.engine.connect() as connection:
                connection.execute(insert_query, row_count=row_count, col_count=col_count, size=table_size_bytes, metric_value=json.dumps(metric_data), table_id=table_id, timestamp=timestamp_value)

            for col in table_cols:
                col_metric = metric_data.get(col)
                update_query = text("UPDATE connector_columndata SET last_data = :col_metric WHERE lower(name) = lower(:col) AND table_id = :table_id")
                with engine_object.engine.connect() as connection:
                    connection.execute(update_query, col_metric=json.dumps(col_metric), col=col, table_id=table_id)

            get_table_pass_query = 'SELECT "etl_pass" FROM connector_tabledata WHERE table_id = :table_id'
            update_table_pass_query = "UPDATE connector_tabledata SET etl_pass = :etl_pass WHERE table_id = :table_id"
            with engine_object.engine.connect() as connection:
                result = connection.execute(text(get_table_pass_query), table_id=table_id)
                etl_last_status = result.fetchone()[0]
                print("Last ETL Pass Count: ", etl_last_status)
                etl_pass = etl_last_status + 1
                connection.execute(text(update_table_pass_query), etl_pass=etl_pass, table_id=table_id)

        except Exception as e:
            print("====================================")
            print("Error: ", e)
            print("====================================")

            get_table_fail_query = 'SELECT "etl_fail" FROM connector_tabledata WHERE table_id = :table_id'
            update_table_fail_query = "UPDATE connector_tabledata SET etl_fail = :etl_fail WHERE table_id = :table_id"
            with engine_object.engine.connect() as connection:
                result = connection.execute(text(get_table_fail_query), table_id=table_id)
                etl_last_status = result.fetchone()[0]
                print("Last ETL Fail Count: ", etl_last_status)
                etl_fail = etl_last_status + 1
                connection.execute(text(update_table_fail_query), etl_fail=etl_fail, table_id=table_id)

            raise AirflowFailException("Error: ", e)
    
    data = extract()
    metric_data = transform(data)
    load(metric_data)

etl_pipline()
