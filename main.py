"""
每日论文及业界实践洞察总结Agent - 主程序入口
"""
import logging
import sys
import time
from datetime import datetime
import schedule

from config import AgentConfig
from paper_fetcher import PaperFetcher
from news_fetcher import NewsFetcher
from summary_workflow import SummaryWorkflow
from email_sender import EmailSender

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


class DailyInsightAgent:
    """每日洞察Agent"""

    def __init__(self, config_path: str = "config.yaml"):
        logger.info("正在加载配置...")
        self.config = AgentConfig.from_yaml(config_path)

        logger.info("正在初始化各模块...")
        self.paper_fetcher = PaperFetcher(
            max_papers=self.config.search.max_papers,
            days_back=self.config.search.days_back
        )

        self.news_fetcher = NewsFetcher(
            max_news=self.config.search.max_news,
            days_back=self.config.search.days_back
        )

        self.summary_workflow = SummaryWorkflow(
            base_url=self.config.llm.base_url,
            api_key=self.config.llm.api_key,
            model_name=self.config.llm.model_name
        )

        self.email_sender = EmailSender(
            sender_email=self.config.email.sender_email,
            sender_password=self.config.email.sender_password,
            smtp_host=self.config.smtp.host,
            smtp_port=self.config.smtp.port,
            use_tls=self.config.smtp.use_tls
        )

        logger.info("Agent初始化完成")

    def run_once(self, dry_run: bool = False):
        """
        执行一次洞察任务

        Args:
            dry_run: 是否为试运行（不发送邮件）
        """
        logger.info("=" * 50)
        logger.info("开始执行每日洞察任务")
        logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 50)

        try:
            # 1. 获取论文
            logger.info("步骤 1/5: 获取最新论文...")
            papers = self.paper_fetcher.fetch_papers(self.config.keywords)
            papers_dict = [p.to_dict() for p in papers]
            logger.info(f"获取到 {len(papers_dict)} 篇论文")

            # 2. 获取业界资讯
            logger.info("步骤 2/5: 获取业界资讯...")
            news = self.news_fetcher.fetch_news(self.config.keywords)
            news_dict = [n.to_dict() for n in news]
            logger.info(f"获取到 {len(news_dict)} 条资讯")

            # 3. 生成总结报告
            logger.info("步骤 3/5: 生成洞察报告...")
            report = self.summary_workflow.run(
                keywords=self.config.keywords,
                papers=papers_dict,
                news=news_dict
            )
            logger.info("报告生成完成")

            # 保存报告到本地
            report_file = f"report_{datetime.now().strftime('%Y%m%d')}.md"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"报告已保存到: {report_file}")

            # 4. 发送邮件
            if not dry_run:
                logger.info("步骤 4/5: 发送邮件...")
                success = self.email_sender.send_insight_report(
                    recipient_emails=self.config.email.recipient_emails,
                    report_content=report
                )
                if success:
                    logger.info("邮件发送成功")
                else:
                    logger.error("邮件发送失败")
            else:
                logger.info("步骤 4/5: [试运行] 跳过邮件发送")
                print("\n" + "=" * 80)
                print("报告预览:")
                print("=" * 80)
                print(report)
                print("=" * 80 + "\n")

            logger.info("=" * 50)
            logger.info("任务执行完成")
            logger.info("=" * 50)

            return report

        except Exception as e:
            logger.error(f"任务执行出错: {e}", exc_info=True)
            raise

    def start_scheduler(self):
        """启动定时调度器"""
        daily_time = self.config.schedule.daily_time
        logger.info(f"启动定时调度器，每日执行时间: {daily_time}")

        # 设置定时任务
        schedule.every().day.at(daily_time).do(self.run_once)

        logger.info("调度器已启动，等待执行...")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("调度器已停止")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="每日论文及业界实践洞察总结Agent"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="配置文件路径"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="立即执行一次任务并退出"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行（不发送邮件，打印报告）"
    )

    args = parser.parse_args()

    # 创建Agent实例
    agent = DailyInsightAgent(config_path=args.config)

    if args.once or args.dry_run:
        # 执行一次
        agent.run_once(dry_run=args.dry_run)
    else:
        # 启动调度器
        agent.start_scheduler()


if __name__ == "__main__":
    main()
