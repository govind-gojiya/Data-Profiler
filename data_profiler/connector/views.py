from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import *
from django.contrib import messages
from .connectors import PostgresConnector, SnowflakeConnector
from .models import Connectiondata, Tabledata, Columndata, Test
from user_group_management.models import Group, Member
from .utils import generate_cron_expression, trigger_etl_cycle, get_etl_status, create_etl_dag
import json
from datetime import datetime
from django.db.models import Q, F
from django.http import JsonResponse
from pandasai import SmartDataframe
import pandas as pd
import shutil
from django.utils import timezone
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


CONNECTOR_DATABASES = ['Postgres', 'Snowflake']
CONNECTOR_FORMS = {
    'Postgres': PostgresForm, 
    'Snowflake': SnowflakeForm,
}
CONNECTOR = {
    'Postgres': PostgresConnector, 
    'Snowflake': SnowflakeConnector,
}
ETL = {
    'Postgres': 'dynamic_postgres_etl_dag', 
    'Snowflake': 'dynamic_snowflake_etl_dag',
}

TEST_PIPLINE = {
    'Postgres': 'test_pipline_postgres', 
    'Snowflake': 'test_pipline_snowflake',
}


TEST_PURPOSE = [
    ("Table", "Number", "Table column count greater then"),
    ("Table", "Number", "Table column count lesser then"),
    ("Table", "Number", "Table row count greater then"),
    ("Table", "Number", "Table row count lesser then"),
    ("Column", "Number", "Column values grater then"),
    ("Column", "Number", "Column values less then"),
    ("Column", "Number", "Column values equal to"),
    ("Column", "Number", "Column values between "),
    ("Column", "Number", "Column minimum value"),
    ("Column", "Number", "Column maximum value"),
    ("Column", "String", "Column values startwith"),
    ("Column", "String", "Column values startwith (ignorecase)"),
    ("Column", "String", "Column values endwith"),
    ("Column", "String", "Column values endwith (ignorecase)"),
    ("Column", "String", "Column values contians"),
    ("Column", "String", "Column values contians (ignorecase)"),
    ("Column", "Boolean", "Column truthy values"),
    ("Column", "Boolean", "Column falsy values"),
]


@login_required
def connector_form(request):
    if request.method == 'POST':
        connector_database = request.POST['connector_database']
        index = CONNECTOR_DATABASES.index(connector_database)
        if index != -1:
            tables_list = None
            groups = None
            form = CONNECTOR_FORMS[connector_database](request.POST)
            if form.is_valid():
                test_connection = CONNECTOR[connector_database](form)
                if test_connection.connect():
                    tables_list = test_connection.tables_name()
                    if tables_list is not None:
                        user = request.user
                        groups = Group.objects.filter(owner=user, group_type=Group.GROUP)
                    else:
                        form = CONNECTOR_FORMS[connector_database]()
                        messages.warning(request, "Provide valid data, there is no table for given database !")
                else: 
                    form = CONNECTOR_FORMS[connector_database]()
                    messages.warning(request, "Provide valid data, Check for data given !")
            return render(request, 'connector-form.html', {'form': form, 'connector_database': connector_database, 'tables_list': tables_list, 'groups': groups})
        else:
            messages.warning(request, "Provide valid inputs.")
            return redirect('home_page')  
    else:
        messages.warning(request, "Unauthorize access !")
        return redirect('/dashboard')

@login_required
def add_connector_data(request):
    if request.method == 'POST':
        if 'connector_database' in request.POST:
            connector_database = request.POST['connector_database']
            index = CONNECTOR_DATABASES.index(connector_database)
            data = request.POST
            if index != -1:
                print("Form valid")
                form = CONNECTOR_FORMS[connector_database](request.POST)
                if form.is_valid():
                    connecter_object = CONNECTOR[connector_database](form)
                    user = request.user
                    database_type = connector_database
                    publish_to = data["visiablity"]
                    publish_status = [status[0] for status in Connectiondata.PUBLISH_TYPE if status[1] == publish_to][0]
                    publish_group = None
                    if publish_to == 'Group':
                        publish_group = Group.objects.filter(pk=data["group_to_visiable"]).first()
                    if publish_to == "Organization":
                        publish_group = Group.objects.filter(group_type=Group.ORGANIZATION, members__user_id=user.id, members__status=Member.APPROVED).first()
                    if publish_group is None and publish_to != "Public":
                        publish_status = Connectiondata.PERSONAL
                    database_name = data["database_name"]
                    connection_details = connecter_object.get_connection_json()
                    
                    connection_data = Connectiondata.objects.create(owner=user, database_type=database_type, publish_status=publish_status, publish_to_group=publish_group, database_name=database_name, connection_details=json.dumps(connection_details))
                    connecter_object.connect()
                    payload = connecter_object.get_connection_json()
                    payload['meta_id'] = connection_data.meta_id

                    tables_list = connecter_object.tables_name()
                    for table in tables_list:
                        print("Get table names")
                        if data.get(f"table_{table}"):
                            scheduled = generate_cron_expression(data[f"schedule_type_{table}"], data[f"schedule_value_{table}"])
                            dag_id = str(user.username.split(' ')[0] + "_" + table + "_" + datetime.now().strftime("%m%d%Y%H%M"))
                            table_data = Tabledata.objects.create(metadata=connection_data, name=table, scheduled=scheduled, dag_id=dag_id)
                            columns_with_dt_list = connecter_object.get_columns_with_type(table)
                            
                            for name, datatype in columns_with_dt_list:
                                Columndata.objects.create(table=table_data, name=name, datatype=datatype)
                            print("Added table and column to db")
                            payload['table_info'] = [table_data.name, table_data.table_id]
                            payload['dag_name'] = dag_id
                            payload['schedule_time'] = scheduled
                            status = create_etl_dag(payload, ETL[connector_database])
                            if status is not None:
                                dag_run_id, etl_status = trigger_etl_cycle(dag_id)
                                
                                if dag_run_id is not None and etl_status is not None:
                                    table_data.dag_run_id = dag_run_id
                                    table_data.status = [status[0] for status in Tabledata.ETL_STATUS if status[1].lower() == etl_status.lower()][0]
                                    table_data.save()
                            else:
                                messages.warning(request, "Something went wrong ! Dag is not created.")
                            
                    messages.success(request, "Data Added successfully.") 
                    return redirect('/dashboard')
                else:
                    messages.warning(request, "Form is not valid.")
            else:
                messages.warning(request, "Form is not valid.")
        else:
            messages.warning(request, "Connector database not provided.")
    
    return redirect(connector_form)

@login_required
def dashboard(request):
    user = request.user
    groups = Group.objects.filter(
        Q(members__user_id=user.id) | Q(owner_id=user.id),
        members__status=Member.APPROVED
    )
    group_ids = groups.values_list('group_id', flat=True)
    connections_of_user = Connectiondata.objects.filter(
        Q(owner=user) | Q(publish_status=Connectiondata.PUBLIC) | Q(publish_status__in=[Connectiondata.GROUP, Connectiondata.ORGANIZATION], publish_to_group__in=group_ids)
    ).select_related('publish_to_group', 'owner').values('meta_id', 'publish_status', 'database_type', 'database_name', 'publish_to_group__name', 'publish_to_group__owner', 'publish_to_group__owner__username', 'owner__username', 'owner')
    return render(request, 'index.html', {"connections_of_user": connections_of_user, "user": user})

@login_required
def get_table_data(request, meta_id):
    try:
        connection_details = Connectiondata.objects.get(pk=meta_id)
        tables_data = Tabledata.objects.filter(metadata=connection_details).prefetch_related('columns', 'metric').annotate(total_case=F('etl_pass')+F('etl_fail')+F('etl_abort'), row_count=F('metric__row_count')).distinct('table_id')
        any_table_running = False
        for table_data in tables_data:
            if table_data.status not in [Tabledata.SUCCESS, Tabledata.FAILED]:
                etl_status = get_etl_status(table_data.dag_id, table_data.dag_run_id)
                if etl_status is not None:
                    status_flag = [status[0] for status in Tabledata.ETL_STATUS if status[1].lower() == etl_status.lower()][0]
                    if status_flag != table_data.status:
                        table_data.status = status_flag
                        table_data.save()
                    if status_flag not in [Tabledata.SUCCESS, Tabledata.FAILED]:
                        any_table_running = True
            row_count = table_data.row_count
            table_data.metric_data = table_data.metric.all()
            table_data.columns_data = table_data.columns.all()
        return render(request, 'tables_data.html', {"connection_data": connection_details, 'tables_data': tables_data, "any_table_running": any_table_running})
    except Exception as e:
        print("Something went wrong!\nError: ", e)
        messages.warning(request, "Something went wrong!")
        return redirect('/dashboard')


@login_required
def remove_connector_details(request, meta_id):
    try:
        connection_details = Connectiondata.objects.get(
            Q(owner=request.user) | Q(publish_status__in=[Connectiondata.GROUP, Connectiondata.ORGANIZATION], publish_to_group__owner=request.user),
            pk=meta_id
        )
        connection_details.delete()
        return redirect('/dashboard')
    except Connectiondata.DoesNotExist:
        messages.warning(request, "Something went wrong, connection details not found. Invalid request !")
        return redirect('/dashboard')


@login_required
def run_etl_for_connector(request, meta_id):
    try:
        tables_data = Tabledata.objects.filter(metadata__meta_id=meta_id)
        for table_data in tables_data: 
            dag_run_id, etl_status = trigger_etl_cycle(table_data.dag_id)
            table_data.dag_run_id = dag_run_id
            table_data.status = [status[0] for status in Tabledata.ETL_STATUS if status[1].lower() == etl_status.lower()][0]
            table_data.save()
        messages.success(request, "All ETL Pipiline manually trigger to run now.")
        return redirect('get_table_data', meta_id=meta_id)
    except Exception as e:
        messages.warning(request, "Something went wrong !")
        print("Error: ", e)
        return redirect('/dashboard')


@login_required
def run_etl_for_table(request, meta_id):
    try:
        table_id = request.POST['table_id']
        table_data = Tabledata.objects.get(table_id=table_id)
        if table_data:
            dag_run_id, etl_status = trigger_etl_cycle(table_data.dag_id)
            table_data.dag_run_id = dag_run_id
            table_data.status = [status[0] for status in Tabledata.ETL_STATUS if status[1].lower() == etl_status.lower()][0]
            table_data.save()
            messages.success(request, "ETL Pipiline Scheduled.")
            return redirect('get_table_data', meta_id=meta_id)
        else:
            messages.error(request, "You trying to run the etl for table having no connection data !")
            return redirect('/dashboard')
    except Exception as e:
        messages.warning(request, "Something went wrong !")
        print("Error: ", e)
        return redirect('/dashboard')

def get_last_etl_logs(request):
    dag_run_id = request.GET.get('dag_run_id')
    dag_run_id = dag_run_id.replace(' ', '+')
    dag_task = request.GET.get('dag_task')
    dag_id = request.GET.get('dag_id')
    if not dag_run_id and not dag_task and not dag_id:
        return JsonResponse({"error": str(e)}, status=500)
    else:
        try:
            url = f"{airflow_url}{dag_id}/dagRuns/{dag_run_id}/taskInstances/{dag_task}/logs/1"
            headers = {
                "Accept": "application/json"
            }
            print(url)
            response = requests.get(url, headers=headers, auth=(airflow_username, airflow_password))
            response_data = response.json()
            return JsonResponse(response_data)
        except Exception as e:
            print("Error: ", e)
            return JsonResponse({"error": str(e)}, status=500)
            

def get_current_data(request):
    table_id = request.POST.get("tableInfo")
    print("Table Id: ", table_id)
    try:
        table_data = Tabledata.objects.select_related('metadata').get(pk=table_id)
        connection_data = table_data.metadata.connection_details
        data = json.loads(connection_data)
        connector_obj = CONNECTOR[table_data.metadata.database_type](form=None, is_form=False, data=data)
        data, data_columns = connector_obj.get_all_data(table_data.name)
        return JsonResponse({"data": data, "data_columns": data_columns}, status=200)
    except Tabledata.DoesNotExist as e:
        print("Invalid request to get data!")
        messages.warning("Invalid request !")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def get_all_connectors(request):
    try:
        user = request.user
        groups = Group.objects.filter(
            Q(members__user_id=user.id) | Q(owner_id=user.id),
            members__status=Member.APPROVED
        )
        group_ids = groups.values_list('group_id', flat=True)
        connections_of_user = Connectiondata.objects.filter(
            Q(owner=user) | Q(publish_status=Connectiondata.PUBLIC) | Q(publish_status__in=[Connectiondata.GROUP, Connectiondata.ORGANIZATION], publish_to_group__in=group_ids)
        ).select_related('publish_to_group', 'owner').values('meta_id', 'publish_status', 'database_type', 'database_name', 'publish_to_group__name', 'publish_to_group__owner', 'publish_to_group__owner__username', 'owner__username', 'owner')
        return render(request, 'test-perform.html', {'connections_of_user': connections_of_user})
    except Exception as e:
        print("Something is not right !\nError: ", e)
        messages.warning(request, "Something went wrong!")
        return redirect('/dashboard')


def get_test_form(request, meta_id):
    try:
        user = request.user
        table_list = Tabledata.objects.filter(metadata=meta_id).select_related('metadata')
        column_list = Columndata.objects.filter(table__in=table_list).values('column_id', 'name', 'table__table_id')
        connector_detail = table_list[0].metadata
        return render(request, 'test-form.html', {'table_list': table_list, 'column_list': column_list, "connector_detail": connector_detail})
    except Exception as e:
        print("Something is not right !\nError: ", e)
        messages.warning(request, "Something went wrong!")
        return redirect('/dashboard')


def get_testcase_for_form(request):
    try:
        test_type = request.GET.get('test_type')
        data = request.GET.get('data')
        test_cases = None
        if test_type == '1':
            test_cases = [[test[2], test[1]] for test in TEST_PURPOSE if test[0] == "Table"]
        else:
            column_data = Columndata.objects.filter(pk=data).select_related('table__metadata').first()
            connector_detail = column_data.table.metadata
            connection_obj = CONNECTOR[connector_detail.database_type](form=None, is_form=False, data=connector_detail.connection_details)
            type_of_column = connection_obj.get_type_of_column(column_data.datatype)
            if type_of_column is not None:
                test_cases = [[test[2], test[1]] for test in TEST_PURPOSE if test[0] == "Column" and test[1] == type_of_column]
        return JsonResponse({"data": test_cases}, status=200)

    except Exception as e:
        print("Something went wrong ! \nError: ", e)
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def add_test(request):
    try:
        test_type = request.POST.get('test_type')
        test_type_name = None
        if test_type == '1':
            test_type_name = "Table"
        if test_type == '2':
            test_type_name = "Column"
        testcase_name = request.POST.get('testcase_name')
        meta_id = request.POST.get('connector_detail')
        if any(test_type_name == item[0] and testcase_name == item[2] for item in TEST_PURPOSE):
            test_name = request.POST.get('name')
            table_name = request.POST.get('table_name')
            column_name = request.POST.get('column_name')
            testpurpose_value = None
            if testcase_name == "Column values between ":
                testpurpose_value = { "min": request.POST.get('test_purpose_value_range_min'),"max": request.POST.get('test_purpose_value_range_max')}
            else:
                testpurpose_value = { "value": request.POST.get('test_purpose_value')}
            table = Tabledata.objects.filter(pk=table_name).select_related('metadata').first()
            column = Columndata.objects.get(pk=column_name)
            new_test = Test.objects.create(name=test_name, test_purpose=testcase_name, test_purpose_value= json.dumps(testpurpose_value), test_type=int(test_type), table=table, column=column, owner=request.user)

            connection_data = table.metadata
            payload = {}
            data = {
                "test_id": new_test.test_id,
                "test_type": new_test.test_type,
                "test_purpose": new_test.test_purpose,
                "test_purpose_value": new_test.test_purpose_value,
                "table": table.name,
                "column": column.name
            }
            payload["test_info"] = data
            payload["connection"] = connection_data.connection_details

            print("Payload: ", payload)

            dag_run_id, test_status = trigger_etl_cycle(TEST_PIPLINE[connection_data.database_type], payload)
                            
            if dag_run_id is not None and test_status is not None:
                new_test.dag_run_id = dag_run_id
                new_test.status = [status[0] for status in Tabledata.ETL_STATUS if status[1].lower() == test_status.lower()][0]
                new_test.save()

            return redirect('get_all_conn_to_test')
        else:
            messages.warning(request, "Test purpose not valid as per the test type!")
            return redirect('get_test_form', meta_id)
        
    except Exception as e:
        print("Something went wrong ! \nError: ", e)
        messages.warning(request, "Something went wrong!")
        return redirect('/test/get_all_connectors')


@login_required
def get_all_tests_performed(request):
    try:
        user = request.user
        groups = Group.objects.filter(
            Q(members__user_id=user.id) | Q(owner_id=user.id),
            members__status=Member.APPROVED
        )

        group_ids = groups.values_list('group_id', flat=True)
        connections_of_user = Connectiondata.objects.filter(
            Q(owner=user) | Q(publish_status=Connectiondata.PUBLIC) | Q(publish_status__in=[Connectiondata.GROUP, Connectiondata.ORGANIZATION], publish_to_group__in=group_ids)
        ).values_list('meta_id', flat=True)

        test_details = Test.objects.filter(table__metadata__meta_id__in=connections_of_user).select_related('table__metadata')
        for test in test_details:
            test.test_purpose_value = json.loads(test.test_purpose_value)
        return render(request, 'test-result.html', {'test_details': test_details})
    except Exception as e:
        print("Something is not right !\nError: ", e)
        messages.warning(request, "Something went wrong!")
        return redirect('/dashboard')
    
def chat_with_data(request):
    try:
        target_table = request.POST['targetTable']
        query = request.POST['query']
        try:
            table_data = Tabledata.objects.select_related('metadata').get(pk=target_table)
            connection_data = table_data.metadata.connection_details
            data = json.loads(connection_data)
            connector_obj = CONNECTOR[table_data.metadata.database_type](form=None, is_form=False, data=data)
            data, data_columns = connector_obj.get_all_data(table_data.name)
            pandas_data = pd.DataFrame(data, columns=data_columns)
            df = SmartDataframe(pandas_data, config={ 'open_charts': False })
            response = df.chat(query)
            print("Response: ", response)
            type_of_response = "String"
            data = None
            if isinstance(response, pd.DataFrame):
                type_of_response = "DataFrame"
                data = {}
                data["column"] = response.columns.tolist()
                if data["column"] == [0]:
                    response.reset_index(inplace=True)
                    data["column"] = response.columns.tolist()
                data["values"] = response.values.tolist()
                print(data)
            elif isinstance(response, str) and response.find("exports/charts/") != -1:
                response_index = response.find("exports/charts")
                timestamp_str = timezone.now().strftime("%Y%m%d%H%M%S")
                destination_path = "static/charts/" +  request.user.username + "_" + timestamp_str + "." + response.split('.')[-1]
                shutil.copy(response, destination_path)
                os.remove(response)
                data = destination_path
                type_of_response = "Image"
            else:
                data = str(response)
            return JsonResponse({"data": data, "type_of_data": type_of_response, "query": query.title()})
        except Tabledata.DoesNotExist as e:
            print("Invalid request to get data!")
            return JsonResponse({"error": str(e)}, status=500)
    except Exception as e:
        print("Something went wrong ! \nError: ", e)
        return JsonResponse({"error": str(e)}, status=500)