from dataclasses import asdict, dataclass ,field
import json
import re
from typing import List, Literal, Dict
from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
import random
import string

@dataclass
class RePlayModel:
    _parameters: Dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _new_parameters: List[str] = field(default_factory=list, init=False, repr=False)
    _template: str = field(default="")
    _var_name_map: str = field(default="")
    _execution_code: str = field(default="")
    _last_llm_call: str = field(default="")

    @property
    def last_llm_call(self) -> str:
        return self._last_llm_call
    
    @last_llm_call.setter
    def last_llm_call(self, value: str):
        self._last_llm_call = value

    @property
    def execution_code(self) -> str:
        return self._execution_code
    
    @execution_code.setter
    def execution_code(self, value: str):
        self._execution_code = value
    
    @property
    def var_name_map(self) -> str:
        return self._var_name_map
    
    @var_name_map.setter
    def var_name_map(self, value: str):
        self._var_name_map = value

    @property
    def new_parameters(self) -> List[str]:
        return self._new_parameters.copy()
    
    @new_parameters.setter
    def new_parameters(self, value: List[str]):
        self._new_parameters = value.copy() if value is not None else []

    @property
    def parameters(self) -> Dict[str, str]:
        return self._parameters.copy()

    @property
    def template(self) -> str:
        return self._template
    
    @parameters.setter
    def parameters(self, value: Dict[str, str]):
        self._parameters = value.copy() if value is not None else {}
    
    def add_parameter(self, name: str, value: str):
        if self._parameters is None:
            self._parameters = []
        self._parameters[name] = value
    
    def add_new_parameter(self, name: str):
        if self._new_parameters is None:
            self._new_parameters=[]
        self._new_parameters.append(name)

    @template.setter
    def template(self, value: str):
        self._template = value
    
    def get_prompt(self,new_dict:Dict[str,str]=None,error:str=None,code:str=None):
        if error and code:
            prompt=f"""
            上次的代码：
            {code}

            发生了下面的错误：
            {error}

            请帮我修复"""
            return prompt
        line1 =  self._template.format(**self._parameters)
        if new_dict is None:
            return line1
        for key,value in new_dict.items():
            line1 = line1.replace(f"${key}$",f"{{{key}}}")
        line2 = line1.format(**new_dict)
        return line2
    
    def get_new_dict(self,namespaces:Dict[str,any]):
        new_dict = {}
        for value in self._new_parameters:
            if value in namespaces:
                new_dict[value] = namespaces[value]
        return new_dict

    def parse_to_dict(self,input_str: str) -> dict:
        """将特定格式的字符串解析为字典。

        Args:
            input_str: 要解析的字符串，格式如：'{key1}=>{value1},{key2}=>{value2}'。

        Returns:
            解析后的字典。
        """
        # 使用正则表达式匹配键值对
        pattern = r'(\{[^,{}]*\})=>(\{[^,{}]*\})'
        matches = re.findall(pattern, input_str)

        result_dict = {}
        for key, value in matches:
            # 去掉大括号
            key = key.strip('{}')
            value = value.strip('{}')
            result_dict[key] = value

        return result_dict

    def trans_var_name(self,name_map:dict,namespace:Dict[str,any]):
        for key,value in name_map.items():
            if key in namespace:
                namespace[value] = namespace[key]
        return namespace
    @staticmethod
    def deserialize_replay_model(dict_store: dict) -> "RePlayModel":
        """Deserializes a JSON string into a RePlayModel object."""

        data = dict_store  # Load the JSON into a dictionary

        model = RePlayModel()        # Create a new RePlayModel

        # Set attributes directly (if they match the dictionary keys)
        model.template = data.get("_template", "") 
        model.last_llm_call = data.get("_last_llm_call", "")
        model.execution_code = data.get("_execution_code", "")
        model.var_name_map = data.get("_var_name_map", "")

        # Handle list attributes 
        model.new_parameters = data.get("_new_parameters", [])

        # Handle the _parameters dictionary (or use your parse_to_dict method)
        model.parameters = data.get("_parameters", {}) 
        # Alternatively:
        # model.parameters = model.parse_to_dict(data.get("_parameters", ""))

        return model


@dataclass
class StepModel:
    name: str
    result_type: Literal["text", "code", "json"]
    _results: Dict[str, str] = field(default_factory=dict, init=False, repr=False)
    success: bool = field(default=True)
    python_code_file: str = field(default=None)
    replay:RePlayModel = field(default=None)

    def __post_init__(self):
        if hasattr(self, '_results') and isinstance(self._results, dict):
            # 如果 _results 已经是字典，就不需要再做任何事
            pass
        elif hasattr(self, 'results') and isinstance(self.results, dict):
            # 如果存在 'results' 字段，将其复制到 _results
            self._results = self.results.copy()
        else:
            # 如果既没有 _results 也没有 results，初始化为空字典
            self._results = {}

    @property
    def results(self) -> Dict[str, str]:
        return self._results.copy()

    @results.setter
    def results(self, value: Dict[str, str]):
        self._results = value.copy() if value is not None else {}
    
    def add_replay(self):
        replay = RePlayModel()
        self.replay = replay
        return replay

    def add_result(self, name: str, result: str):
        self._results[name] = result

    def gen_python_code_file_name(self):
        key =  list(self.results.keys())[0]
        digits = self.gen_four_random_digit()
        self.python_code_file = f"./step_code/code_{self.name}_{key}_{digits}.py"

    def gen_four_random_digit(self,num=4):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=num))

    def save_python_code(self):
        if self.result_type != "code":
            return
        if self.python_code_file is None:
            self.gen_python_code_file_name()
        with open(self.python_code_file, 'w') as f:
            value =  list(self.results.values())[0]
            f.write(value)
        print(f"Saved python code to {self.python_code_file}")

    def load_python_code(self):
        with open(self.python_code_file, 'r') as f:
            value =  f.read()
            key = list(self.results.keys())[0]
            self.results[key] = value


@dataclass
class QueryModel:
    query: str
    steps: List["StepModel"] =field(default_factory=list)
    failed: bool= field(default=True)
    is_code_stored: bool = field(default=False)

    def _add_step(self, step: "StepModel"):
        self.steps.append(step)

    def add_step(self,name:str,result_type:str="text",success:bool=True)->StepModel:
        step = StepModel(name=name,result_type=result_type,success=success)
        self.steps.append(step)
        return step

    def save_steps_python_code(self):
        for step in self.steps:
            step.save_python_code()


class PlaybackModel:
    _instance =None
    def __init__(self):
        self.queries = []

    @staticmethod
    def get_instance():
        if PlaybackModel._instance is None:
            PlaybackModel._instance = PlaybackModel()
            instance = PlaybackModel._instance
            instance.load_from_json()
        return PlaybackModel._instance

    def add_query(self, query: QueryModel):
        self.queries.append(query)

    def add_query(self,query:str)->QueryModel:
        query_exists = [query for query in self.queries if query.query == query]
        if len(query_exists)>0:
            return query_exists[0]
        q = QueryModel(query=query,steps=[],failed=True,is_code_stored=False)
        self.queries.append(q)
        return q

    def get_queries(self):
        return self.queries

    
    def load_from_json_(self, json_data: List[Dict]) -> List[QueryModel]:
        try:
            queries = []
            for query_data in json_data:
                steps = [StepModel(**{k: v for k, v in step_data.items() if k != '_results'}) for step_data in query_data.get('steps', [])]
                for step, step_data in zip(steps, query_data.get('steps', [])):
                    if '_results' in step_data:
                        step._results = step_data['_results']
                query = QueryModel(query=query_data['query'], steps=steps, failed=query_data['failed'])
                queries.append(query)
            
            print(f"Successfully loaded {len(queries)} queries from JSON data")
            return queries
        except KeyError as e:
            print(f"Error: Missing key in JSON structure: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return []

    
    def save_to_json_(self, queries: List[QueryModel]) -> List[Dict]:
        try:
            json_data = [asdict(query) for query in queries]
            print(f"Successfully converted {len(queries)} QueryModel objects to List[Dict]")
            return json_data
        except Exception as e:
            print(f"An error occurred while converting to List[Dict]: {e}")
            return []

    def load_from_json(self):
        singleton = AKShareDataSingleton()
        json_data = singleton.get_completed_querys()
        self.completed_querys = self.load_from_json_(json_data)
        print(f"Loaded {len(self.completed_querys)} queries from AKShareDataSingleton")

    def save_to_json(self):
        self.queries = [query for query in self.queries if not query.failed and len(query.steps) > 0]
        for query in self.queries:
            if not query.is_code_stored:
                query.save_steps_python_code()
                query.is_code_stored = True
        json_data = self.save_to_json_(self.queries)
        singleton = AKShareDataSingleton()
        singleton.completed_querys.extend(json_data)
        singleton.save_completed_querys()
        print(f"Saved {len(json_data)} queries to AKShareDataSingleton and file")