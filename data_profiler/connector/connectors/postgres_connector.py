import psycopg2
from django.contrib import messages
import json


class PostgresConnector():
    numeric_data_types = ["smallint", "integer", "bigint", "decimal", "numeric", "real", "double precision", "smallserial", "serial", "bigserial", "numeric"]
    boolean_data_types = ["boolean"]
    string_data_types = ["character", "text"]

    def __init__(self, form, is_form=True, data=None):
        if is_form:
            self.hostname = form.cleaned_data['hostname']
            self.username = form.cleaned_data['username']
            self.password = form.cleaned_data['password']
            self.portnumber = form.cleaned_data['portnumber']
            self.database_name = form.cleaned_data['database_name']
        else: 
            if type(data) == str:
                data = json.loads(data)
            self.hostname = data['hostname']
            self.username = data['username']
            self.password = data['password']
            self.portnumber = data['portnumber']
            self.database_name = data['database_name']

    def connect(self):
        try: 
            self.conn = psycopg2.connect(user = self.username, 
                            host = self.hostname,
                            password = self.password,
                            port = int(self.portnumber),
                            database = self.database_name)
            return True
        except Exception as e:
            print("Error While connecting! \n", e)
            return False

    def tables_name(self):
        if not self.conn:
            None        
        cursor = self.conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
        tables_list = [table[0] for table in cursor.fetchall()]
        return tables_list
    
    def get_connection_json(self):
        conntion_details = {
            'hostname': self.hostname,
            'username': self.username,
            'password': self.password,
            'portnumber': self.portnumber,
            'database_name': self.database_name
        }

        return conntion_details

    def get_columns_with_type(self, table_name):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (table_name,))
        columns = cursor.fetchall()
        column_info = [(col[0], col[1]) for col in columns]
        cursor.close()
        return column_info
    
    def get_all_data(self, table_name):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        return rows, columns
    
    def get_type_of_column(self, column_type):

        for numeric_data_type in self.numeric_data_types:
            if column_type.lower().startswith(numeric_data_type.lower()):
                return "Number"
            
        for string_data_type in self.string_data_types:
            if column_type.lower().startswith(string_data_type.lower()):
                return "String"
            
        for boolean_data_type in self.boolean_data_types:
            if column_type.lower().startswith(boolean_data_type.lower()):
                return "Boolean"
            
        return None