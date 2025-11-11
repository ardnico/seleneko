# 🦊 seleneko

**seleneko** は、Selenium をベースにした軽量かつ堅牢なブラウザ自動化ライブラリです。  
ヘッドレスモードだけでなく、GUIモードでもクリックや入力の安定性を保証するよう設計されています。

---

## ✨ 特徴

- ✅ Selenium の煩雑なオプション設定を自動化  
- ✅ クリック／入力操作を「成功判定つき」で再試行  
- ✅ 一時ユーザープロファイル生成によるクリーン環境実行  
- ✅ config / encryption のユーティリティを同梱  
- ✅ ログ・暗号化・エラーハンドリングまで一体化

---

## 📦 インストール

```
pip install seleneko
```

もしくは開発版として：

```
git clone https://github.com/yourname/seleneko.git
cd seleneko
pip install -e .
```

---

## 🚀 使い方

### 最小構成

```
from seleneko.automation import SeleniumClient, DriverSettings

settings = DriverSettings(headless=True)
with SeleniumClient(settings) as cli:
    cli.get("https://example.com")
    print(cli.driver.title)
```

---

### 高信頼クリック

```
from seleneko.automation import SeleniumClient, DriverSettings

with SeleniumClient(DriverSettings(headless=False)) as cli:
    cli.get("https://example.com/login")

    cli.type_text_smart(("id", "username"), "my_id")
    cli.type_text_smart(("id", "password"), "my_password")
    cli.click_smart(("css", "button[type=submit]"),
                    success=cli.expect_url_change(from_url=cli.driver.current_url))
```

---

### 設定と暗号化

```
from seleneko.core import config

conf = config(name="example")
conf.set_id("myuser", "mypassword")
uid, pwd = conf.get_id()
print(uid, pwd)
```

---

## 🧰 CLI 利用例

```
seleneko --url https://www.python.org
```

もしくは：

```
python -m seleneko --headless
```

---

## 🧪 テスト

```
pytest
```

---

## 📜 ライセンス

MIT License  
Copyright (c) 2025 Niko

---

## 🌐 プロジェクト情報

- **リポジトリ**: [https://github.com/yourname/seleneko](https://github.com/yourname/seleneko)
- **PyPI**: [https://pypi.org/project/seleneko](https://pypi.org/project/seleneko)
- **作者**: Niko
- **対応環境**: Python 3.9+

