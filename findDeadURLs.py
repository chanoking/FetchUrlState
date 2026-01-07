import pandas as pd
import requests

df = pd.read_excel("urls.xlsx")
urls = df["URL"]

status_list = []

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    )
}

for url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=5, allow_redirects=True)

        if r.status_code >= 400:
            status_list.append("Dead")
            continue

        page_text = r.text

        # Deleted first (more specific)
        if any(x in page_text for x in ["삭제", "존재하지", "찾을 수 없"]):
            status_list.append("Deleted")

        # Private (no content containers)
        elif (
            "se-main-container" not in page_text
            and "se_component_wrap" not in page_text
            and "<iframe" not in page_text
        ):
            status_list.append("Private")

        else:
            status_list.append("Alive")

    except requests.exceptions.RequestException:
        status_list.append("Dead")

df["Status"] = status_list
df.to_excel("urls_checked.xlsx", index=False)

print("Done! Results saved to urls_checked.xlsx")
