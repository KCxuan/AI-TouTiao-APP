import redis.asyncio as redis
from typing import Any
from typing import Dict, List
import json
from typing import Optional

from config.env import require_env

REDIS_HOST = require_env("REDIS_HOST")
REDIS_PORT = int(require_env("REDIS_PORT"))
REDIS_DB = int(require_env("REDIS_DB"))

# 创建 Redis 的连接对象
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)

"""
缓存操作就是围绕 Redis 做“存、取、删、判断、过期”等操作，让数据访问更快、数据库压力更小。
Redis 存储数据：key - value
方法	    参数	            描述
----------------------------------------------------------------
            expire: int (秒)
setex	    key: str
            value: str	        设置缓存并指定过期时间 (秒)
----------------------------------------------------------------
get	        key: str	        获取缓存值。若缓存不存在，返回 None
----------------------------------------------------------------
delete	    key: str	        删除指定的缓存键
----------------------------------------------------------------
exists	    key: str	        检查缓存键是否存在，返回布尔值
----------------------------------------------------------------
"""

# 设置缓存 读取缓存（两种方法： 字符串 和 列表或者字典）
# 读取缓存 字符串
async def get_cache(key: str):
    # return await redis_client.get(key)
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"Error reading cache: {e}")
        return None

# 读取缓存 列表或者字典
async def get_json_cache(key: str):
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data) # 反序列化 就是从原来的字符串转换成列表或者字典
        else:
            return None
    except Exception as e:
        print(f"Error reading cache: {e}")
        return None


# 设置缓存
async def set_cache(key: str, value: Any, expire: int = 3600):
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False) # 序列化 就是把列表或者字典转换成字符串
        await redis_client.set(key, value, ex=expire)
        # 如果设置成功，返回 True
        return True
    except Exception as e:
        print(f"Error writing cache: {e}")
        return False

# 删除缓存(支持一个或者多个)
async def delete_cache(*keys: str):
    try:
        if keys:
            await redis_client.delete(*keys)
        return True
    except Exception as e:
        print(f"Error deleting cache: {e}")
        return False

# 模式删除（按通配符批量清楚键，例如"news_list:3:*"）
async def delete_cache_pattern(pattern: str):
    try:
        count = 0
        # scan_iter 返回一个异步迭代器，逐批扫描出匹配的键（不阻塞 Redis）
        async for key in redis_client.scan_iter(match=pattern, count=100):
            await redis_client.delete(key)
            count += 1
        return count # 返回删除了多少个键
    except Exception as e:
        print(f"Error deleting cache: {e}")
        return 0
