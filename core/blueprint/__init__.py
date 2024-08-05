"""
# 如何添加新的模块
## 新建四个文件
- 继承自 StepInfoGenerator  的类
- 继承自 StepCodeGenerator 的类
- 继承自 StepExecutor 的类
- 继承自 BaseStepModel 的类

### StepInfoGenerator
- 填写 step_description，描述这个步骤的作用，如果需要额外的数据来运作，要写明额外的数据是什么，什么取值，怎么取值
- 返回 StepCodeGenerator StepExecutor BaseStepModel
- 实现 gen_step_info 方法，这个方法会接受一个 dict，这个 dict 是用户填写的信息，返回一个 BaseStepModel 的实例 用这个dict的值去填充BaseStepModel
- 实现 validate_step_info 方法，这个方法会接受一个 dict，这个 dict 就是llm生成的信息，这个方法判断llm有没有生成错误，返回一个 tuple，第一个值是错误信息，第二个值是是否合法
- fix_step_info 暂时没有使用，不用管

### StepCodeGenerator
- 实现 gen_step_code 方法，就是如何根据BaseStepModel 的信息来生成代码，主要要教会llm使用以前的变量，不然生成的代码会出错

### StepExecutor
- 如何执行代码，如果没有特殊需求，可以直接继承自基类，也可以直接使用一个现成的基类，因为执行代码的逻辑基本很相似，很少需要重载的

### BaseStepModel
- 添加新的字段

## 修改 CurrentGeneratorCollection
- 在current_generator_collection.py中修改 CurrentGeneratorCollection 添加StepInfoGenerator

## 修改 base_step_model_collection.py BaseStepModelCollection
- 在base_step_model_collection.py中修改 BaseStepModelCollection
- 修改 _get_step_class 方法，添加新的类。这个方法是用来反序列化的，如果不填写，反序列化就肯定不正确

"""