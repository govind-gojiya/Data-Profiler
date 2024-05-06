# Data Profiler

## Project setup steps :
1. Create venv for project
2. Download requirement dependencies
    - pip install -r requirement.txt
3. Change the config info in airflow/dags/config/connection.py file
4. Set env for Django also at data_profiler/.env file
4. start the airflow server
    - airflow standalone
5. copy airflow/dags folder at ~/airflow

## Start the project :
Open two terminals having venv activated.
### In one terminal : 
`airflow standalone`
### In another terminal :
`python3 data_profiler/manage.py runserver`
