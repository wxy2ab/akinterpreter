from typing import List, Dict, Any, Union, Tuple
from core.llms._llm_api_client import LLMApiClient
import datetime
import pandas as pd

class LLMFactor:
    def __init__(self,client: LLMApiClient):
        self.client: LLMApiClient = client
    
    def get_company_relation(self, stock_target: str, stock_match: str) -> str:
        prompt = f"请填空并返回完整的句子: {stock_target}和{stock_match}最可能是___关系。"
        response = self.client.one_chat(prompt)
        return response.strip()
    
    def get_relation(self, stock_target: str, stock_match: str, is_match_index: bool) -> str:
        if is_match_index:
            prompt = f"请描述{stock_target}与{stock_match}指数之间的关系。"
        else:
            prompt = f"请填空并返回完整的句子: {stock_target}和{stock_match}最可能是___关系。"
        response = self.client.one_chat(prompt)
        return response.strip()
    
    def extract_factors(self, stock_target: str, news: List[Dict[str, Any]], start_date: datetime.date, end_date: datetime.date, k: int = 5) -> List[str]:
        relevant_news = [
            n for n in news 
            if start_date <= datetime.datetime.strptime(n['date'], "%Y-%m-%d").date() <= end_date
        ]
        relevant_news.sort(key=lambda x: x['date'], reverse=True)
        
        combined_news = "\n\n".join([f"日期: {n['date']}\n内容: {n['content']}" for n in relevant_news[:5]])
        prompt = f"请从以下新闻中提取可能影响{stock_target}股价的前{k}个因素：\n\n{combined_news}"
        response = self.client.one_chat(prompt)
        factors = response.strip().split('\n')
        return factors[:k]
    
    def predict_movement(self, stock_target: str, stock_match: str, is_match_index: bool, factors: List[str], relation: str, 
                         target_price_history: List[Dict[str, Any]], match_price_history: List[Dict[str, Any]], 
                         news_summary: str) -> Dict[str, Any]:
        target_price_template = "\n".join([f"在{p['date']}, {stock_target}的股价{'上涨' if p['movement'] else '下跌'}。" for p in target_price_history])
        match_price_template = "\n".join([f"在{p['date']}, {stock_match}的{'指数' if is_match_index else '股价'}{'上涨' if p['movement'] else '下跌'}。" for p in match_price_history])
        
        prompt = f"""
        根据以下信息，请判断{stock_target}的股价是上涨还是下跌，填写在空白处并给出理由。
        这些是最近可能影响该股票价格的主要因素: {', '.join(factors)}。
        {stock_target}和{stock_match}{'指数' if is_match_index else ''}的关系: {relation}。
        最近的相关新闻摘要: {news_summary}
        {stock_target}的最近股价变动:
        {target_price_template}
        {stock_match}的最近{'指数' if is_match_index else '股价'}变动:
        {match_price_template}
        在下一个交易日，{stock_target}的股价将___。
        """
        
        response = self.client.one_chat(prompt)
        
        prediction_lines = response.strip().split('\n')
        prediction = '上涨' if '上涨' in prediction_lines[0] else '下跌'
        reasoning = '\n'.join(prediction_lines[1:])
        
        return {
            "prediction": prediction,
            "reasoning": reasoning
        }
    
    def analyze(self, stock_target: str, stock_match: str, is_match_index: bool, news: List[Dict[str, Any]], 
                target_price_data: Union[List[Dict[str, Any]], pd.DataFrame],
                match_price_data: Union[List[Dict[str, Any]], pd.DataFrame],
                target_date: datetime.date) -> Dict[str, Any]:
        target_price_history, start_date = self.calculate_price_history(target_price_data, target_date)
        match_price_history, _ = self.calculate_price_history(match_price_data, target_date)
        relation = self.get_relation(stock_target, stock_match, is_match_index)
        factors = self.extract_factors(stock_target, news, start_date, target_date)
        
        relevant_news = [
            n for n in news 
            if start_date <= datetime.datetime.strptime(n['date'], "%Y-%m-%d").date() <= target_date
        ]
        news_summary = self.summarize_news(relevant_news)
        
        prediction = self.predict_movement(stock_target, stock_match, is_match_index, factors, relation, 
                                           target_price_history, match_price_history, news_summary)
        
        return {
            "relation": relation,
            "factors": factors,
            "prediction": prediction["prediction"],
            "reasoning": prediction["reasoning"]
        }
    
    def calculate_price_history(self, price_data: Union[List[Dict[str, Any]], pd.DataFrame], target_date: datetime.date, window_size: int = 5) -> Tuple[List[Dict[str, Any]], datetime.date]:
        if isinstance(price_data, list) and isinstance(price_data[0], dict):
            df = pd.DataFrame(price_data)
            df['date'] = pd.to_datetime(df['date'])
        elif isinstance(price_data, pd.DataFrame):
            df = price_data.copy()
            df['date'] = pd.to_datetime(df['date'])
        else:
            raise ValueError("Unsupported price_data format.")

        df = df.sort_values('date')
        
        # 获取目标日期之前的数据
        df = df[df['date'] <= target_date]
        
        if len(df) < window_size + 1:
            raise ValueError(f"Not enough data points before the target date. Need at least {window_size + 1} data points.")

        price_history = []
        for i in range(-window_size - 1, -1):
            current_price = df.iloc[i]['close']
            previous_price = df.iloc[i-1]['close']
            movement = current_price > previous_price
            price_history.append({
                "date": df.iloc[i]['date'].strftime("%Y-%m-%d"),
                "movement": movement
            })
        
        start_date = df.iloc[-window_size - 1]['date'].date()
        
        return price_history, start_date

    def summarize_news(self, news: List[Dict[str, Any]], max_length: int = 500) -> str:
        combined_news = "\n\n".join([f"日期: {n['date']}\n内容: {n['content']}" for n in news])
        prompt = f"请对以下新闻进行总结，总结长度不超过{max_length}个字：\n\n{combined_news}"
        summary = self.client.one_chat(prompt)
        return summary.strip()