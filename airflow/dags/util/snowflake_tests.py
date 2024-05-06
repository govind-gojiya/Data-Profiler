import snowflake.connector as sf


class SnowflakeTests():

    def __init__(self, conn):
        self.conn = conn

    def test_list(self):
        return {
            "Table column count greater then": self.table_column_count_gt,
            "Table column count lesser then": self.table_column_count_lt,
            "Table row count greater then": self.table_row_count_gt,
            "Table row count lesser then": self.table_row_count_lt,
            "Column minimum value": self.column_min,
            "Column maximum value": self.column_max,
            "Column values grater then": self.column_values_gt,
            "Column values less then": self.column_values_lt,
            "Column values equal to": self.column_values_eql,
            "Column values between ": self.column_values_in_range,
            "Column values startwith": self.column_value_startswith,
            "Column values startwith (ignorecase)": self.column_value_startswith_ignorecase,
            "Column values endwith": self.column_value_endswith,
            "Column values endwith (ignorecase)": self.column_value_endswith_ignorecase,
            "Column values contians": self.column_value_contains,
            "Column values contians (ignorecase)": self.column_value_contains_ignorecase,
            "Column truthy values": self.column_value_truthy_count,
            "Column falsy values": self.column_value_falsy_count,
        }

    def table_column_count_gt(self, table_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name}
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                if len(columns) > value: 
                    return { "result": True}
                else:
                    return { "result": False}
        except Exception as e:
            print("Error while getting column count : ", e)
            return { "result": False}  
        
    def table_column_count_lt(self, table_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name}
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                if len(columns) < value: 
                    return { "result": True}
                else:
                    return { "result": False}
        except Exception as e:
            print("Error while getting column count : ", e)
            return { "result": False}
        
    def table_row_count_gt(self, table_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name}
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if { "result": len(rows)} > value: 
                    return { "result": True}
                else:
                    return { "result": False}
        except Exception as e:
            print("Error while getting row count : ", e)
            return { "result": False}  
        
    def table_row_count_lt(self, table_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name}
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if { "result": len(rows)} < value: 
                    return { "result": True}
                else:
                    return { "result": False}
        except Exception as e:
            print("Error while getting row count : ", e)
            return { "result": False}
        
    def column_min(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT MIN({clumn_name}") from {table_name}
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                if row is not None:
                    return { "result": row[0]}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for minimum in column : ", e)
            return { "result": 0}
        
    def column_max(self, table_name, column_name, value):
        value = value.get('value')
        query = f'SELECT MAX({clumn_name}") FROM {table_name}'
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                if row is not None:
                    return { "result": row[0]}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for maximum in column : ", e)
            return { "result": 0}
        
    def column_values_gt(self, table_name, column_name, value):
        print("Called column values greater then.")
        value = value.get('value')
        print("Value: ", value)
        query = f"""
            SELECT * from {table_name} WHERE {column_name} > {value}
        """
        try:
            with self.conn.cursor() as cursor:
                print("Query: ", query)
                cursor.execute(query)
                rows = cursor.fetchall()
                print("rows: ", rows)
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for greater values in column : ", e)
            return { "result": 0}  
        
    def column_values_lt(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} < {value}
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for lesser values in column : ", e)
            return { "result": 0}
        
    def column_values_eql(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} = {value}
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for equal values in column : ", e)
            return { "result": 0}
        
    def column_values_in_range(self, table_name, column_name, value):
        min = value.get('min')
        max = value.get('max')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} > {min} and {column_name} < {max}
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for range values in column : ", e)
            return { "result": 0}
    
    def column_value_startswith(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} LIKE '{value}%'
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for startswith values in column : ", e)
            return { "result": 0}
        
    def column_value_startswith_ignorecase(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} ILIKE '{value}%'
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for startswith values in column : ", e)
            return { "result": 0}
        
    def column_value_endswith(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} LIKE '%{value}'
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for endswith values in column : ", e)
            return { "result": 0}
        
    def column_value_endswith_ignorecase(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} ILIKE '%{value}'
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for endswith values in column : ", e)
            return { "result": 0}
        
    def column_value_contains(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} LIKE '%{value}%'
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for contains values in column : ", e)
            return { "result": 0}
        
    def column_value_contains_ignorecase(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} ILIKE '%{value}%'
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for contains values in column : ", e)
            return { "result": 0}
        
    def column_value_truthy_count(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} = true
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for truthy values in column : ", e)
            return { "result": 0}
        
    def column_value_falsy_count(self, table_name, column_name, value):
        value = value.get('value')
        query = f"""
            SELECT * from {table_name} WHERE {column_name} = false
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows is not None:
                    return { "result": len(rows)}
                else:
                    return { "result": 0}
        except Exception as e:
            print("Error while checking for falsy values in column : ", e)
            return { "result": 0}