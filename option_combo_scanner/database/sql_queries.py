from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.database_connector import DatabaseConnector

logger = CustomLogger.logger

DB_CONN = DatabaseConnector()


class SqlQueries:
    def __init__(self) -> None:
        pass

    @staticmethod
    def insert_into_db_table(table_name, values_dict):
        query = SqlQueries.create_insert_query(
            table_name=table_name,
            values_dict=values_dict,
        )

        # Execute the query
        return SqlQueries.execute_insert_query(query)

    @staticmethod
    def select_from_db_table(table_name, columns, where_clause=False):
        query = SqlQueries.create_select_query(
            table_name=table_name,
            columns=columns,
        )

        # Execute the query
        return SqlQueries.execute_select_query(query)

    @staticmethod
    def update_db_table(table_name, values_dict, where_clause=False):
        query = SqlQueries.create_update_query(
            table_name=table_name,
            values_dict=values_dict,
            where_clause=where_clause,
        )

        # Execute the query
        return SqlQueries.execute_update_query(query)

    @staticmethod
    def delete_from_db_table(table_name, where_clause=False):
        query = SqlQueries.create_delete_query(
            table_name=table_name,
            where_clause=where_clause,
        )

        # Execute the query
        return SqlQueries.execute_delete_query(query)

    # Create Insert Query
    @staticmethod
    def create_insert_query(table_name, values_dict):
        query = f"""
            INSERT INTO {table_name} (
        """

        for key, value in values_dict.items():
            query += f"`{key}`,"

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
            query += f"`{key}` = '{value}',"

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
                {where_clause}
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

    @staticmethod
    def run_config_update_transaction(common_config_dict, list_of_config_legs_dict):
        """
        Returns True if the transaction is successful
        """
        list_of_all_queries = []
        # list_of_all_queries.append(
        #     SqlQueries.create_delete_query(
        #         table_name="config_table", where_clause=" WHERE `config_id` > 0;"
        #     )
        # )
        list_of_all_queries.append(
            SqlQueries.create_insert_query(
                table_name="config_table", values_dict=common_config_dict
            )
        )

        connection = DB_CONN.get_connection_to_database()

        if connection is None:
            return False, False

        try:
            cursor = connection.cursor(dictionary=True)

            # Start the transaction
            connection.start_transaction()

            for query in list_of_all_queries:
                cursor.execute(query)
            if cursor.rowcount < 1:
                raise "Unable to insert common config in the database"

            # Get the last insert ID
            config_id = cursor.lastrowid

            for config_leg_dict in list_of_config_legs_dict:
                config_leg_dict["config_id"] = config_id
                query = SqlQueries.create_insert_query(
                    table_name="config_legs_table", values_dict=config_leg_dict
                )
                cursor.execute(query)

            # If all queries are executed successfully, commit the transaction
            connection.commit()

            return True, config_id

        except Exception as e:
            # Log the error and rollback the transaction in case of any exception
            logger.error(f"Transaction failed. Exception occurred: {e}")
            connection.rollback()
            return False, False

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
