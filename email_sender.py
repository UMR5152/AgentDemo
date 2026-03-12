"""
邮件发送模块 - 使用Gmail SMTP发送邮件
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import List
import logging
import re

logger = logging.getLogger(__name__)


class EmailSender:
    """邮件发送器"""

    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        use_tls: bool = True
    ):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.use_tls = use_tls

    def _extract_title(self, html_content: str) -> str:
        """从HTML内容中提取标题"""
        # 尝试从Markdown标题提取
        import re
        h1_match = re.search(r'^#\s+(.+)$', html_content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # 尝试从第一个H1标签提取
        h1_tag_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)
        if h1_tag_match:
            return re.sub(r'<[^>]+>', '', h1_tag_match.group(1)).strip()

        return "每日论文及业界洞察"

    def _markdown_to_html(self, markdown_text: str) -> str:
        """简单的Markdown转HTML"""
        html = markdown_text

        # 标题
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)

        # 粗体和斜体
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # 链接
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

        # 列表
        html = re.sub(r'^\s*[-*+]\s+(.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

        # 段落和换行
        html = re.sub(r'\n\n', r'</p><p>', html)
        html = re.sub(r'\n', r'<br>', html)

        if not html.startswith('<p>'):
            html = '<p>' + html
        if not html.endswith('</p>'):
            html = html + '</p>'

        # 包装在HTML body中
        html = f"""
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
        h2 {{ color: #202124; margin-top: 30px; }}
        h3 {{ color: #5f6368; }}
        a {{ color: #1a73e8; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .paper, .news {{ background: #f8f9fa; border-left: 4px solid #1a73e8; padding: 15px; margin: 15px 0; border-radius: 0 4px 4px 0; }}
        li {{ margin: 8px 0; }}
    </style>
</head>
<body>
{html}
</body>
</html>
"""
        return html

    def send_email(
        self,
        recipient_emails: List[str],
        subject: str,
        content: str,
        is_html: bool = True
    ) -> bool:
        """
        发送邮件

        Args:
            recipient_emails: 收件人邮箱列表
            subject: 邮件主题
            content: 邮件内容
            is_html: 是否为HTML格式

        Returns:
            是否发送成功
        """
        msg = MIMEMultipart()
        msg['From'] = formataddr(("每日洞察Agent", self.sender_email))
        msg['To'] = ", ".join(recipient_emails)
        msg['Subject'] = subject

        if is_html:
            html_content = self._markdown_to_html(content)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(content, 'plain', 'utf-8'))

        try:
            logger.info(f"正在连接SMTP服务器 {self.smtp_host}:{self.smtp_port}")

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                logger.info("正在登录SMTP服务器")
                server.login(self.sender_email, self.sender_password)

                logger.info(f"正在发送邮件给: {recipient_emails}")
                server.send_message(msg)

            logger.info("邮件发送成功")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP认证失败，请检查邮箱和密码/应用专用密码")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            return False
        except Exception as e:
            logger.error(f"发送邮件时出错: {e}")
            return False

    def send_insight_report(
        self,
        recipient_emails: List[str],
        report_content: str
    ) -> bool:
        """
        发送洞察报告

        Args:
            recipient_emails: 收件人邮箱列表
            report_content: 报告内容（Markdown格式）

        Returns:
            是否发送成功
        """
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        subject = f"📊 每日论文及业界洞察 - {date_str}"

        return self.send_email(
            recipient_emails=recipient_emails,
            subject=subject,
            content=report_content,
            is_html=True
        )
