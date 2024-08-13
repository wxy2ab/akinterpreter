



import akshare as ak



def get_index_dict()->dict:
    result = {}
    index_stock_info_df = ak.index_stock_info()
    for _, row in index_stock_info_df.iterrows():
        result[row.at["index_code"]] = row.at["display_name"]
    return result


index_code=get_index_dict()