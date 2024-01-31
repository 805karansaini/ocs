from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.database_connector import DatabaseConnector

logger = CustomLogger.logger

DB_CONN = DatabaseConnector()


class SqlQueries:
    def __init__(self) -> None:
        pass

    @staticmethod
    def insert_order_preset(values_dict):
        query = SqlQueries.create_insert_query(
            table_name="order_specs",
            values_dict=values_dict,
        )

        # Execute the query
        return SqlQueries.execute_insert_query(query)

    @staticmethod
    def get_preset_orders(columns, where_clause=False):
        query = SqlQueries.create_select_query(
            table_name="order_specs",
            columns=columns,
        )

        # Execute the query
        return SqlQueries.execute_select_query(query)

    @staticmethod
    def update_preset_order(values_dict, where_clause=False):
        query = SqlQueries.create_update_query(
            table_name="order_specs",
            values_dict=values_dict,
            where_clause=where_clause,
        )

        # Execute the query
        return SqlQueries.execute_update_query(query)

    @staticmethod
    def insert_into_orders(values_dict):
        query = SqlQueries.create_insert_query(
            table_name="orders",
            values_dict=values_dict,
        )

        # Execute the query
        return SqlQueries.execute_insert_query(query)

    @staticmethod
    def get_orders(columns, where_clause=False):
        query = SqlQueries.create_select_query(
            table_name="orders",
            columns=columns,
            where_clause=where_clause,
        )

        # Execute the query
        return SqlQueries.execute_select_query(query)

    @staticmethod
    def insert_into_executions(values_dict):
        query = SqlQueries.create_insert_query(
            table_name="executions",
            values_dict=values_dict,
        )

        # Execute the query
        return SqlQueries.execute_insert_query(query)

    @staticmethod
    def update_orders(values_dict, where_clause=False):
        query = SqlQueries.create_update_query(
            table_name="orders",
            values_dict=values_dict,
            where_clause=where_clause,
        )

        # Execute the query
        return SqlQueries.execute_update_query(query)

    # Create Insert Query
    @staticmethod
    def create_insert_query(table_name, values_dict):
        query = f"""
            INSERT INTO {table_name} (
        """

        for key, value in values_dict.items():
            query += f"{key},"

        query = query[:-1] + ") VALUES ("

        for key, value in values_dict.items():
            query += f"'{value}',"

        query = query[:-1] + ")"

        return query

    # Create Update Query
    @staticmethod
    def create_update_query(table_name, values_dict, where_clause=False):
        query = f"""
            UPDATE {table_name}
            SET
        """

        for key, value in values_dict.items():
            query += f"{key} = '{value}',"

        query = query[:-1]

        if where_clause:
            query += f""" {where_clause} """

        return query

    # Create Select Query
    @staticmethod
    def create_select_query(table_name, columns=None, where_clause=False):
        query = f"""
            SELECT {columns}
            FROM {table_name}
        """

        if where_clause:
            query += f""" {where_clause}"""

        return query

    # Create Delete Query
    @staticmethod
    def create_delete_query(table_name, where_clause=False):
        query = f"""
            DELETE FROM {table_name}
        """

        if where_clause:
            query += f"""
                WHERE {where_clause}
            """

        return query

    # Execute Insert Query
    @staticmethod
    def execute_insert_query(query):
        connection = DB_CONN.get_connection_to_database()

        res = False, False
        if connection is None:
            return res

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(query)

            # Get the last insert ID
            last_insert_id = cursor.lastrowid

            if cursor.rowcount > 0:
                return True, last_insert_id
            else:
                return res
        except Exception as e:
            logger.error(
                f"Insert Query: {query}\nException occurred while executing query: {e}"
            )
            return res
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # Execute Select Query
    @staticmethod
    def execute_select_query(query):
        """
        Returns a list of dictionaries
        """
        connection = DB_CONN.get_connection_to_database()

        res = False
        if connection is None:
            return res

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(query)

            # Fetch Result
            res = cursor.fetchall()

            return res

        except Exception as e:
            logger.error(
                f"Select Query: {query}\nException occurred while executing query: {e}"
            )
            return res
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # Execute Update Query
    @staticmethod
    def execute_update_query(query):
        """
        Returns True if rows are updated
        """
        connection = DB_CONN.get_connection_to_database()

        res = False
        if connection is None:
            return res

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(query)

            if cursor.rowcount > 0:
                return True
            else:
                return res

        except Exception as e:
            logger.error(
                f"Update Query: {query}\nException occurred while executing query: {e}"
            )
            return res
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # Execute Delete Query
    @staticmethod
    def execute_delete_query(query):
        """
        Returns True if rows are deleted
        """
        connection = DB_CONN.get_connection_to_database()

        res = False
        if connection is None:
            return res

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(query)

            if cursor.rowcount > 0:
                return True
            else:
                return res

        except Exception as e:
            logger.error(
                f"Delete Query: {query}\nException occurred while executing query: {e}"
            )
            return res
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
