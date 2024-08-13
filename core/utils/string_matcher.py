import os
import pickle
import re
import jieba
from collections import defaultdict
from rapidfuzz import fuzz as rfuzz

class StringMatcher:
    def __init__(self, data_dict, index_cache=None):
        self.data_dict = data_dict
        self.index_cache = index_cache
        self.inverted_index = self._build_inverted_index()

    def _build_inverted_index(self):
        if self.index_cache and os.path.exists(self.index_cache):
            print("Loading inverted index from cache...")
            with open(self.index_cache, 'rb') as f:
                return pickle.load(f)
        
        print("Building inverted index...")
        inverted_index = defaultdict(list)
        for key, value in self.data_dict.items():
            words = jieba.cut(value)
            for word in words:
                inverted_index[word].append((key, value))
        
        if self.index_cache:
            print("Saving inverted index to cache...")
            with open(self.index_cache, 'wb') as f:
                pickle.dump(inverted_index, f)
        else:
            print("No cache file specified. Skipping cache saving.")
        
        return inverted_index

    def exact_match(self, query):
        for key, value in self.data_dict.items():
            if query.lower() in value.lower():
                return key
        return None

    def regex_match(self, query):
        pattern = re.compile(query, re.IGNORECASE)
        for key, value in self.data_dict.items():
            if pattern.search(value):
                return key
        return None

    def rapidfuzz_match(self, query, threshold=80):
        best_match = max(self.data_dict.items(), key=lambda x: rfuzz.partial_ratio(query, x[1]))
        return best_match[0] if rfuzz.partial_ratio(query, best_match[1]) >= threshold else None

    def inverted_index_match(self, query):
        query_words = jieba.cut(query)
        candidates = []
        for word in query_words:
            candidates.extend(self.inverted_index.get(word, []))
        
        if not candidates:
            return None

        best_match = max(candidates, key=lambda x: rfuzz.partial_ratio(query, x[1]))
        return best_match[0]

    def __getitem__(self, query):
        # 尝试各种匹配方法
        result = self.exact_match(query)
        if result:
            return result
        
        result = self.regex_match(query)
        if result:
            return result
        
        result = self.rapidfuzz_match(query)
        if result:
            return result
        
        result = self.inverted_index_match(query)
        if result:
            return result
        
        return None  # 如果所有方法都失败，返回 None