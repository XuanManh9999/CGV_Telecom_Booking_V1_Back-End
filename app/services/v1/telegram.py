import time
from typing import Optional, Dict, Any
import logging
import pandas as pd
import requests
from tabulate import tabulate
from telegram.constants import ParseMode

from app.core.config import TelegramConfig



# Tạo logger riêng cho Telegram Bot
telegram_logger = logging.getLogger("telegram_bot_logger")
telegram_logger.setLevel(logging.ERROR)

# Xóa tất cả các handler cũ của logger để tránh bị ảnh hưởng bởi các log khác
for handler in telegram_logger.handlers[:]:
    telegram_logger.removeHandler(handler)

# Cấu hình ghi log vào file
file_handler = logging.FileHandler("telegram_bot_log.log", encoding="utf-8")
file_handler.setLevel(logging.ERROR)

# Định dạng log
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)

# Gán handler cho logger
telegram_logger.addHandler(file_handler)


class TelegramBot:
    """
    A class to interact with the Telegram Bot API.
    """

    def __init__(self, token: str, max_retries: int = TelegramConfig['MAX_RETRIES'],
                 retry_delay: int = TelegramConfig['RETRY_DELAY']):
        """
        Initializes the TelegramBot instance.

        Args:
            token (str): The bot token from BotFather.
            max_retries (int): Maximum number of retries for failed requests.
            retry_delay (int): Delay in seconds between retries.
        """
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def send_message(self, chat_id: int, message: str, parse_mode: str = ParseMode.MARKDOWN) -> Optional[
        Dict[str, Any]]:
        """
        Sends a message to a Telegram chat.

        Args:
            chat_id (int): The chat ID to send the message to.
            message (str): The message text.
            parse_mode (str): The parse mode for the message.

        Returns:
            Optional[Dict[str, Any]]: The response from the Telegram API if successful, else None.
        """
        # Escape các ký tự đặc biệt nếu dùng Markdown
        if parse_mode == ParseMode.MARKDOWN:
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                message = message.replace(char, f'\\{char}')

        url = f"{self.base_url}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': parse_mode}
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(url, data=payload, timeout=30)

                if response.status_code == 200:
                    print(f"✓ Message sent successfully to {chat_id}")
                    return response.json()
                else:
                    print(f"Response: {response.text}")
                    telegram_logger.error(f"Đã xảy ra lỗi gửi tin nhắn với nội dung: {message} ")
                    return None

            except requests.exceptions.RequestException as e:
                error_msg = f"✗ Attempt {attempt}/{self.max_retries} failed | Error: {e}"
                print(f"error_msg: {error_msg}")
            if attempt < self.max_retries:
                time.sleep(self.retry_delay)

        print("✗ All retry attempts failed. Message not sent.")
        return None

    def send_table(self, chat_id: int, df: pd.DataFrame, format_cols: Dict = None, chunk_size: int = 10) -> bool:
        """
        Gửi bảng dữ liệu từ DataFrame đến Telegram chat, chia thành các đoạn nhỏ

        Args:
            chat_id (int): ID của chat cần gửi
            df (pd.DataFrame): DataFrame cần hiển thị
            format_cols (Dict): Dictionary chỉ định format cho từng cột
            chunk_size (int): Số dòng dữ liệu gửi mỗi lần (mặc định là 10)

        Returns:
            bool: True nếu gửi thành công tất cả các phần, False nếu có lỗi
        """
        try:
            formatted_df = df.copy()

            if format_cols:
                for col, fmt in format_cols.items():
                    if col in formatted_df.columns:
                        formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:{fmt}}")

            # Tính số lượng phần cần chia
            total_chunks = (len(formatted_df) + chunk_size - 1) // chunk_size

            for i in range(total_chunks):
                start_idx = i * chunk_size
                end_idx = min((i + 1) * chunk_size, len(formatted_df))
                chunk_df = formatted_df.iloc[start_idx:end_idx]

                # Chuyển DataFrame chunk thành bảng
                table = tabulate(chunk_df, headers='keys', tablefmt='pretty', showindex=False)

                # Gửi phần dữ liệu với thông tin về phần hiện tại
                message = f"Phần {i + 1}/{total_chunks}:\n<pre>{table}</pre>"
                result = self.send_message(chat_id, message, parse_mode=ParseMode.HTML)

                if result is None:
                    print(f"✗ Lỗi khi gửi phần {i + 1}/{total_chunks}")
                    return False

                # Đợi một chút giữa các lần gửi để tránh spam
                if i < total_chunks - 1:
                    time.sleep(1)

            return True

        except Exception as e:
            print(f"✗ Lỗi khi gửi bảng: {str(e)}")
            return False