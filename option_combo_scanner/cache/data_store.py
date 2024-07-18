import time

import pandas as pd


class DataStore:
    """
    Only for Stroing Historical Price Data
    """

    data_store = {}
    MAX_CACHE_TIME_IN_SECONDS = 3000

    @staticmethod
    def store_data(key, df):
        """
        Store a Pandas DataFrame in the data store with the given key.
        """
        DataStore.data_store[key] = (df, time.time())

    @staticmethod
    def get_data(key):
        """
        Retrieve a Pandas DataFrame from the data store using the given key.
        If the DataFrame is older than 30 minutes, return None.
        """
        if key in DataStore.data_store:
            df, timestamp = DataStore.data_store[key]
            if (
                time.time() - timestamp <= DataStore.MAX_CACHE_TIME_IN_SECONDS
            ):  # 30 minutes in seconds
                return df
            else:
                del DataStore.data_store[key]  # Remove the expired DataFrame
        return None


# # Example usage
# data_store = DataStore()

# df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
# data_store.store_data('my_data', df)

# # Access the DataFrame within 30 minutes
# print(data_store.get_data('my_data'))

# # Wait for more than 30 minutes
# import time

# time.sleep(1801)

# # Try to access the DataFrame after 30 minutes (should return None)
# print(data_store.get_data('my_data'))
