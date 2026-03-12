"""
配置管理模块
"""
from typing import List
from pydantic import BaseModel, Field
import yaml


class LLMConfig(BaseModel):
    """大模型配置"""
    base_url: str = Field(..., description="大模型API Base URL")
    api_key: str = Field(..., description="大模型API Key")
    model_name: str = Field(..., description="大模型名称")


class EmailConfig(BaseModel):
    """邮箱配置"""
    sender_email: str = Field(..., description="发件人邮箱")
    sender_password: str = Field(..., description="发件人密码/应用专用密码")
    recipient_emails: List[str] = Field(..., description="收件人邮箱列表")


class SMTPConfig(BaseModel):
    """SMTP配置"""
    host: str = Field(default="smtp.gmail.com", description="SMTP服务器地址")
    port: int = Field(default=587, description="SMTP服务器端口")
    use_tls: bool = Field(default=True, description="是否使用TLS")


class SearchConfig(BaseModel):
    """搜索配置"""
    max_papers: int = Field(default=5, description="最大论文数量")
    max_news: int = Field(default=5, description="最大资讯数量")
    days_back: int = Field(default=1, description="搜索时间范围（天）")


class ScheduleConfig(BaseModel):
    """调度配置"""
    daily_time: str = Field(default="09:00", description="每日执行时间")


class AgentConfig(BaseModel):
    """Agent总配置"""
    keywords: List[str] = Field(..., description="关键词列表")
    llm: LLMConfig = Field(..., description="大模型配置")
    email: EmailConfig = Field(..., description="邮箱配置")
    smtp: SMTPConfig = Field(default_factory=SMTPConfig, description="SMTP配置")
    search: SearchConfig = Field(default_factory=SearchConfig, description="搜索配置")
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig, description="调度配置")

    @classmethod
    def from_yaml(cls, file_path: str) -> "AgentConfig":
        """从YAML文件加载配置"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)
