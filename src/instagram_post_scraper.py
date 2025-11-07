"""
instagram_profile_image_scraper.py

Notes:
- Place a .env file in the root folder of the project (one level above src/) with:
    INSTAGRAM_USERNAME=your_user
    INSTAGRAM_PASSWORD=your_pass

- Run: python src/instagram_post_scraper.py
- The target profile and number of images are set in Config
- Images will be saved in images/<target_profile>/ one level above src/
"""

import os
import time
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
# you can use chrome or other browsers
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import dotenv_values

# ---------- Config ----------
MIN_ALT_LEN = 15                  # Filter out images with short alt (icons)
SCROLL_PAUSE = 2                  # Seconds to wait after each scroll
MAX_SCROLL_ROUNDS_WITHOUT_NEW = 4  # Stop if no new images after multiple scrolls
TARGET_PROFILE = "barbaralennie"  # Target Instagram profile
NUM_IMAGES = 5                    # Number of images to download
# ----------------------------

# ---- load .env (from root folder) ----


def load_env(path=None):
    if path is None:
        path = Path(__file__).parent.parent / ".env"
    env = {}
    if os.path.exists(path):
        try:
            env = dotenv_values(path)
            return {k: v for k, v in env.items() if v is not None}
        except Exception:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


env = load_env()
INSTAGRAM_USERNAME = env.get("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = env.get("INSTAGRAM_PASSWORD")

if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
    print("Place INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in the .env file (root folder) and run again.")
    raise SystemExit(1)

# ---- prepare download folder ----
download_root = Path(__file__).parent.parent / "images" / TARGET_PROFILE
download_root.mkdir(parents=True, exist_ok=True)

# ---- start selenium ----
edge_options = Options()
edge_options.add_argument("--start-maximized")
edge_options.add_argument("--disable-notifications")
edge_options.add_argument("--inprivate")
# edge_options.add_argument("--headless=new")  # optional

driver = webdriver.Edge(options=edge_options)
wait = WebDriverWait(driver, 30)

try:
    # ---- login ----
    driver.get("https://www.instagram.com/accounts/login/")

    username_input = wait.until(
        EC.presence_of_element_located((By.NAME, "username")))
    username_input.clear()
    username_input.send_keys(INSTAGRAM_USERNAME)

    password_input = wait.until(
        EC.presence_of_element_located((By.NAME, "password")))
    password_input.clear()
    password_input.send_keys(INSTAGRAM_PASSWORD)

    login_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@type='submit']")))
    login_button.click()

    time.sleep(4)

    # close potential dialogs
    for _ in range(5):
        try:
            btn = driver.find_element(By.XPATH,
                                      "//button[normalize-space(.)='Not Now' or normalize-space(.)='Not now' or normalize-space(.)='Save info' or normalize-space(.)='Save']"
                                      )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
        except Exception:
            break

    # ---- go to target profile ----
    profile_url = f"https://www.instagram.com/{TARGET_PROFILE}/"
    driver.get(profile_url)
    time.sleep(4)

    # ---- find tablist and parent_div ----
    tablist_div = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//div[@role="tablist"]')))
    parent_div = tablist_div.find_element(By.XPATH, "./..")

    try:
        target_div = parent_div.find_element(
            By.XPATH, "following-sibling::div[1]")
    except Exception:
        target_div = None

    # ---- scrolling & collecting images ----
    collected_urls = []
    seen = set()
    scroll_rounds_without_new = 0
    prev_count = 0
    scan_root = target_div if target_div is not None else driver.find_element(
        By.TAG_NAME, "body")

    while len(collected_urls) < NUM_IMAGES:
        imgs = scan_root.find_elements(By.TAG_NAME, "img")
        for img in imgs:
            try:
                src = img.get_attribute("src") or ""
                alt = (img.get_attribute("alt") or "").strip()
            except Exception:
                continue
            if not src or not src.startswith("http"):
                continue
            if len(alt) < MIN_ALT_LEN:
                continue
            if src in seen:
                continue
            seen.add(src)
            collected_urls.append((src, alt))
            if len(collected_urls) >= NUM_IMAGES:
                break

        if len(collected_urls) == prev_count:
            scroll_rounds_without_new += 1
        else:
            scroll_rounds_without_new = 0
            prev_count = len(collected_urls)

        if len(collected_urls) >= NUM_IMAGES:
            break

        if scroll_rounds_without_new >= MAX_SCROLL_ROUNDS_WITHOUT_NEW:
            break

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)

        # update scan_root in case DOM changed
        try:
            tablist_div = driver.find_element(
                By.XPATH, '//div[@role="tablist"]')
            parent_div = tablist_div.find_element(By.XPATH, "./..")
            target_div = parent_div.find_element(
                By.XPATH, "following-sibling::div[1]")
            scan_root = target_div
        except Exception:
            scan_root = scan_root

    # ---- result handling ----
    found_n = len(collected_urls)
    if found_n == 0:
        print("No images found. The profile may be private or have a different structure.")
    else:
        print(f"\nNumber of images found: {found_n}")
        if found_n < NUM_IMAGES:
            print(
                f"Notice: the profile has only {found_n} images; fewer than requested {NUM_IMAGES}.")
        sess = requests.Session()
        sess.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        for c in driver.get_cookies():
            sess.cookies.set(c['name'], c['value'], domain=c.get('domain'))

        to_download = collected_urls[:min(found_n, NUM_IMAGES)]
        for idx, (url, alt) in enumerate(to_download, start=1):
            try:
                ext = ".jpg"
                if "jpg" in url.lower() or "jpeg" in url.lower():
                    ext = ".jpg"
                elif "png" in url.lower():
                    ext = ".png"
                filename = f"{idx:03d}_{TARGET_PROFILE}{ext}"
                out_path = download_root / filename
                r = sess.get(url, stream=True, timeout=20)
                if r.status_code == 200:
                    with open(out_path, "wb") as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                    print(f"[{idx}] downloaded -> {out_path.name}")
                else:
                    print(
                        f"[{idx}] failed to download (status {r.status_code}): {url}")
            except Exception as e:
                print(f"[{idx}] error downloading {url}: {e}")

    print("\nDone.")

finally:
    time.sleep(2)
    driver.quit()
