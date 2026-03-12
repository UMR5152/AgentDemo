# 每日论文及业界实践洞察总结Agent

一个基于LangGraph的每日论文及业界资讯洞察总结Agent，根据关键词自动获取最新论文和业界资讯，使用LLM生成洞察报告，并通过Gmail发送。

## 功能特性

- 📄 **论文检索：从arXiv获取最新学术论文
- 🌐 **业界资讯：从Hacker News、Reddit、GitHub获取业界动态
- 🤖 **智能总结：使用LangGraph工作流生成专业洞察报告
- 📧 **邮件推送：通过Gmail SMTP自动发送报告
- ⏰ **定时调度：每日定时自动执行

## 安装

### 1. 环境要求

- Python 3.9+
- conda环境：`agent_demo`

### 2. 安装依赖

```bash
conda activate agent_demo
pip install -r requirements.txt
```

## 配置

编辑 `config.yaml` 文件，填写以下配置：

### 关键词列表
```yaml
keywords:
  - "large language model"
  - "agent"
  - "RAG"
```

### 大模型配置
```yaml
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key-here"
  model_name: "gpt-4o"
```

### 邮箱配置
```yaml
email:
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"  # Gmail应用专用密码
  recipient_emails:
    - "recipient1@example.com"
```

## Gmail应用专用密码设置

1. 开启Google账号的两步验证
2. 访问 https://myaccount.google.com/apppasswords
3. 生成应用专用密码

## 使用方法

### 立即执行一次（试运行，不发送邮件）
```bash
python main.py --once --dry-run
```

### 立即执行一次并发送邮件
```bash
python main.py --once
```

### 启动定时调度器
```bash
python main.py
```
默认每天 `09:00` 执行（可在配置文件中修改）

## 项目结构

```
.
├── config.yaml          # 配置文件
├── config.py          # 配置模型
├── paper_fetcher.py   # 论文检索模块
├── news_fetcher.py   # 业界资讯检索模块
├── summary_workflow.py  # LangGraph总结工作流
├── email_sender.py   # 邮件发送模块
├── main.py          # 主程序入口
├── requirements.txt # 依赖列表
└── README.md        # 说明文档
```

## 配置文件字段说明

| 字段 | 说明 | 必填 |
|------|------|------|
| keywords | 关键词列表 | 是 |
| llm.base_url | 大模型API Base URL | 是 |
| llm.api_key | 大模型API Key | 是 |
| llm.model_name | 大模型名称 | 是 |
| email.sender_email | 发件人邮箱 | 是 |
| email.sender_password | 发件人密码/应用专用密码 | 是 |
| email.recipient_emails | 收件人邮箱列表 | 是 |
# AgentDemo
