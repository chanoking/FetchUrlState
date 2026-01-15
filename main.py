import asyncio
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

df = pd.read_excel("urls.xlsx")
urls = df["URL"].tolist()

deleted_msgs = ["게시물이 삭제되었거나"]
private_msgs = ["비공개 글 입니다"]


async def check_urls(urls):
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        for idx, url in enumerate(urls, start=1):
            status = "Alive"
            page = None  # ⭐ 중요

            try:
                # page 생성 보호
                page = await asyncio.wait_for(
                    browser.new_page(), timeout=2
                )

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

                response = await page.goto(url, timeout=20000)

                if response is None or response.status >= 400:
                    status = "Dead"

            except asyncio.TimeoutError:
                status = "Dead"

                # ⭐ browser 오염 → 재시작
                await browser.close()
                browser = await p.chromium.launch(headless=False)

                continue

            except PlaywrightTimeoutError:
                status = "Dead"

            except Exception:
                status = "Dead"

            finally:
                print(f"[{idx}/{len(urls)}] {url} {status}")
                results.append(status)

                if page is not None:
                    await page.close()

        await browser.close()

    return results

statuses = asyncio.run(check_urls(urls))
df["Status"] = statuses
df.to_excel("urls_checked.xlsx", index=False)
print("✅ Done!")
