from abc import ABC, abstractmethod
import hashlib
import hmac
import time
from typing import List, Dict, Any
import json
import requests

from ._embedding import Embedding
from ..utils.config_setting import Config


class HunyuanEmbedding(Embedding):
    def __init__(self):
        config = Config()
        secret_id  = config.get("hunyuan_SecretId")
        secret_key = config.get("hunyuan_SecretKey")
        self.secret_id  = secret_id 
        self.secret_key = secret_key
        self.url = "https://hunyuan.tencentcloudapi.com"
        self.headers = {
            "Content-Type": "application/json",
            "X-TC-Action": "GetEmbedding",
            "X-TC-Version": "2023-09-01",
        }
        self.endpoint = "hunyuan.tencentcloudapi.com"
        self.service = "hunyuan"
        self.region = "" 
        self.action = "GetEmbedding"
        self.version = "2023-09-01"

    def _get_signature(self, params: Dict[str, str], http_method: str) -> str:
        canonical_uri = "/"
        canonical_querystring = ""
        ct = "application/json; charset=utf-8"
        payload = json.dumps(params)
        
        canonical_headers = "content-type:%s\nhost:%s\n" % (ct, self.endpoint)
        signed_headers = "content-type;host"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (http_method + "\n" +
                             canonical_uri + "\n" +
                             canonical_querystring + "\n" +
                             canonical_headers + "\n" +
                             signed_headers + "\n" +
                             hashed_request_payload)

        algorithm = "TC3-HMAC-SHA256"
        timestamp = int(time.time())
        date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))
        credential_scope = date + "/" + self.service + "/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = (algorithm + "\n" +
                          str(timestamp) + "\n" +
                          credential_scope + "\n" +
                          hashed_canonical_request)

        def sign(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = sign(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = sign(secret_date, self.service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization = (algorithm + " " +
                         "Credential=" + self.secret_id + "/" + credential_scope + ", " +
                         "SignedHeaders=" + signed_headers + ", " +
                         "Signature=" + signature)

        return authorization, timestamp

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        embeddings = []
        for input_string in input_strings:
            params = {
                "Input": input_string
            }

            authorization, timestamp = self._get_signature(params, "POST")

            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Host": self.endpoint,
                "X-TC-Action": self.action,
                "X-TC-Timestamp": str(timestamp),
                "X-TC-Version": self.version,
                "X-TC-Region": self.region,
                "Authorization": authorization,
            }

            response = requests.post(
                f"https://{self.endpoint}",
                headers=headers,
                data=json.dumps(params)
            )

            if response.status_code == 200:
                result = response.json()
                if "Response" in result and "Data" in result["Response"]:
                    embedding = result["Response"]["Data"][0]["Embedding"]
                    embeddings.append(embedding)
                else:
                    raise ValueError(f"Unexpected response format: {result}")
            else:
                raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

        return embeddings

    def get_usage(self, response: Dict[str, Any]) -> Dict[str, int]:
        if "Response" in response and "Usage" in response["Response"]:
            usage = response["Response"]["Usage"]
            return {
                "prompt_tokens": usage["PromptTokens"],
                "total_tokens": usage["TotalTokens"]
            }
        else:
            raise ValueError(f"Unexpected response format: {response}")
        
    @property
    def vector_size(self) -> int:
        return 1024