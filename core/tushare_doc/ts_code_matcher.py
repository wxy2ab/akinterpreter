import pickle
import re
import os
import pandas as pd
import jieba
from collections import defaultdict
from fuzzywuzzy import fuzz
from rapidfuzz import fuzz as rfuzz

class StringMatcher:
    def __init__(self, df, index_cache, index_column='content', result_column='ts_code'):
        self.df = df
        self.index_column = index_column
        self.result_column = result_column
        self.inverted_index = self._build_inverted_index(index_cache)

    def _build_inverted_index(self, index_cache):
        if os.path.exists(index_cache):
            print("Loading inverted index from cache...")
            with open(index_cache, 'rb') as f:
                return pickle.load(f)
        
        print("Building inverted index...")
        inverted_index = defaultdict(list)
        for _, row in self.df.iterrows():
            words = jieba.cut(row[self.index_column])
            for word in words:
                inverted_index[word].append(row.to_dict())
        
        print("Saving inverted index to cache...")
        with open(index_cache, 'wb') as f:
            pickle.dump(inverted_index, f)
        
        return inverted_index

    def exact_match(self, query):
        match = self.df[self.df[self.index_column].str.contains(query, case=False, na=False)]
        return match[self.result_column].iloc[0] if not match.empty else None

    def regex_match(self, query):
        pattern = re.compile(query, re.IGNORECASE)
        match = self.df[self.df[self.index_column].apply(lambda x: bool(pattern.search(str(x))))]
        return match[self.result_column].iloc[0] if not match.empty else None

    def fuzzywuzzy_match(self, query, threshold=80):
        best_match = max(self.df.itertuples(), key=lambda x: fuzz.partial_ratio(query, getattr(x, self.index_column)))
        return getattr(best_match, self.result_column) if fuzz.partial_ratio(query, getattr(best_match, self.index_column)) >= threshold else None

    def rapidfuzz_match(self, query, threshold=80):
        best_match = max(self.df.itertuples(), key=lambda x: rfuzz.partial_ratio(query, getattr(x, self.index_column)))
        return getattr(best_match, self.result_column) if rfuzz.partial_ratio(query, getattr(best_match, self.index_column)) >= threshold else None

    def inverted_index_match(self, query):
        query_words = jieba.cut(query)
        candidates = []
        for word in query_words:
            candidates.extend(self.inverted_index.get(word, []))
        
        if not candidates:
            return None

        candidates_df = pd.DataFrame(candidates)
        best_match = max(candidates_df.itertuples(), key=lambda x: fuzz.partial_ratio(query, getattr(x, self.index_column)))
        return getattr(best_match, self.result_column)

class TsCodeMatcher(StringMatcher):
    def __init__(self, index_column='content', result_column='ts_code'):
        df = pickle.load(open('./json/tushare_code_20240804.pickle', 'rb'))
        index_cache = f"./json/tushare_code_20240804_index_{index_column}_{result_column}.pickle"
        df['content'] = df['ts_code'] + ',' + df['name'] + ',' + df['type']
        super().__init__(df, index_cache, index_column, result_column)
    def __getitem__(self, query):
        return self.rapidfuzz_match(query)