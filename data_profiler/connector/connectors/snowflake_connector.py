import snowflake.connector as sf
from django.contrib import messages
import json


class SnowflakeConnector():
    numeric_data_types = ["number", "decimal", "numeric", "int", "integer", "bigint", "smallint", "tinyint", "byteint", "float", "real", "double", "double precision"]
    boolean_data_types = ["boolean"]
    string_data_types = ["varchar", "char", "character", "text", "string"]

    def __init__(self, form, is_form=True, data=None):
        if is_form:
            self.username = form.cleaned_data['username']
            self.password = form.cleaned_data['password']
            self.account_identifier = form.cleaned_data['account_identifier']
            self.database_name = form.cleaned_data['database_name']
        else:
            if type(data) == str:
                data = json.loads(data)
            self.username = data['username']
            self.password = data['password']
            self.account_identifier = data['account_identifier']
            self.database_name = data['database_name']

    def connect(self):
        try: 
            self.conn = sf.connect(user = self.username,
                            password = self.password,
                            account = self.account_identifier,
                            database = self.database_name)
            return True
        except Exception as e:
            print("Error While connecting! \n", e)
            return False

    def tables_name(self):
        try:
            if not self.conn:
                return None        
            cursor = self.conn.cursor()
            tables_data = cursor.execute(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'PUBLIC' and TABLE_CATALOG='{self.database_name.upper()}'").fetchall()
            tables_list = [table[0] for table in tables_data]
            return tables_list
        except Exception as e:
            print("Error While fetching tables! \n", e)
            return None


    def get_connection_json(self):
        conntion_details = {
            'username': self.username,
            'password': self.password,
            'account_identifier': self.account_identifier,
            'database_name': self.database_name
        }

        return conntion_details

    def get_columns_with_type(self, table_name):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("DESCRIBE TABLE {}".format(table_name))
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