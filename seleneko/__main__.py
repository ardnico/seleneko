from .seleneko import Seleneko

def main():
    # 引数処理が必要なら argparse をここで
    print("Starting Seleneko...")
    app = Seleneko()
    # ここで app を実際に動かす処理を書く
    # 例: app.run() など
    print("Seleneko initialized:", app)

if __name__ == "__main__":
    main()
