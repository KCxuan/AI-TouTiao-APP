import os

from dotenv import load_dotenv

load_dotenv()


def require_env(name: str, *, allow_empty: bool = False) -> str:
    """读取必需的环境变量；缺失时提示去复制 .env.example。"""
    if name not in os.environ:
        raise RuntimeError(
            f"缺少环境变量 {name}。请复制 .env.example 为 .env 并填写后重启。"
        )
    value = os.environ[name]
    if not allow_empty and not str(value).strip():
        raise RuntimeError(
            f"环境变量 {name} 不能为空。请检查项目根目录的 .env。"
        )
    return value
