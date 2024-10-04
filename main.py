from playwright.sync_api import sync_playwright
import time
import json
from loguru import logger


class SuiMiner:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.accounts = self.load_addresses()

    def load_addresses(self):
        with open('account.json', 'r') as f:
            accounts = json.load(f)
            return accounts

    def save_addresses(self, account):
        if self.data_dir in self.accounts:
            logger.info('地址已存在')
            return

        self.accounts[self.data_dir] = account
        with open('account.json', 'w') as f:
            json.dump(self.accounts, f, indent=2)

    def run(self):
        with sync_playwright() as p:
            # Use launch_persistent_context and pass user_data_dir as the first argument
            context = p.chromium.launch_persistent_context(
                self.data_dir,
                headless=False,
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            page.goto("https://suimine.xyz/#/tokens/fomo")

            try:
                page.wait_for_selector("//button[contains(text(),'Get Started: Create Your Address')]", timeout=3000)
                page.click("//button[contains(text(),'Get Started: Create Your Address')]")

                page.wait_for_selector("//button[contains(text(),'Generate')]")
                page.click("//button[contains(text(),'Generate')]")

                page.wait_for_selector("//button[contains(text(),'Save')]")
                page.click("//button[contains(text(),'Save')]")
            except Exception as e:
                logger.info("地址已创建")

            # Get address
            page.click('//*[@id="root"]/html/body/div/header/div/div[2]/div/div/button[1]')
            page.wait_for_selector('input')

            address = page.evaluate('document.querySelector("input[type=text]").value')

            page.click("//button[contains(text(),'Close')]")

            private_key = page.evaluate("localStorage.getItem('local_private_key')")
            logger.info(f'address: {address}')
            logger.info(f'private_key: {private_key}')

            self.save_addresses(f'{address}:{private_key}')

            while True:
                try:
                    button = page.locator("//button[contains(text(),'Mine with Web GPU')]")
                    if button.is_enabled():
                        logger.info('click start button')
                        button.click()
                    elif page.query_selector_all("div.text-red-500"):
                        page.reload()
                        time.sleep(3)

                    try:
                        button = page.get_by_text("Stop Mine with Web GPU")
                        if button.is_enabled():
                            logger.info("miner is started.")
                    except Exception as e:
                        logger.info(e)
                        page.reload()

                    time.sleep(1)

                except Exception:
                    logger.info("miner is started.")
                    time.sleep(10)


if __name__ == "__main__":
    import sys

    data_dir = f'chrome_data_{sys.argv[1]}'
    miner = SuiMiner(data_dir)
    miner.run()
