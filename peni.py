import base64
import random
import requests
from seleniumbase import SB

# --- GEO + USER DATA ---------------------------------------------------------

def fetch_geo():
    info = requests.get("http://ip-api.com/json/").json()
    return (
        info.get("lat"),
        info.get("lon"),
        info.get("timezone"),
        info.get("countryCode", "").lower()
    )

lat, lon, tz_id, lang = fetch_geo()

encoded_user = "YnJ1dGFsbGVz"
decoded_user = base64.b64decode(encoded_user).decode("utf-8")

twitch_url = f"https://www.twitch.tv/{decoded_user}"
youtube_url = f"https://www.youtube.com/@{decoded_user}/live"

# --- HELPERS -----------------------------------------------------------------

def click_if_exists(driver, selector, wait=4):
    if driver.cdp.is_element_present(selector):
        driver.cdp.click(selector, timeout=wait)
        return True
    return False

def prepare_driver(main_driver, target_url):
    d = main_driver.get_new_driver(undetectable=True)
    d.activate_cdp_mode(target_url, tzone=tz_id, geoloc=(lat, lon))
    d.sleep(10)
    click_if_exists(d, 'button:contains("Start Watching")')
    click_if_exists(d, 'button:contains("Accept")')
    return d

# --- MAIN LOOP ---------------------------------------------------------------

while True:
    with SB(
        uc=True,
        locale="en",
        ad_block=True,
        chromium_arg="--disable-webgl"
    ) as session:

        delay = random.randint(450, 900)

        session.activate_cdp_mode(
            twitch_url,
            tzone=tz_id,
            geoloc=(lat, lon)
        )

        session.sleep(10)

        click_if_exists(session, 'button:contains("Start Watching")')
        click_if_exists(session, 'button:contains("Accept")')

        # Check if stream is live
        if session.cdp.is_element_present("#live-channel-stream-information"):

            click_if_exists(session, 'button:contains("Accept")')

            # Open Twitch in second driver
            tw_driver = prepare_driver(session, twitch_url)
            session.sleep(10)

            # Open YouTube in third driver
            yt_driver = session.get_new_driver(undetectable=True)
            yt_driver.activate_cdp_mode(youtube_url, tzone=tz_id, geoloc=(lat, lon))
            yt_driver.sleep(10)

            if not click_if_exists(yt_driver, 'button:contains("Accept")'):
                yt_driver.sleep(10)
                yt_driver.cdp.gui_press_key("K")

            session.sleep(delay)
            session.quit_extra_driver()

        else:
            break
