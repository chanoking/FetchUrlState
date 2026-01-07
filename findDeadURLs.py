import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ---------------- Load URLs ----------------
df = pd.read_excel("urls.xlsx")
urls = df["URL"].tolist()

# Messages for detection
deleted_msgs = [
    "게시물이 삭제되었거나 다른 페이지로 변경되었습니다",
    "존재하지",
    "찾을 수 없"
]
private_msgs = [
    "비공개 글 입니다"
]
# Main content containers to check
content_containers = ["se-main-container", "se_component_wrap"]

# ---------------- Playwright Checker ----------------
def check_urls(urls):
    status_list = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for idx, url in enumerate(urls, start=1):
            print(f"[{idx}/{len(urls)}] Checking: {url}")
            try:
                page = browser.new_page()
                status = "Alive"  # default

                # Handler for popups/dialogs
                def dialog_handler(dialog):
                    nonlocal status
                    msg = dialog.message
                    if any(d in msg for d in deleted_msgs):
                        status = "Deleted"
                    elif any(d in msg for d in private_msgs):
                        status = "Private"
                    dialog.dismiss()

                page.on("dialog", dialog_handler)

                # Navigate to URL
                try:
                    response = page.goto(url, timeout=20000)
                    if response is None or response.status >= 400:
                        status = "Dead"
                        page.close()
                        status_list.append(status)
                        continue
                except PlaywrightTimeoutError:
                    status = "Dead"
                    page.close()
                    status_list.append(status)
                    continue

                # Wait for JS rendering
                page.wait_for_timeout(3000)

                # Check main containers for private/deleted messages
                found_container = False
                for container in content_containers:
                    if page.locator(f".{container}").count() > 0:
                        found_container = True
                        container_text = page.locator(f".{container}").inner_text()
                        if any(d in container_text for d in deleted_msgs):
                            status = "Deleted"
                            break
                        elif any(d in container_text for d in private_msgs):
                            status = "Private"
                            break

                # Fallback: check full body text if no container matched
                if not found_container and status == "Alive":
                    body_text = page.inner_text("body")
                    if any(d in body_text for d in deleted_msgs):
                        status = "Deleted"
                    elif any(d in body_text for d in private_msgs):
                        status = "Private"

                page.close()

            except Exception:
                status = "Dead"

            status_list.append(status)

        browser.close()

    return status_list

# ---------------- Run Checker ----------------
statuses = check_urls(urls)
df["Status"] = statuses
df.to_excel("urls_checked_playwright.xlsx", index=False)
print("Done! Results saved to urls_checked_playwright.xlsx")
