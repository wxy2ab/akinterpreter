


from typing import ClassVar, Literal
from ._base_step_model import BaseStepModel


class DataExportStepModel(BaseStepModel):
    step_type: ClassVar[Literal['data_export']] =  'data_export'
    filetype: Literal['csv', 'json', 'parquet','xml','xlsx','markdown' ,'html','pdf','docx'] = 'csv'