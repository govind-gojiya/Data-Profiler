from airflow import DAG
from airflow.decorators import dag, task
from airflow.models import DagBag
from datetime import datetime
import shutil
import os
from airflow.api.common.experimental.trigger_dag import trigger_dag

@dag(
    dag_id="dynamic_snowflake_etl_dag",
    start_date=datetime(2024, 4, 17),
    schedule_interval=None,
    catchup=False
)
def dynamic_postgres_etl_dag():
    
    @task(task_id="create_dynamic_dag")
    def create_dynamic_dag(**kwargs):
        try:
            data = kwargs['dag_run'].conf
            # Load the original DAG file
            dag_bag = DagBag(os.path.dirname("dags/etl_pipline_snowflake.py"))
            new_dag_id = data["dag_name"]
            schedule_time = data["schedule_time"]
            if new_dag_id in dag_bag.dags:
                raise ValueError(f"DAG with ID '{new_dag_id}' already exists.")

            # Copy the original DAG file to a new file
            shutil.copyfile("dags/etl_pipline_snowflake.py", f"dags/{new_dag_id}.py")

            # Read the new DAG file and replace parameters
            new_dag_file_path = f"dags/{new_dag_id}.py"
            with open(new_dag_file_path, "r") as f:
                new_dag_file_content = f.read()

            new_dag_file_content = new_dag_file_content.replace('dag_id="etl_pipline_snowflake"', f'dag_id="{new_dag_id}"')
            new_dag_file_content = new_dag_file_content.replace('schedule="@once"', f'schedule="{schedule_time}"')
            new_dag_file_content = new_dag_file_content.replace("data = kwargs['dag_run'].conf", "")
            new_dag_file_content = new_dag_file_content.replace("data.get('account_identifier')", f"'{data.get('account_identifier')}'")
            new_dag_file_content = new_dag_file_content.replace("data.get('username')", f"'{data.get('username')}'")
            new_dag_file_content = new_dag_file_content.replace("data.get('password')", f"'{data.get('password')}'")
            new_dag_file_content = new_dag_file_content.replace("table_info = data.get('table_info')", "")
            new_dag_file_content = new_dag_file_content.replace("data.get('database_name')", f"'{data.get('database_name')}'")
            new_dag_file_content = new_dag_file_content.replace("value=table_info[0]", f"value='{data['table_info'][0]}'")
            new_dag_file_content = new_dag_file_content.replace("value=table_info[1]", f"value={data['table_info'][1]}")
            new_dag_file_content = new_dag_file_content.replace("table_id=0", f"table_id={data['table_info'][1]}")
    
            # Write the modified content back to the new DAG file
            with open(new_dag_file_path, "w") as f:
                f.write(new_dag_file_content)

            # Load the newly created DAG
            dag_bag = DagBag(os.path.dirname(new_dag_file_path))
            dag_bag.process_file(filepath=new_dag_file_path, only_if_updated=True)

            # run_id = f"manual_run_{datetime.now().isoformat()}"

            # trigger_dag(dag_id=new_dag_id, run_id=run_id, conf={})

        except Exception as e:
            raise ValueError(f"Error creating dynamic DAG: {e}")

    return create_dynamic_dag()

# Instantiate the DAG
dynamic_postgres_etl_dag_dag = dynamic_postgres_etl_dag()
