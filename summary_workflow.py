"""
使用LangGraph实现的总结工作流
"""
from typing import TypedDict, List, Dict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from operator import add
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Agent状态"""
    keywords: List[str]
    papers: List[Dict]
    news: List[Dict]
    paper_summaries: List[str]
    news_summaries: List[str]
    final_report: str
    messages: Annotated[Sequence[BaseMessage], add]


class SummaryWorkflow:
    """总结工作流"""

    def __init__(self, base_url: str, api_key: str, model_name: str):
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model_name,
            temperature=0.7
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建LangGraph工作流"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("summarize_papers", self._summarize_papers)
        workflow.add_node("summarize_news", self._summarize_news)
        workflow.add_node("generate_report", self._generate_report)

        # 设置入口点
        workflow.set_entry_point("summarize_papers")

        # 添加边
        workflow.add_edge("summarize_papers", "summarize_news")
        workflow.add_edge("summarize_news", "generate_report")
        workflow.add_edge("generate_report", END)

        return workflow.compile()

    def _summarize_papers(self, state: AgentState) -> AgentState:
        """总结论文"""
        logger.info("开始总结论文...")
        papers = state.get("papers", [])
        summaries = []

        if not papers:
            return {
                "paper_summaries": [],
                "messages": [HumanMessage(content="No papers to summarize")]
            }

        for i, paper in enumerate(papers, 1):
            prompt = f"""请为以下学术论文写一个简洁的摘要（100-150字）：

标题: {paper['title']}
作者: {', '.join(paper['authors'][:3])}{' et al.' if len(paper['authors']) > 3 else ''}
摘要: {paper['abstract'][:500]}...
链接: {paper['url']}

请包含：
1. 论文的核心问题/目标
2. 主要方法/创新点
3. 关键结论/贡献

格式：
📄 标题
   - 核心要点: [一句话总结]
   - 方法: [主要方法]
   - 链接: {paper['url']}
"""

            try:
                response = self.llm.invoke([
                    SystemMessage(content="你是一个专业的学术论文总结助手。"),
                    HumanMessage(content=prompt)
                ])
                summaries.append(response.content)
            except Exception as e:
                logger.error(f"总结论文失败: {e}")
                summaries.append(f"📄 {paper['title']}\n   - 链接: {paper['url']}")

        return {
            "paper_summaries": summaries,
            "messages": [HumanMessage(content="Papers summarized")]
        }

    def _summarize_news(self, state: AgentState) -> AgentState:
        """总结业界资讯"""
        logger.info("开始总结业界资讯...")
        news = state.get("news", [])
        summaries = []

        if not news:
            return {
                "news_summaries": [],
                "messages": [HumanMessage(content="No news to summarize")]
            }

        for item in news:
            prompt = f"""请为以下业界资讯写一个简洁的摘要（50-100字）：

标题: {item['title']}
来源: {item['source']}
摘要/描述: {item['summary']}
链接: {item['url']}

请突出这个资讯的重要性和关注点。

格式：
🌐 标题
   - 来源: {item['source']}
   - 要点: [一句话总结]
   - 链接: {item['url']}
"""

            try:
                response = self.llm.invoke([
                    SystemMessage(content="你是一个专业的科技资讯总结助手。"),
                    HumanMessage(content=prompt)
                ])
                summaries.append(response.content)
            except Exception as e:
                logger.error(f"总结资讯失败: {e}")
                summaries.append(f"🌐 {item['title']}\n   - 来源: {item['source']}\n   - 链接: {item['url']}")

        return {
            "news_summaries": summaries,
            "messages": [HumanMessage(content="News summarized")]
        }

    def _generate_report(self, state: AgentState) -> AgentState:
        """生成最终报告"""
        logger.info("生成最终报告...")
        keywords = state.get("keywords", [])
        paper_summaries = state.get("paper_summaries", [])
        news_summaries = state.get("news_summaries", [])

        date_str = datetime.now().strftime("%Y年%m月%d日")

        paper_section = "\n\n".join(paper_summaries) if paper_summaries else "本日无相关论文。"
        news_section = "\n\n".join(news_summaries) if news_summaries else "本日无相关业界资讯。"

        final_prompt = f"""请将以下内容整合成一份专业、易读的每日洞察报告。

日期: {date_str}
关键词: {', '.join(keywords)}

【论文总结】
{paper_section}

【业界资讯】
{news_section}

请添加：
1. 一个吸引人的邮件主题和报告标题
2. 一段整体的洞察摘要（200-300字），分析本日的趋势
3. 对每个部分进行适当的格式美化
4. 结尾的总结与展望

请使用Markdown格式。"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="你是一个专业的科技洞察分析师，擅长撰写清晰、专业的日报。"),
                HumanMessage(content=final_prompt)
            ])
            final_report = response.content
        except Exception as e:
            logger.error(f"生成最终报告失败: {e}")
            final_report = f"""# 每日论文及业界洞察 - {date_str}

## 关键词
{', '.join(keywords)}

## 学术论文
{paper_section}

## 业界资讯
{news_section}
"""

        return {
            "final_report": final_report,
            "messages": [HumanMessage(content="Report generated")]
        }

    def run(
        self,
        keywords: List[str],
        papers: List[Dict],
        news: List[Dict]
    ) -> str:
        """
        运行工作流

        Args:
            keywords: 关键词列表
            papers: 论文列表（字典格式）
            news: 资讯列表（字典格式）

        Returns:
            最终报告
        """
        initial_state: AgentState = {
            "keywords": keywords,
            "papers": papers,
            "news": news,
            "paper_summaries": [],
            "news_summaries": [],
            "final_report": "",
            "messages": []
        }

        result = self.graph.invoke(initial_state)
        return result.get("final_report", "")
