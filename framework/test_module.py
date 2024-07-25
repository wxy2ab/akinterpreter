import time
import logging
import os
import importlib
import traceback


class TestModule:
    @staticmethod
    def test_one(module, continue_on_error=False, log_file=None):
        functions = [func for func in dir(module) if callable(getattr(module, func)) and func.startswith("test_")]
        num_functions = len(functions)
        
        logging.info(f"Starting test for module: {module.__name__}")
        logging.info(f"Number of functions to test: {num_functions}")
        
        for func_name in functions:
            func = getattr(module, func_name)
            
            start_time = time.time()
            logging.info(f"Starting test: {func_name}")
            
            try:
                func()
                end_time = time.time()
                logging.info(f"Test finished: {func_name}, Time elapsed: {end_time - start_time:.2f} seconds")
            except Exception as e:
                end_time = time.time()
                logging.error(f"Test failed: {func_name}, Error: {str(e)}, Time elapsed: {end_time - start_time:.2f} seconds")
                logging.error(traceback.format_exc())
                if not continue_on_error:
                    raise
        
        logging.info(f"Finished testing module: {module.__name__}")
    @staticmethod
    def test_all(modules, continue_on_error=False, log_file=None):
        if log_file:
            logging.basicConfig(filename=log_file, level=logging.INFO,
                                format='%(asctime)s - %(levelname)s - %(message)s')
        else:
            logging.basicConfig(level=logging.INFO,
                                format='%(asctime)s - %(levelname)s - %(message)s')
        
        start_time = time.time()
        logging.info("=============start test============")
        
        for module in modules:
            module_start_time = time.time()
            logging.info(f"Testing module: {module.__name__}")
            
            try:
                TestModule.test_one(module, continue_on_error, log_file)
                module_end_time = time.time()
                logging.info(f"Test {module.__name__} finished! Time elapsed: {module_end_time - module_start_time:.2f} seconds")
            except Exception as e:
                module_end_time = time.time()
                logging.error(f"Test {module.__name__} failed! Error: {str(e)}, Time elapsed: {module_end_time - module_start_time:.2f} seconds")
                if not continue_on_error:
                    raise
        
        end_time = time.time()
        logging.info("=============end of test============")
        logging.info(f"Total time elapsed: {end_time - start_time:.2f} seconds")
    @staticmethod
    def import_test_libs():
        test_modules = []
        for file in os.listdir("test"):
            if file.startswith("test_") and file.endswith(".py"):
                module_name = file[:-3]
                module = importlib.import_module(f"test.{module_name}")
                test_modules.append(module)
        return test_modules
    @staticmethod
    def run(continue_on_error=None, log_file=None, module_names=None):
        try:
            import test.tester as tester
            # 如果参数未传递,则使用 test.tester 中的默认配置
            if continue_on_error is None:
                continue_on_error = tester.continue_on_error
            if log_file is None:
                log_file = tester.log_file
            if module_names is None:
                module_names = tester.tests
        except ImportError:
            # 如果 test.tester 模块不存在,则设置默认值
            if continue_on_error is None:
                continue_on_error = False
            if log_file is None:
                log_file = "test.log"
            if module_names is None:
                module_names = ["*"]
        
        all_modules = TestModule.import_test_libs()
        if module_names == ["*"] or module_names == ["all"]:
            module_for_tests = all_modules
        else:
            module_for_tests = [module for module in all_modules if module.__name__ in [f"test.{name}" for name in module_names]]
        TestModule.test_all(module_for_tests, continue_on_error, log_file)
    