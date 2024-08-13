from .index_code import index_code
from core.utils.string_matcher import StringMatcher

index_finder = StringMatcher(index_code,"./json/index_cache.pickle")