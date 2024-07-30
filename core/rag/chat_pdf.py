import argparse
import hashlib
import os
import re
from threading import Thread
from typing import Union, List

import jieba
from ..utils.log import logger
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from core.embeddings._embedding import Embedding
from core.embeddings.embedding_factory import EmbeddingFactory
from core.embeddings._ranker import Ranker
from core.embeddings.ranker_factory import RankerFactory
from core.llms._llm_api_client import LLMApiClient
from core.llms.llm_factory import LLMFactory

jieba.setLogLevel("ERROR")

PROMPT_TEMPLATE = """基于以下已知信息，简洁和专业的来回答用户的问题。
如果无法从中得到答案，请说 "根据已知信息无法回答该问题" 或 "没有提供足够的相关信息"，不允许在答案中添加编造成分。

已知内容:
{context_str}

问题:
{query_str}
"""

class SentenceSplitter:
    def __init__(self, chunk_size: int = 250, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        if self._is_has_chinese(text):
            return self._split_chinese_text(text)
        else:
            return self._split_english_text(text)

    def _split_chinese_text(self, text: str) -> List[str]:
        sentence_endings = {'\n', '。', '！', '？', '；', '…'}  # 句末标点符号
        chunks, current_chunk = [], ''
        for word in jieba.cut(text):
            if len(current_chunk) + len(word) > self.chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = word
            else:
                current_chunk += word
            if word[-1] in sentence_endings and len(current_chunk) > self.chunk_size - self.chunk_overlap:
                chunks.append(current_chunk.strip())
                current_chunk = ''
        if current_chunk:
            chunks.append(current_chunk.strip())
        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._handle_overlap(chunks)
        return chunks

    def _split_english_text(self, text: str) -> List[str]:
        # 使用正则表达式按句子分割英文文本
        sentences = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
        chunks, current_chunk = [], ''
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size or not current_chunk:
                current_chunk += (' ' if current_chunk else '') + sentence
            else:
                chunks.append(current_chunk)
                current_chunk = sentence
        if current_chunk:  # Add the last chunk
            chunks.append(current_chunk)

        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._handle_overlap(chunks)

        return chunks

    def _is_has_chinese(self, text: str) -> bool:
        # check if contains chinese characters
        if any("\u4e00" <= ch <= "\u9fff" for ch in text):
            return True
        else:
            return False

    def _handle_overlap(self, chunks: List[str]) -> List[str]:
        # 处理块间重叠
        overlapped_chunks = []
        for i in range(len(chunks) - 1):
            chunk = chunks[i] + ' ' + chunks[i + 1][:self.chunk_overlap]
            overlapped_chunks.append(chunk.strip())
        overlapped_chunks.append(chunks[-1])
        return overlapped_chunks

class ChatPDF:
    def __init__(
            self,
            collection_name: str = "chatpdf_collection",
            corpus_files: Union[str, List[str]] = None,
            chunk_size: int = 250,
            chunk_overlap: int = 0,
            enable_history: bool = False,
            num_expand_context_chunk: int = 2,
            similarity_top_k: int = 50,
            rerank_top_k: int = 5,
    ):
        self.text_splitter = SentenceSplitter(chunk_size, chunk_overlap)
        
        embedding_factory = EmbeddingFactory()
        self.embedding: Embedding = embedding_factory.get_instance()
        
        ranker_factory = RankerFactory()
        self.ranker: Ranker = ranker_factory.get_instance()
        
        llm_factory = LLMFactory()
        self.llm_client: LLMApiClient = llm_factory.get_instance()
        
        self.qdrant_client = QdrantClient(path="./database/")
        self.collection_name = collection_name
        
        self.history = []
        self.corpus_files = corpus_files
        if corpus_files:
            self.add_corpus(corpus_files)
        
        self.enable_history = enable_history
        self.similarity_top_k = similarity_top_k
        self.num_expand_context_chunk = num_expand_context_chunk
        self.rerank_top_k = rerank_top_k

    def __str__(self):
        return f"Embedding model: {self.embedding}, Ranker model: {self.ranker}, LLM model: {self.llm_client}"

    def add_corpus(self, files: Union[str, List[str]]):
        from qdrant_client.http import models
        from uuid import uuid4
        if isinstance(files, str):
            files = [files]
        
        all_chunks = []
        for doc_file in files:
            if doc_file.endswith('.pdf'):
                corpus = self.extract_text_from_pdf(doc_file)
            elif doc_file.endswith('.docx'):
                corpus = self.extract_text_from_docx(doc_file)
            elif doc_file.endswith('.md'):
                corpus = self.extract_text_from_markdown(doc_file)
            else:
                corpus = self.extract_text_from_txt(doc_file)
            full_text = '\n'.join(corpus)
            chunks = self.text_splitter.split_text(full_text)
            all_chunks.extend(chunks)
        
        # Process embeddings in batches of 10
        embeddings = []
        for i in range(0, len(all_chunks), 10):
            batch = all_chunks[i:i+10]
            batch_embeddings = self.embedding.convert_to_embedding(batch)
            embeddings.extend(batch_embeddings)
        
        self.qdrant_client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=len(embeddings[0]), distance=Distance.COSINE),
        )
        
        # Create Record objects for Qdrant using UUID
        records = [
            models.Record(
                id=str(uuid4()),  # Generate a new UUID for each record
                vector=emb,
                payload={"text": chunk}
            )
            for emb, chunk in zip(embeddings, all_chunks)
        ]
        
        # Upload records to Qdrant
        self.qdrant_client.upload_records(
            collection_name=self.collection_name,
            records=records
        )
        
        self.corpus_files = files
        logger.debug(f"files: {files}, corpus size: {len(all_chunks)}, top3: {all_chunks[:3]}")

    @staticmethod
    def get_file_hash(fpaths):
        hasher = hashlib.md5()
        target_file_data = bytes()
        if isinstance(fpaths, str):
            fpaths = [fpaths]
        for fpath in fpaths:
            with open(fpath, 'rb') as file:
                chunk = file.read(1024 * 1024)  # read only first 1MB
                hasher.update(chunk)
                target_file_data += chunk

        hash_name = hasher.hexdigest()[:32]
        return hash_name

    @staticmethod
    def extract_text_from_pdf(file_path: str):
        import PyPDF2
        contents = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text().strip()
                raw_text = [text.strip() for text in page_text.splitlines() if text.strip()]
                new_text = ''
                for text in raw_text:
                    new_text += text
                    if text[-1] in ['.', '!', '?', '。', '！', '？', '…', ';', '；', ':', '：', '"', '\'', '）', '】', '》', '」',
                                    '』', '〕', '〉', '》', '〗', '〞', '〟', '»', '"', "'", ')', ']', '}']:
                        contents.append(new_text)
                        new_text = ''
                if new_text:
                    contents.append(new_text)
        return contents

    @staticmethod
    def extract_text_from_txt(file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            contents = [text.strip() for text in f.readlines() if text.strip()]
        return contents

    @staticmethod
    def extract_text_from_docx(file_path: str):
        import docx
        document = docx.Document(file_path)
        contents = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return contents

    @staticmethod
    def extract_text_from_markdown(file_path: str):
        import markdown
        from bs4 import BeautifulSoup
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        html = markdown.markdown(markdown_text)
        soup = BeautifulSoup(html, 'html.parser')
        contents = [text.strip() for text in soup.get_text().splitlines() if text.strip()]
        return contents

    @staticmethod
    def _add_source_numbers(lst):
        return [f'[{idx + 1}]\t "{item}"' for idx, item in enumerate(lst)]

    def get_reference_results(self, query: str):
        query_vector = self.embedding.convert_to_embedding([query])[0]
        
        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=self.similarity_top_k
        )
        
        reference_results = [hit.payload['text'] for hit in search_result]
        
        if reference_results and self.ranker:
            rerank_scores = self.ranker.rank(query, reference_results)
            reference_results = [reference for reference, score in sorted(
                zip(reference_results, rerank_scores), key=lambda x: x[1], reverse=True)][:self.rerank_top_k]
        
        if self.num_expand_context_chunk > 0:
            expanded_results = []
            for hit in search_result[:self.rerank_top_k]:
                # Get all documents
                all_docs = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    limit=1000,  # Adjust this value based on your collection size
                    with_payload=True,
                    with_vectors=False
                )[0]
                
                # Find the index of the current hit
                current_index = next(i for i, doc in enumerate(all_docs) if doc.id == hit.id)
                
                # Get the expanded context
                start_index = max(0, current_index - self.num_expand_context_chunk)
                end_index = min(len(all_docs), current_index + self.num_expand_context_chunk + 1)
                expanded_context = all_docs[start_index:end_index]
                
                expanded_text = ' '.join([doc.payload['text'] for doc in expanded_context])
                expanded_results.append(expanded_text)
            
            reference_results = expanded_results
        
        return reference_results

    def predict_stream(
            self,
            query: str,
            max_length: int = 512,
            context_len: int = 2048,
            temperature: float = 0.7,
    ):
        if not self.enable_history:
            self.history = []
        
        reference_results = self.get_reference_results(query)
        
        if not reference_results:
            yield '没有提供足够的相关信息', reference_results
        
        reference_results = self._add_source_numbers(reference_results)
        context_str = '\n'.join(reference_results)[:(context_len - len(PROMPT_TEMPLATE))]
        prompt = PROMPT_TEMPLATE.format(context_str=context_str, query_str=query)
        logger.debug(f"prompt: {prompt}")
        
        self.history.append([prompt, ''])
        response = ""
        
        for new_text in self.llm_client.text_chat(prompt):
            response += new_text
            yield response

    def predict(
            self,
            query: str,
            max_length: int = 512,
            context_len: int = 2048,
            temperature: float = 0.7,
    ):
        if not self.enable_history:
            self.history = []
        
        reference_results = self.get_reference_results(query)
        
        if not reference_results:
            return '没有提供足够的相关信息', reference_results
        
        reference_results = self._add_source_numbers(reference_results)
        context_str = '\n'.join(reference_results)[:(context_len - len(PROMPT_TEMPLATE))]
        prompt = PROMPT_TEMPLATE.format(context_str=context_str, query_str=query)
        logger.debug(f"prompt: {prompt}")
        
        self.history.append([prompt, ''])
        response = self.llm_client.text_chat(prompt)
        
        self.history[-1][1] = response
        return response, reference_results
