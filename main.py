import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

df = pd.read_excel("urls.xlsx")
urls = df["URL"].tolist()

deleted_msgs = ["게시물이 삭제되었거나"]
private_msgs = ["비공개 글 입니다"]

def check_urls(urls):
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for idx, url in enumerate(urls, start=1):
            print(f"[{idx}/{len(urls)}] Checking: {url}")
            status = "Alive"
            page = browser.new_page()

            # dialog 핸들러
            def dialog_handler(dialog):
                nonlocal status
                msg = dialog.message
                if any(d in msg for d in deleted_msgs):
                    status = "Deleted"
                elif any(d in msg for d in private_msgs):
                    status = "Private"
                dialog.dismiss()

            page.on("dialog", dialog_handler)

            try:
                response = page.goto(url, timeout=20000)
                if response is None or response.status >= 400:
                    status = "Dead"
            except PlaywrightTimeoutError:
                status = "Dead"
            except Exception:
                status = "Dead"
            finally:
                page.close()
                results.append(status)

    return results

statuses = check_urls(urls)
df["Status"] = statuses
df.to_excel("urls_checked.xlsx", index=False)
print("✅ Done!")
