import logging, random, string, pytz, aiohttp
from datetime import date
from config import SHORTLINK_API, SHORTLINK_URL
from shortzy import Shortzy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# In-memory storage for tokens & verifications
TOKENS = {}    # {user_id: {token: is_used}}
VERIFIED = {}  # {user_id: last_verified_date}

# 🔗 Generate shortlink for verify URL
async def get_verify_shorted_link(link):
    if SHORTLINK_URL == "api.shareus.io":
        url = f'https://{SHORTLINK_URL}/easy_api'
        params = {
            "key": SHORTLINK_API,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return link
    else:
        shortzy = Shortzy(api_key=SHORTLINK_API, base_site=SHORTLINK_URL)
        short_link = await shortzy.convert(link)
        return short_link

# ✅ Generate verification token + shortlink
async def get_token(bot, userid, base_link):
    user = await bot.get_users(userid)
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    
    # store token as unused
    if user.id not in TOKENS:
        TOKENS[user.id] = {}
    TOKENS[user.id][token] = False

    # build and shorten verify link
    full_link = f"{base_link}verify-{user.id}-{token}"
    short_link = await get_verify_shorted_link(full_link)
    return short_link

# 🔍 Check if token is valid and not used
async def check_token(bot, userid, token):
    user = await bot.get_users(userid)
    user_tokens = TOKENS.get(user.id, {})
    is_used = user_tokens.get(token)
    
    if is_used is None:
        return False  # token not found
    return not is_used  # True if unused, False if already used

# ☑️ Mark token as used
async def verify_user(bot, userid, token):
    user = await bot.get_users(userid)

    if user.id in TOKENS and token in TOKENS[user.id]:
        TOKENS[user.id][token] = True

    # store verified date (not required now, but useful for logs or extra rules)
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    VERIFIED[user.id] = str(today)

# ❓ Optional: Check if user already verified today
async def check_verification(bot, userid):
    user = await bot.get_users(userid)
    today = date.today()
    
    if user.id in VERIFIED:
        y, m, d = VERIFIED[user.id].split("-")
        verified_date = date(int(y), int(m), int(d))
        return verified_date == today
    return False
