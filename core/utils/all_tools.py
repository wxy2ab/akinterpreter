import ast
import contextlib
import io
import requests
"""
这个文件的内容是测试用的
很不完善
不要用于生产环境
"""


class AllTools:

    @staticmethod
    def get_current_weather(location):
        # 使用高德开放平台的天气API接口
        from .config_setting import Config
        config = Config()
        api_key = config.get("GAODE_MAP_API_KEY")  # 替换为你自己的API Key
        base_url = "https://restapi.amap.com/v3/weather/weatherInfo"

        # 发送请求获取天气数据
        params = {
            "key": api_key,
            "city": location,
            "output": "JSON",
            "extensions": "base"
        }
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()

            if data["status"] == "1" and int(data["count"]) > 0:
                weather_info = data["lives"][0]

                # 提取所需的天气信息
                province = weather_info["province"]
                city = weather_info["city"]
                weather_description = weather_info["weather"]
                temperature = weather_info["temperature"]
                humidity = weather_info["humidity"]
                wind_direction = weather_info["winddirection"]
                wind_power = weather_info["windpower"]

                # 返回天气信息
                weather_info = f"{province} {city}当前天气:\n" \
                            f"天气描述: {weather_description}\n" \
                            f"温度: {temperature}°C\n" \
                            f"湿度: {humidity}%\n" \
                            f"风向: {wind_direction}\n" \
                            f"风力: {wind_power} 级"

                return weather_info
            else:
                return f"未找到{location}的天气信息。"
        else:
            return f"获取{location}天气信息失败。"

    @staticmethod
    def get_current_weather_en(location):
        # 使用天气API接口
        from .config_setting import Config
        config = Config()
        api_key = config.get("OPEN_WEATHER_API_KEY")  # 替换为你自己的API Key
        base_url = "http://api.openweathermap.org/data/2.5/weather"

        # 发送请求获取天气数据
        params = {
            "q": location,
            "appid": api_key,
            "units": "metric",  # 单位为摄氏度
            "lang": "zh_cn"  # 天气信息使用中文描述
        }
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()

            # 提取所需的天气信息
            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            # 返回天气信息
            weather_info = f"{location}当前天气:\n" \
                        f"天气描述: {weather_description}\n" \
                        f"温度: {temperature}°C\n" \
                        f"湿度: {humidity}%\n" \
                        f"风速: {wind_speed} m/s"

            return weather_info
        else:
            return f"获取{location}天气信息失败。"

    @staticmethod
    def get_current_time():
        from datetime import datetime
        current_datetime = datetime.now()
        formatted_time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return f"当前时间:{formatted_time}。"

    @staticmethod
    def CodeRunner(code: str) -> str:
        # 删除代码开头和结尾的 ```python 标记
        code = code.strip()
        if code.startswith("```python"):
            code = code[9:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()

        # 重定向标准输出到缓冲区
        stdout_buffer = io.StringIO()
        with contextlib.redirect_stdout(stdout_buffer):
            try:
                # 执行代码
                exec(code)
                output = stdout_buffer.getvalue()

                # 如果没有打印输出，获取最后一个表达式的值
                if output.strip() == "":
                    tree = ast.parse(code)
                    if isinstance(tree.body[-1], ast.Expr):
                        last_expr = compile(
                            ast.Expression(tree.body[-1].value), '<string>',
                            'eval')
                        output = str(eval(last_expr))

            except Exception as e:
                output = f"发生错误: {str(e)}"

        return output


tool_info_gemini = [{
    "name": "get_current_weather",
    "description": "获取指定地点的天气信息，使用高德开放平台的天气API。",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "查询天气的城市名称"
            }
        },
        "required": ["location"]
    }
}, {
    "name": "get_current_weather_en",
    "description": "获取指定地点的天气信息，使用OpenWeatherMap的天气API。",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "查询天气的城市名称"
            }
        },
        "required": ["location"]
    }
}, {
    "name": "get_current_time",
    "description": "获取当前时间，格式为'年-月-日 时:分:秒'。",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}, {
    "name": "CodeRunner",
    "description": "执行Python代码并返回输出结果或错误信息。",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "要执行的Python代码"
            }
        },
        "required": ["code"]
    }
}]

tools_info_gpt = [{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "获取指定位置的当前天气信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "需要查询天气的地点，例如'北京'。"
                }
            },
            "required": ["location"]
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "get_current_weather_en",
        "description": "获取指定位置的当前天气信息（英文版本）。",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "需要查询天气的地点，例如'New York'。"
                }
            },
            "required": ["location"]
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "获取当前的日期和时间。",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "CodeRunner",
        "description": "执行给定的 Python 代码并返回输出。",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "需要执行的 Python 代码。"
                }
            },
            "required": ["code"]
        }
    }
}]

tools_info_claude = [{
    "name": "get_current_weather",
    "description": "获取指定位置的当前天气信息，使用高德开放平台的天气API",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "要查询天气的地点名称"
            }
        },
        "required": ["location"]
    }
}, {
    "name": "get_current_weather_en",
    "description": "获取指定位置的当前天气信息，使用OpenWeatherMap API",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "要查询天气的地点名称（英文）"
            }
        },
        "required": ["location"]
    }
}, {
    "name": "get_current_time",
    "description": "获取当前的日期和时间",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    }
}, {
    "name": "CodeRunner",
    "description": "执行给定的Python代码并返回输出结果",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "要执行的Python代码"
            }
        },
        "required": ["code"]
    }
}]

tools_info = [{
    "name": "get_current_weather",
    "description": "获取指定位置的当前天气信息，这个函数的位置参数是中文的",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "要查询天气的地点，如城市名或地区名"
            }
        },
        "required": ["location"]
    }
}, {
    "name": "get_current_weather_en",
    "description": "获取指定位置的当前天气信息，这个函数的位置参数是英文的",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "要查询天气的地点，如城市名或地区名（英文）"
            }
        },
        "required": ["location"]
    }
}, {
    "name": "get_current_time",
    "description": "获取当前的日期和时间",
    "input_schema": {
        "type": "object",
        "properties": {}
    }
}, {
    "name": "CodeRunner",
    "description": "执行给定的Python代码并返回输出结果",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "要执行的Python代码"
            }
        },
        "required": ["code"]
    }
}]
