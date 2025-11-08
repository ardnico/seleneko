# seleneko

[![Python Version](https://img.shields.io/badge/Python-3.9-3776AB.svg?logo=python)]()
[![Selenium Version](https://img.shields.io/badge/Selenium-4.35.0-43B02A.svg?logo=selenium)]()
[![License](https://img.shields.io/badge/license-ApacheLicense2.0-019B8F?logo=apachelucene)]()

## Description

Seleneko supports your Selenium development.
ex. await for accessing any site, handle any browsers, ...

| Requirement          |
| -------------------- |
| Python >= 3.9, < 4.0 |
| selenium  = 4.35.0   |

## Install

```bash
pip install git+https://github.com/ardnico/seleneko
```

- For development

```bash
git clone https://github.com/ユーザー名/プロジェクト名.git
cd プロジェクト名
pip install -e ".[dev]"
```

## Usage



## Contribution

1. Fork it ( http://github.com//ardnico/UseSel )
2. Create your feature branch (git checkout -b my-new-feature)
3. Commit your changes (git commit -am 'Add some feature')
4. Push to the branch (git push origin my-new-feature)
5. Create new Pull Request

## Licence

show LICENSE file.

## Author

[nico](https://github.com/ardnico)

## Bazel（簡単ガイド）

以下はこのリポジトリで Bazel を使うための最小限の手順とコマンド例です。

### 前提
- Bazel または Bazelisk がインストールされていること（https://bazel.build/ や https://github.com/bazelbuild/bazelisk を参照）。
- Python 用ルール（rules_python）を使っています。外部依存は MODULE.bazel / requirements.txt や各 BUILD ファイルで定義されています。

### 主要コマンド
- 全ビルド（依存のダウンロードを含む）
  ```
  bazel build //...
  ```
- 特定の Python バイナリを実行（例: pythoneko/app）
  ```
  bazel run //pythoneko:app
  ```
- テストを実行（テスト用の BUILD ターゲット名を指定）
  ```
  bazel test //tests:unit
  ```
- 依存の更新やフェッチに失敗したとき
  - まず `bazel clean --expunge` を試す
  - ネットワークやプロキシの影響がある場合は環境変数（HTTP_PROXY 等）を確認する

### このリポジトリの例
- Python アプリケーション（pythoneko）用の BUILD は `pythoneko/BUILD.bazel` にあります。
  - 実行: `bazel run //pythoneko:app`
- テスト用の BUILD は `tests/BUILD.bazel` にあります（rules_python の py_test を利用）。
  - 実行: `bazel test //tests:unit`
- 外部 Python パッケージは `requirements.txt` と `MODULE.bazel` / `MODULE.bazel` の設定で管理されています。Bazel は初回ビルド時に必要な外部リポジトリを取得します。

### 開発ワークフローのヒント
- 変更を加えたらまずコンパイル（`bazel build`）→ テスト（`bazel test`）を回すと依存関係や構成ミスに早く気づけます。
- Windows 環境では Bazel のサンドボックスやツールチェインの影響で外部ツールを正しく見つけられない場合があります。問題が出たら、コマンドプロンプトを管理者権限で開くか、必要なツール（Visual Studio Build Tools など）が PATH にあるか確認してください。
- rules_python の挙動や pip ベースの依存管理について詳しく知りたい場合は rules_python のドキュメントを参照してください: https://github.com/bazelbuild/rules_python

### よくある問題
- 「依存が見つからない / fetch に失敗する」
  - ネットワーク、プロキシ、認証が原因の場合が多いです。環境変数と `bazel fetch //...` の出力を確認してください。
- 「Python 実行エラー（モジュールが見つからない）」
  - BUILD ファイルの deps が正しく指定されているか確認。`requirements.txt` の内容が MODULE.bazel の設定に反映されているかもチェック。

必要なら、このリポジトリ固有の Bazel ワークフロー（例: CI 用の bazel コマンドや、MODULE.bazel の再生成手順）を具体的にまとめます。どの点を詳しく知りたいですか？ (インストール手順 / Windows 固有の注意点 / rules_python の使い方 など)
