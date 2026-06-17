import os
import json

def Get_model_config(model: str):
    """
    从config.json中获取模型配置
    
    Args:
        model: 模型名称
        
    Returns:
        tuple: (model_name, api_key, base_url)
    """
    # 默认配置值
    default_config = ("nebulacoder-lite-v7.0", "10171727", "http://nebulacoder.dev.zte.com.cn:40081/v1")
    
    try:
        # 读取config.json文件
        with open("../config/config.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # 获取模型配置
        model_config = config_data["models"].get(model)
        if not model_config:
            raise ValueError(f"模型 {model} 在配置文件中不存在")
        
        model_name = model_config["model"]
        base_url = model_config["url"]
        api_key = model_config["key"]
        
        return model_name, api_key, base_url
    except FileNotFoundError:
        return default_config
    except KeyError:
        return default_config
    except ValueError as e:
        return default_config
    except Exception as e:
        return default_config

def Clear_proxy():
    for p in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'):
        os.environ.pop(p, None)
