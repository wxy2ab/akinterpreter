import pandas as pd
from functools import wraps
import inspect

def tsdata(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        limit = kwargs.pop('limit', None)
        offset = kwargs.pop('offset', None)
        if limit is None:
            limit = 1000

        all_data = []
        while True:
            kwargs['limit'] = limit
            kwargs['offset'] = offset
            df = func(*args, **kwargs)
            all_data.append(df)

            if len(df) < limit:
                break

            offset = offset + limit if offset else limit

        result_df = pd.concat(all_data, ignore_index=True)
        return result_df

    return wrapper