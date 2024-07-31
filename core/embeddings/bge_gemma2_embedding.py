from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List
from ._embedding import Embedding
import os
from huggingface_hub import snapshot_download

#模型文件及其巨大，不是机器性能极好，不要尝试
class BGEGemma2Embedding(Embedding):
    def __init__(self):
        from ..utils.get_sentence_device import get_sentence_transformer_device
        from ..utils.config_setting import Config

        device = get_sentence_transformer_device()
        config = Config()
        
        # 设置模型路径
        model_name = "BAAI/bge-multilingual-gemma2"
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        local_model_path = os.path.join(cache_dir, model_name)

        # 检查本地模型文件是否存在，如果不存在则下载
        if not os.path.exists(local_model_path) or not os.listdir(local_model_path):
            print(f"Model not found in {local_model_path}. Downloading...")
            api_key = config.get("hugging_face_api_key")
            if api_key:
                os.environ['HUGGING_FACE_HUB_TOKEN'] = api_key
            
            try:
                local_model_path = snapshot_download(model_name, cache_dir=cache_dir, token=api_key)
                print(f"Model downloaded successfully to {local_model_path}")
            except Exception as e:
                print(f"Error downloading model: {str(e)}")
                raise

        # 加载模型和分词器
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(local_model_path)
            self.model = AutoModel.from_pretrained(
                local_model_path, 
                torch_dtype=torch.float16, 
                device_map="auto"
            )
            self.model.to(device)
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        inputs = self.tokenizer(input_strings, padding=True, truncation=True, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return embeddings.tolist()

    @property
    def vector_size(self) -> int:
        return 768


class BGEGemma2Embedding1(Embedding):
    def __init__(self):
        from ..utils.get_sentence_device import get_sentence_transformer_device
        device = get_sentence_transformer_device()
        from ..utils.config_setting import Config
        api_key = ""
        config = Config()
        if config.has_key("hugging_face_api_key"):
            api_key = config.get("hugging_face_api_key")
        # 设置 API Key
        if api_key:
            import os
            os.environ['HUGGING_FACE_HUB_TOKEN'] = api_key
        self.model = SentenceTransformer("BAAI/bge-multilingual-gemma2", model_kwargs={"torch_dtype": torch.float16},device=device,token=api_key)

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        return self.model.encode(input_strings).tolist()
    
    @property
    def vector_size(self) -> int:
        return 768
    
    