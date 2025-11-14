# seleneko

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg?logo=python)](https://www.python.org/)
[![Selenium Version](https://img.shields.io/badge/Selenium-4.35.0-43B02A.svg?logo=selenium)](https://www.selenium.dev/)
[![License](https://img.shields.io/badge/License-Apache%202.0-019B8F.svg?logo=apache)](LICENSE)

seleneko は Selenium ベースのブラウザ自動化を快適にする Python ライブラリです。<br>
ヘッドレス・GUI どちらのモードでも安定して動作するよう、ドライバの初期化や
各種ユーティリティを取りそろえています。

## 必要環境

| コンポーネント | バージョン |
| -------------- | ---------- |
| Python         | >= 3.9, < 4.0 |
| Selenium       | >= 4.35.0, < 5.0 |

## インストール

```bash
pip install git+https://github.com/ardnico/seleneko
```

開発版として利用する場合は以下の通りです。

```bash
git clone https://github.com/ardnico/seleneko.git
cd seleneko
pip install -e .
```

## 使い方

```python
from seleneko.automation import SeleniumClient, DriverSettings

settings = DriverSettings(headless=True)
with SeleniumClient(settings) as client:
    client.get("https://example.com")
    print(client.driver.title)
```

## コミット / コーディングルール

- [コミット規約](https://github.com/ardnico/doc/blob/main/CodingRules/commit_rules.adoc)
- [Python コーディング規約](https://github.com/ardnico/doc/blob/main/CodingRules/python_coding_rules.adoc)

## ライセンス

本プロジェクトは [Apache License 2.0](LICENSE) の下で提供されています。

## 作者

- [@ardnico](https://github.com/ardnico)

