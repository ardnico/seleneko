import os
import logging
from datetime import datetime as dt
from logging import getLogger, Formatter
from .encrypter import Enc
import traceback

class config:
    """
    改良版 config クラス
    - ロガー多重登録防止
    - OS依存パスの除去
    - 安全なデータ書き込み
    - 例外ログ強化
    """
    __enc = Enc()

    def __init__(self, delimita=":::", name=__name__):
        self.data = {
            "loglevel": logging.INFO,
            "encrypt": 0,
            "work_dir": 0,
            "data_path": os.path.join(os.getcwd(), "data"),
            "log_path": os.path.join(os.getcwd(), "log"),
        }
        self.delimita = delimita
        self.setting_path = os.path.join(self.data["data_path"], "setting.data")
        self.log_name = os.path.join(self.data["log_path"], f"{name}.log")

        os.makedirs(self.data["data_path"], exist_ok=True)
        os.makedirs(self.data["log_path"], exist_ok=True)

        self.logger = None
        self.read_key()
        self._init_logger_once()

    # -----------------------------------------
    # Logging
    # -----------------------------------------
    def _init_logger_once(self):
        """重複しないロガー初期化"""
        if self.logger is not None:
            return self.logger  # すでに初期化済み

        self.logger = getLogger(__name__)
        if self.logger.handlers:
            # 既にハンドラ登録済みなら再登録しない
            return self.logger

        self.logger.setLevel(self.data.get("loglevel", logging.INFO))

        log_format = Formatter("[%(levelname)s %(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")
        st_handler = logging.StreamHandler()
        st_handler.setFormatter(log_format)
        fl_handler = logging.FileHandler(filename=self.log_name, encoding="utf-8")
        fl_handler.setFormatter(log_format)

        self.logger.addHandler(st_handler)
        self.logger.addHandler(fl_handler)
        return self.logger

    def set_log(self, level: int = None):
        """明示的にログレベル変更（例: logging.DEBUG）"""
        if level:
            self.data["loglevel"] = level
        self._init_logger_once()
        self.logger.setLevel(self.data["loglevel"])

    def write_log(self, text, type=-1, species=""):
        """安全なログ出力（重複なし）"""
        self._init_logger_once()
        level_map = {
            0: "DEBUG",
            1: "INFO",
            2: "WARNING",
            3: "ERROR",
            4: "CRITICAL",
        }
        if type > -1:
            species = level_map.get(type, "INFO")

        method = getattr(self.logger, species.lower(), self.logger.info)
        method(str(text))

    # -----------------------------------------
    # 設定ファイル関連
    # -----------------------------------------
    def read_key(self):
        if not os.path.exists(self.setting_path):
            self.write_data()
            return
        with open(self.setting_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        for line in lines[1:]:  # skip header
            parts = line.strip('"').split(f'"{self.delimita}"')
            if len(parts) != 2:
                continue
            k, v = parts
            try:
                self.data[k] = int(v)
            except ValueError:
                self.data[k] = v

    def write_data(self):
        header = f'"KEY"{self.delimita}"VALUE"\n'
        body = "".join([f'"{k}"{self.delimita}"{v}"\n' for k, v in self.data.items()])
        with open(self.setting_path, "w", encoding="utf-8") as f:
            f.write(header + body)

    def set_data(self, key, value):
        self.data[key] = value
        # 頻繁に呼ばれるため即書き込みは避ける設計も可能
        self.write_data()

    def get_data(self, key):
        return self.data.get(key)

    def del_data(self, key):
        if key in self.data:
            self.data.pop(key)
            self.write_data()

    # -----------------------------------------
    # 認証情報関連
    # -----------------------------------------
    def set_id(self, id_line, pwd_line):
        self.data["id"] = self.__enc.encrypt(id_line)
        self.data["pwd"] = self.__enc.encrypt(pwd_line)
        self.write_data()

    def get_id(self):
        id_enc = self.data.get("id")
        pwd_enc = self.data.get("pwd")
        if not id_enc or not pwd_enc:
            self.write_log("No credentials found", species="WARNING")
            return None, None
        try:
            return self.__enc.decrypt(id_enc), self.__enc.decrypt(pwd_enc)
        except Exception as e:
            self.write_log(f"Decryption error: {e}", species="ERROR")
            return None, None

    def del_id(self):
        for key in ("id", "pwd"):
            self.del_data(key)

    # -----------------------------------------
    # Utility
    # -----------------------------------------
    def get_date_str_ymd(self):
        return dt.now().strftime("%Y%m%d")

    def get_date_str_ymdhms(self):
        return dt.now().strftime("%Y/%m/%d %H:%M:%S")

    def log_exception(self, func):
        """例外をキャッチしてログ出力するデコレータ"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_trace = traceback.format_exc()
                self.write_log(f"{func.__name__}() failed: {e}\n{err_trace}", species="ERROR")
                raise
        return wrapper
