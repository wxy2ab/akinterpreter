from datetime import datetime
import logging
import traceback
import akshare
import inspect
import json
import time
from typing import List, Dict, Any, Tuple
import pandas as pd
from ..llms._llm_api_client import LLMApiClient
from ..llms.llm_factory import LLMFactory
import os
import re

class AkShareDocEnhancer:
    def __init__(self):
        factory = LLMFactory()
        self.llm_client = factory.get_instance()
        self.supplement_dict = self.load_supplement_dict()

    def load_supplement_dict(self) -> Dict[str, Dict[str, str]]:
        """
        Load existing supplement dictionary from JSON file if it exists.
        """
        if os.path.exists("akshare_supplement_dict.json"):
            with open("akshare_supplement_dict.json", "r",encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_supplement_dict(self) -> None:
        """
        Save the current supplement dictionary to JSON file.
        """
        with open("akshare_supplement_dict.json", "w",encoding="utf-8") as f:
            json.dump(self.supplement_dict, f, indent=2)

    def get_all_functions(self) -> List[str]:
        """
        Get all function names from the akshare module.
        """
        return [name for name, obj in inspect.getmembers(akshare) if inspect.isfunction(obj)]

    def get_function_doc(self, func_name: str) -> str:
        """
        Get the docstring of the given function.
        """
        func = getattr(akshare, func_name)
        return inspect.getdoc(func) or ""

    def call_claude_api(self, prompt: str) -> str:
        """
        Call Claude API to generate code using the text_chat method.
        """
        response = self.llm_client.text_chat(prompt)
        return response

    def _extract_python_code1(self, response: str) -> str:
        """
        Extract Python code from the response
        
        :param response: Claude API's response
        :return: Extracted Python code
        """
        # First try to find Markdown code block
        code_block_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # If no Markdown code block is found, try to extract all possible Python code
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        for line in lines:
            if line.strip().startswith('import') or line.strip().startswith('from'):
                in_code_block = True
            if in_code_block:
                code_lines.append(line)
            if line.strip().startswith('print(') and in_code_block:
                break
        
        return '\n'.join(code_lines).strip() if code_lines else ''

    def _extract_python_code(self, response: str) -> Tuple[str, str]:
        """
        Extract Python code from the response
        
        :param response: Claude API's response
        :return: A tuple of (extracted code, extraction method)
        """
        logging.debug(f"Raw response from Claude API:\n{response}")

        # First try to find Markdown code block
        code_block_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_block_match:
            extracted_code = code_block_match.group(1).strip()
            logging.info("Code extracted using Markdown code block")
            return extracted_code, "markdown"
        
        # If no Markdown code block is found, try to extract all possible Python code
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('import') or stripped_line.startswith('def ') or stripped_line.startswith('result ='):
                in_code_block = True
            if in_code_block:
                code_lines.append(line)
            if stripped_line.startswith('print(') and in_code_block:
                code_lines.append(line)
                break
        
        extracted_code = '\n'.join(code_lines).strip()
        if extracted_code:
            logging.info("Code extracted line by line")
            return extracted_code, "line_by_line"
        
        # If still no code is found, try to find any Python-like content
        python_like_content = re.findall(r'(import.*?|def.*?|result\s*=.*?|print\(.*?\))', response, re.DOTALL)
        if python_like_content:
            extracted_code = '\n'.join(python_like_content)
            logging.warning("Extracted Python-like content, but it may not be complete code")
            return extracted_code, "partial_extraction"

        logging.error("Failed to extract any valid Python code")
        return response.strip(), "full_response"

    def describe_return_value(self, value: Any, include_types: bool = False, include_samples: bool = True) -> str:
        """
        Generate a description of the return value's structure.
        
        :param value: The return value to describe
        :param include_types: Whether to include column types for DataFrames
        :param include_samples: Whether to include sample data for potentially ambiguous fields
        :return: A string description of the value
        """
        if isinstance(value, pd.DataFrame):
            base_description = f"DataFrame with shape {value.shape}, columns: {list(value.columns)}"
            
            if include_types:
                type_info = {col: str(value[col].dtype) for col in value.columns}
                base_description += f", types: {type_info}"
            
            if include_samples:
                sample_data = {}
                for col in value.columns:
                    if 'date' in col.lower() or value[col].dtype == 'datetime64[ns]' or 'time' in col.lower():
                        sample_data[col] = str(value[col].iloc[0])
                    elif value[col].dtype == 'object':
                        sample_data[col] = str(value[col].iloc[0])
                if sample_data:
                    base_description += f", sample data: {sample_data}"
            
            return base_description
        elif isinstance(value, (list, tuple)):
            return f"{type(value).__name__} of length {len(value)}, sample: {value[:3]}"
        elif isinstance(value, dict):
            return f"Dictionary with keys: {list(value.keys())}"
        else:
            return f"{type(value).__name__}: {str(value)[:100]}"

    def process_function(self, func_name: str, max_retries: int = 3, include_types: bool = False, include_samples: bool = True) -> None:
        """
        Process a single function, generate code, execute it, and update the supplement dictionary.
        """
        if func_name in self.supplement_dict:
            logging.info(f"Skipping {func_name} as it has already been processed.")
            return

        doc = self.get_function_doc(func_name)
        error_message = ""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.llm_client.clear_chat()  # Clear chat history before starting a new function

        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    prompt = f"""The current date and time is {current_time}. Generate Python code to call akshare.{func_name} based on this docstring: {doc}. 
                    The code should include the following:
                    1. Import akshare as ak (this is already done for you)
                    2. Call the function with appropriate parameters, considering the current date and time
                    3. Store the result in a variable named 'result'
                    4. Print the result
                    Enclose the entire code in a Python markdown code block (```python). If the function requires date parameters, use appropriate dates based on the current date provided. 
                    Do not include any explanations or comments outside the code block."""
                else:
                    prompt = f"""The previous attempt to generate code for akshare.{func_name} failed. 
                    Here's the error message:
                    
                    {error_message}
                    
                    Please provide an improved version of the code that addresses this error. 
                    Remember that akshare is already imported as ak, so you don't need to import it again.
                    Make sure to call the function with appropriate parameters (considering the current date and time), 
                    store the result in 'result', and print it. 
                    Enclose the entire code in a Python markdown code block (```python).
                    If the function returned an empty DataFrame, try adjusting the parameters, especially date-related ones.
                    Do not include any explanations or comments outside the code block."""

                response = self.call_claude_api(prompt)
                generated_code, extraction_method = self._extract_python_code(response)
                
                if extraction_method == "full_response":
                    raise ValueError(f"Failed to extract valid Python code. Full response: {response}")
                elif extraction_method == "partial_extraction":
                    logging.warning(f"Only partial code could be extracted for {func_name}. Attempting to execute anyway.")
                
                logging.info(f"Generated code for {func_name}:\n{generated_code}")
                
                result = self.execute_generated_code(generated_code)
                return_description = self.describe_return_value(result, include_types=include_types, include_samples=include_samples)
                
                self.supplement_dict[func_name] = {"return": return_description}
                self.save_supplement_dict()  # Save after each successful processing
                logging.info(f"Successfully processed and saved {func_name} on attempt {attempt + 1}")
                return
            except Exception as e:
                error_message = f"Error on attempt {attempt + 1}: {str(e)}\n{traceback.format_exc()}"
                logging.error(error_message)
        
        logging.error(f"Failed to process {func_name} after {max_retries} attempts")
        with open("failed.txt", "a", encoding='utf-8') as f:
            f.write(f"{func_name}\n")

    def execute_generated_code(self, code: str) -> Any:
        """
        Execute the generated code and return the result.
        """
        try:
            # Create a local namespace for execution
            local_namespace = {"ak": akshare}
            exec(code, globals(), local_namespace)
            
            # The result should be stored in a variable named 'result'
            if 'result' in local_namespace:
                result = local_namespace['result']
                if isinstance(result, pd.DataFrame) and result.empty:
                    raise ValueError("The function returned an empty DataFrame. This might be due to incorrect parameters.")
                return result
            else:
                raise ValueError("No 'result' variable found in the generated code")
        except Exception as e:
            raise RuntimeError(f"Error executing generated code: {str(e)}")

    def process_all_functions(self, include_types: bool = False, include_samples: bool = True):
        """
        Process all functions in akshare and save the results.
        """
        all_functions = self.get_all_functions()

        for func_name in all_functions:
            self.process_function(func_name,max_retries = 5, include_types =include_types,include_samples = include_samples)

        print("Processing complete. Results saved to akshare_supplement_dict.json")

def main():
    enhancer = AkShareDocEnhancer()
    enhancer.process_all_functions()

if __name__ == "__main__":
    main()