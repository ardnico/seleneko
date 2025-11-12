import argparse
from seleneko.automation import SeleniumClient, DriverSettings

def main():
    parser = argparse.ArgumentParser(
        prog="seleneko",
        description="Selenium-based browser automation toolkit"
    )
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--url", type=str, help="URL to open", default="https://example.com")
    args = parser.parse_args()

    settings = DriverSettings(headless=args.headless)
    with SeleniumClient(settings) as cli:
        cli.get(args.url)
        print(f"[INFO] Page title: {cli.driver.title}")

if __name__ == "__main__":
    main()
