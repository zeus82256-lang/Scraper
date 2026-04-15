import os
import json
import time
import threading
import requests
import re
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin


# ==========================================
# إعدادات التطبيق
# ==========================================
app = Flask(__name__)
CORS(app)

# مفتاح سري لحماية الرابط
API_SECRET = os.environ.get('API_SECRET', 'Zeusndndjddnejdjdjdejekk29393838msmskxcm9239484jdndjdnddjj99292938338zeuslojdnejxxmejj82283849')

# رابط الخادم الرئيسي (Node.js)
NODE_BACKEND_URL = os.environ.get('NODE_BACKEND_URL', 'https://c-production-89da.up.railway.app')

# ==========================================
# 🍪 إعدادات الكوكيز (تجاوز حماية تسجيل الدخول)
# ==========================================
# تم تحديث الكوكيز بناءً على طلبك لمركز الروايات
MARKAZ_COOKIES = 'wordpress_sec_198f6e9e82ba200a53325105f201ddc5=mikey%7C1771590380%7CKJphcZkhBFCpXyLUDrDcGPi9XmNOC47IPCSEHAPyfXS%7C5e8e596c5389b65f91a30668be6f16c7134b98b3ae55a007ed360594dd035527; cf_clearance=qYXkJIaj1IiaBKgi561_IQ.9oWgJ3fx10itfVR20lXY-1765278736-1.2.1.1-soYoRwUhDSq_.2cCoaJ22MPadmCmaQ0cW3AkfA1L97BJIbxQQro5hvpmuJxhQaT57TxfEW10l9gQYsmy5QgrwLsiWHScUWVvqYzZufRRYs9LIDPAhyxiOnL2Byevi12fb8iAZWttVNlqYWeKjH06tTp8bNhPx4dsmudPpIh0qzijEZhRk8lK6nWip1SeDFO2Of35W2rBKDEtjidGFyIj1RU3B7Xt.4CVoQbE9pGFaS8gFTMOp.0qmMMiz1UmHoFc; wpmanga-body-contrast=light; wpmanga-reading-history=W3siaWQiOjEyODE3LCJjIjoiMzEzMDgiLCJwIjoxLCJpIjoiIiwidCI6MTc2ODEwMTY3MH1d; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2026-02-06%2012%3A25%3A57%7C%7C%7Cep%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fwww.bing.com%2F; sbjs_first_add=fd%3D2026-02-06%2012%3A25%3A57%7C%7C%7Cep%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fwww.bing.com%2F; sbjs_current=typ%3Dreferral%7C%7C%7Csrc%3Dbing.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_first=typ%3Dreferral%7C%7C%7Csrc%3Dbing.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_udata=vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%206.2%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F109.0.0.0%20Safari%2F537.36%20Edg%2F109.0.1518.140; wordpress_test_cookie=WP%20Cookie%20check; _lscache_vary=8d8d3777c370b0211addc5b0a9411cd9; wordpress_logged_in_198f6e9e82ba200a53325105f201ddc5=mikey%7C1771590380%7CKJphcZkhBFCpXyLUDrDcGPi9XmNOC47IPCSEHAPyfXS%7Cb7d906dce3f0b160d5c2f585bfec331fe7d0cc3e4640a74945cc619df837e5c9; sbjs_session=pgs%3D2%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%3Fnsl_bypass_cache%3D74d71305203b9ce18787813c87e33f8c'

# ==========================================
# 🔄 GLOBAL SERVER-SIDE SCHEDULER STATE
# ==========================================
SCHEDULER_CONFIG = {
    'active': False,
    'interval_seconds': 86400, # Default 24h
    'next_run': 0,
    'last_run': 0,
    'status': 'idle',
    'admin_email': 'system@auto'
}

# ==========================================
# أدوات السحب المشتركة (Shared Scraper Tools)
# ==========================================

def get_headers(referer=None, use_cookies=False):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
    }
    if referer:
        headers['Referer'] = referer
    
    if use_cookies and MARKAZ_COOKIES and MARKAZ_COOKIES != 'ضع_هنا_الكوكيز_الخاصة_بك_كاملة':
        headers['Cookie'] = MARKAZ_COOKIES
        
    return headers

def fix_image_url(url, base_url='https://api.rewayat.club'):
    if not url: return ""
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        # Fix for absolute paths without domain
        if 'novelfire.net' in base_url:
            return 'https://novelfire.net' + url
        elif 'wuxiabox.com' in base_url or 'wuxiaspot.com' in base_url:
             parsed = urlparse(base_url)
             domain = f"{parsed.scheme}://{parsed.netloc}"
             return domain + url
        return base_url + url
    elif not url.startswith('http'):
        return base_url + '/' + url
    return url

def parse_relative_date(date_str):
    """تحويل التواريخ النسبية (منذ 5 ساعات، يومين ago) إلى تاريخ حقيقي"""
    try:
        if not date_str: return None
        
        now = datetime.now()
        text = str(date_str).lower().strip()
        
        # معالجة النصوص العربية الخاصة (يومين، ساعتين، إلخ)
        if 'يومين' in text:
            return (now - timedelta(days=2)).isoformat()
        if 'ساعتين' in text:
            return (now - timedelta(hours=2)).isoformat()
        if 'دقيقتين' in text:
            return (now - timedelta(minutes=2)).isoformat()
        if 'أمس' in text or 'امس' in text:
            return (now - timedelta(days=1)).isoformat()
        
        # إزالة كلمات زائدة
        text = text.replace('updated', '').replace('ago', '').replace('منذ', '').strip()
        
        # استخراج الرقم والوحدة (عربي وإنجليزي)
        # Match number followed by optional whitespace and unit
        match = re.search(r'(\d+)\s*(sec|min|hour|day|week|month|year|ثانية|ثواني|دقيقة|دقائق|ساعة|ساعات|يوم|أيام|ايام|أسبوع|اسبوع|أسابيع|اسابيع|شهر|أشهر|اشهر|سنة|سنوات)', text)
        
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            delta = timedelta(seconds=0)
            
            # English Units
            if 'sec' in unit: delta = timedelta(seconds=amount)
            elif 'min' in unit: delta = timedelta(minutes=amount)
            elif 'hour' in unit: delta = timedelta(hours=amount)
            elif 'day' in unit: delta = timedelta(days=amount)
            elif 'week' in unit: delta = timedelta(weeks=amount)
            elif 'month' in unit: delta = timedelta(days=amount * 30)
            elif 'year' in unit: delta = timedelta(days=amount * 365)
            
            # Arabic Units
            elif 'ثان' in unit: delta = timedelta(seconds=amount)
            elif 'دقيق' in unit: delta = timedelta(minutes=amount)
            elif 'ساع' in unit: delta = timedelta(hours=amount)
            elif 'يوم' in unit or 'أيام' in unit or 'ايام' in unit: delta = timedelta(days=amount)
            elif 'أسبوع' in unit or 'اسبوع' in unit or 'أسابيع' in unit: delta = timedelta(weeks=amount)
            elif 'شهر' in unit or 'أشهر' in unit: delta = timedelta(days=amount * 30)
            elif 'سنة' in unit or 'سنوات' in unit: delta = timedelta(days=amount * 365)
            
            return (now - delta).isoformat()
            
        # محاولة قراءة تاريخ ثابت (May 20, 2024 / 2025/12/15)
        try:
            # Try MM/DD/YYYY or similar common formats
            for fmt in ['%B %d, %Y', '%Y/%m/%d', '%d/%m/%Y', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(text, fmt)
                    return dt.isoformat()
                except: continue
        except:
            pass
            
        return None # Return None if we can't parse it
    except:
        return None

def send_data_to_backend(payload):
    """إرسال البيانات إلى الخادم الرئيسي"""
    try:
        endpoint = f"{NODE_BACKEND_URL}/api/scraper/receive"
        headers = { 'Content-Type': 'application/json', 'Authorization': API_SECRET, 'x-api-secret': API_SECRET }
        response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to send data: {e}")
        return False

def check_existing_chapters(title):
    """التحقق من الفصول الموجودة في الباك إند لمنع التكرار"""
    try:
        endpoint = f"{NODE_BACKEND_URL}/api/scraper/check-chapters"
        headers = { 'Content-Type': 'application/json', 'Authorization': API_SECRET, 'x-api-secret': API_SECRET }
        response = requests.post(endpoint, json={'title': title}, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('exists'):
                return data['chapters']
            else:
                return []
        return []
    except Exception as e:
        print(f"❌ Error checking existence: {e}")
        return []

# ==========================================
# 🟣 1. Rewayat Club (Nuxt) Logic
# ==========================================

def extract_from_nuxt(soup):
    try:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'window.__NUXT__' in script.string:
                content = script.string
                # Extract poster
                match = re.search(r'poster_url:"(.*?)"', content)
                if not match: match = re.search(r'poster:"(.*?)"', content)
                if match:
                    raw_url = match.group(1)
                    return raw_url.encode('utf-8').decode('unicode_escape')
    except: pass
    return None

def fetch_metadata_rewayat(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
        
        cover_url = extract_from_nuxt(soup) or ""
        if not cover_url:
            og_image = soup.find("meta", property="og:image")
            if og_image: cover_url = og_image["content"]
        cover_url = fix_image_url(cover_url)

        desc_div = soup.find(class_='text-pre-line') or soup.find('div', class_='v-card__text')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""
        
        # 🔥🔥 STATUS CHECK - REWAYAT CLUB SPECIFIC 🔥🔥
        status = "مستمرة"
        # 1. Check for specific status badges in Vuetify chips
        chips = soup.find_all(class_='v-chip__content')
        for chip in chips:
            txt = chip.get_text(strip=True)
            if "مكتملة" in txt or "Completed" in txt:
                status = "مكتملة"
                break
        
        # 2. Fallback: Search in full text if not found
        if status == "مستمرة":
            if "مكتملة" in soup.get_text():
                status = "مكتملة"

        # 🔥 EXTRACT REAL LAST UPDATE DATE (NUXT/Vue Logic) 🔥
        last_update = None
        
        # Try finding date pattern YYYY/MM/DD in list items text content directly
        # Example from provided HTML: 2025/12/16 inside v-list-item__subtitle
        # We look for date patterns anywhere in the HTML body text to be safe or specific elements
        
        # Method 1: Regex search in subtitles
        subtitles = soup.find_all(class_='v-list-item__subtitle')
        for sub in subtitles:
            txt = sub.get_text(strip=True)
            # Match date YYYY/MM/DD
            date_match = re.search(r'(\d{4}/\d{1,2}/\d{1,2})', txt)
            if date_match:
                last_update = parse_relative_date(date_match.group(1))
                if last_update: break 
        
        # Do NOT default to now. If None, it means we couldn't find a new date.
        
        return {
            'title': title, 'description': description, 'cover': cover_url,
            'status': status, 'category': "عام", 'tags': [], 'sourceUrl': url,
            'lastUpdate': last_update
        }
    except Exception as e:
        print(f"Error rewayat metadata: {e}")
        return None

def scrape_chapter_rewayat(novel_url, chapter_num):
    url = f"{novel_url.rstrip('/')}/{chapter_num}"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code != 200: return None, None
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        clean_paragraphs = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        if clean_paragraphs:
            text = "\n\n".join(clean_paragraphs)
        else:
            div = soup.find('div', class_='pre-formatted') or soup.find('div', class_='v-card__text')
            text = div.get_text(separator="\n\n", strip=True) if div else ""
        
        if len(text.strip()) < 2: return None, None
        
        title_tag = soup.find(class_='v-card__subtitle') or soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else f"الفصل {chapter_num}"
        title = re.sub(r'^\d+\s*-\s*', '', title)
        return title, text
    except: return None, None

def worker_rewayat_probe(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    # Send initial meta update
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    current_chapter = 1
    errors = 0
    batch = []
    
    while current_chapter < 5000 and errors < 15:
        if current_chapter in existing_chapters:
            current_chapter += 1
            errors = 0
            continue
            
        chap_title, content = scrape_chapter_rewayat(url, current_chapter)
        if content:
            errors = 0
            batch.append({'number': current_chapter, 'title': chap_title, 'content': content})
            print(f"Fetched Ch {current_chapter}")
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
        else:
            errors += 1
            print(f"Failed Ch {current_chapter} ({errors}/15)")
        current_chapter += 1
        
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})

# ==========================================
# 🟢 2. Madara Themes (Ar-Novel & Markaz Riwayat - Updated for NEW DESIGN)
# ==========================================

def get_base_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def clean_madara_title(raw_title):
    cleaned = re.sub(r'^\s*(?:Chapter|الفصل|فصل)?\s*\d+\s*[:\-–]\s*', '', raw_title, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else raw_title 

def fetch_metadata_madara(url):
    try:
        use_cookies = 'markazriwayat.com' in url
        response = requests.get(url, headers=get_headers(use_cookies=use_cookies), timeout=15)
        
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # --- Check for NEW Markaz Riwayat Design (Theam App) ---
        is_new_design = bool(soup.select_one('.manga-title'))
        
        if is_new_design:
            # 1. Title
            title_tag = soup.select_one('h1.manga-title')
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            # 2. Cover
            cover = ""
            img_tag = soup.select_one('.manga-cover-wrap img')
            if img_tag:
                cover = img_tag.get('data-src') or img_tag.get('src')
            cover = fix_image_url(cover)
            
            # 3. Description
            desc_div = soup.find('div', id='manga-summary')
            if desc_div:
                description = desc_div.get_text(separator="\n\n", strip=True)
            else:
                description = ""
            
            # 4. Status
            status = "مستمرة"
            status_pill = soup.select_one('.manga-status-pill')
            if status_pill:
                txt = status_pill.get_text(strip=True)
                if "مكتملة" in txt or "Completed" in txt:
                    status = "مكتملة"
            
            # 5. Categories (Tags)
            tags = []
            pill_links = soup.select('.pill-list .pill')
            for pill in pill_links:
                tags.append(pill.get_text(strip=True))
            category = tags[0] if tags else "عام"
            
            # 6. Novel ID
            novel_id = None
            # Try to get from buttons or data attributes
            like_btn = soup.select_one('.manga-like-btn')
            if like_btn and like_btn.has_attr('data-manga-id'):
                novel_id = like_btn['data-manga-id']
            if not novel_id:
                rating_btn = soup.select_one('.manga-stat--rating')
                if rating_btn and rating_btn.has_attr('data-manga-id'):
                    novel_id = rating_btn['data-manga-id']
            
            # 7. Last Update (from latest chapter in list)
            last_update = None
            first_ch_row = soup.select_one('.ch-list .ch-row .ch-date')
            if first_ch_row:
                last_update = parse_relative_date(first_ch_row.get_text(strip=True))

        else:
            # --- OLD Standard Madara Design ---
            title_tag = soup.find(class_='post-title')
            title = title_tag.find('h1').get_text(strip=True) if title_tag else "Unknown"
            title = re.sub(r'\s*~.*$', '', title) 

            cover = ""
            og_img = soup.find("meta", property="og:image")
            if og_img: cover = og_img["content"]
            if not cover:
                img_container = soup.find(class_='summary_image')
                if img_container:
                    img_tag = img_container.find('img')
                    if img_tag:
                        cover = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('srcset', '').split(' ')[0]
            cover = fix_image_url(cover)

            novel_id = None
            shortlink = soup.find("link", rel="shortlink")
            if shortlink:
                match = re.search(r'p=(\d+)', shortlink.get('href', ''))
                if match: novel_id = match.group(1)
            if not novel_id:
                id_input = soup.find('input', class_='rating-post-id')
                if id_input: novel_id = id_input.get('value')
            if not novel_id:
                body_tag = soup.find('body')
                if body_tag and body_tag.has_attr('class'):
                    for c in body_tag.get('class', []):
                        if c.startswith('manga-id-'):
                            novel_id = c.replace('manga-id-', '')

            desc_div = soup.find(class_='summary__content') or soup.find(class_='description-summary')
            description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""
            description = re.sub(r'\n{3,}', '\n\n', description)

            genres_content = soup.find(class_='genres-content')
            category = "عام"
            tags = []
            if genres_content:
                links = genres_content.find_all('a')
                tags = [a.get_text(strip=True) for a in links]
                if tags: category = tags[0]

            status = "مستمرة"
            status_terms = soup.find_all('div', class_='post-status')
            if status_terms:
                for st in status_terms:
                    txt = st.get_text(strip=True).lower()
                    if 'completed' in txt or 'مكتملة' in txt:
                        status = "مكتملة"
                        break
            
            last_update = None
            timediff_span = soup.select_one('.post-on .timediff')
            if timediff_span:
                raw_date = timediff_span.get_text(strip=True)
                last_update = parse_relative_date(raw_date)
            if not last_update:
                update_node = soup.select_one('.post-on span') or soup.select_one('.post-on')
                if update_node:
                    raw_date = update_node.get_text(strip=True)
                    last_update = parse_relative_date(raw_date)

        print(f"Found Novel ID: {novel_id}")

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'novel_id': novel_id, 'sourceUrl': url,
            'lastUpdate': last_update
        }
    except Exception as e:
        print(f"Error Madara Meta: {e}")
        return None

def fetch_metadata_markaz(url):
    return fetch_metadata_madara(url)

def parse_madara_chapters_from_html(soup):
    chapters = []
    
    # 1. Try NEW Design Selector (.ch-list .ch-row)
    new_rows = soup.select('.ch-list .ch-row')
    if new_rows:
        for row in new_rows:
            # Link is usually the anchor tag wrapping or inside the row
            a = row.find('a')
            if not a: continue
            
            link = a.get('href')
            
            # Extract Number from .ch-num
            num_div = row.select_one('.ch-num')
            number = 0
            if num_div:
                try:
                    number = int(num_div.get_text(strip=True))
                except: pass
            
            # If number not found in div, try from link or title
            if number == 0:
                num_match = re.search(r'(\d+)', link)
                if num_match: number = int(num_match.group(1))

            # Extract Title from .ch-title
            title_div = row.select_one('.ch-title')
            raw_title = title_div.get_text(strip=True) if title_div else f"Chapter {number}"
            clean_title = clean_madara_title(raw_title)

            if number > 0:
                chapters.append({'number': number, 'url': link, 'title': clean_title})
        
        return chapters

    # 2. Try OLD Design Selector (li.wp-manga-chapter)
    items = soup.find_all('li', class_='wp-manga-chapter')
    if items:
        for item in items:
            a = item.find('a')
            if a:
                link = a.get('href')
                raw_title = a.get_text(strip=True)
                num_match = re.search(r'(\d+)', raw_title)
                number = int(num_match.group(1)) if num_match else 0
                clean_title = clean_madara_title(raw_title)
                if number > 0:
                    chapters.append({'number': number, 'url': link, 'title': clean_title})
        return chapters

    return chapters

def fetch_chapter_list_madara(novel_id, novel_url):
    chapters = []
    base_url = get_base_url(novel_url)
    use_cookies = 'markazriwayat.com' in novel_url
    
    # Try getting chapters from the loaded page HTML first (if provided in variable, but here we fetch fresh)
    # Some new designs load chapters directly in the HTML without AJAX if they are few, 
    # but mostly they use AJAX or Load More.
    
    # 1. Try Standard Madara AJAX
    if novel_url:
        ajax_endpoint = f"{novel_url.rstrip('/')}/ajax/chapters/"
        try:
            headers = get_headers(use_cookies=use_cookies)
            headers['X-Requested-With'] = 'XMLHttpRequest'
            res = requests.post(ajax_endpoint, headers=headers, timeout=20)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                chapters = parse_madara_chapters_from_html(soup)
                print(f"✅ Chapters fetched via /ajax/chapters/ ({len(chapters)})")
        except Exception as e:
            print(f"AJAX endpoint failed: {e}")

    # 2. Try Admin AJAX (Fallback)
    if not chapters and novel_id:
        try:
            admin_ajax_url = f"{base_url}/wp-admin/admin-ajax.php"
            data = {'action': 'manga_get_chapters', 'manga': novel_id}
            res = requests.post(admin_ajax_url, data=data, headers=get_headers(novel_url, use_cookies=use_cookies), timeout=20)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                chapters = parse_madara_chapters_from_html(soup)
                print(f"✅ Chapters fetched via admin-ajax ({len(chapters)})")
        except Exception as e:
            print(f"admin-ajax failed: {e}")
    
    # 3. Try parsing the novel page directly (If the new design puts chapters in the DOM)
    if not chapters and novel_url:
        try:
            res = requests.get(novel_url, headers=get_headers(use_cookies=use_cookies), timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                chapters = parse_madara_chapters_from_html(soup)
                print(f"✅ Chapters fetched via direct HTML ({len(chapters)})")
        except Exception as e:
            print(f"Direct HTML fetch failed: {e}")

    if chapters:
        chapters.sort(key=lambda x: x['number'])
    
    return chapters

def scrape_chapter_madara(url):
    try:
        use_cookies = 'markazriwayat.com' in url
        res = requests.get(url, headers=get_headers(use_cookies=use_cookies), timeout=15)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # Selectors: Old Madara + New Markaz (.reading-content with .text-right)
        container = soup.find(class_='reader-target') or \
                    soup.find(class_='reading-content') or \
                    soup.find(class_='text-left') or \
                    soup.find(class_='text-right') or \
                    soup.find(class_='entry-content')
            
        if container:
            # Check if there is a nested .text-right inside .reading-content (New Design)
            inner_text_right = container.find(class_='text-right')
            if inner_text_right:
                container = inner_text_right

            for bad in container.find_all(['div', 'script', 'style', 'input', 'ins', 'iframe', 'button']):
                # Clean specific classes
                if bad.get('class') and any(c in ['nav-links', 'code-block', 'adsbygoogle', 'pf-ad', 'wpmcr-under-title-row'] for c in bad.get('class')):
                    bad.decompose()
                if bad.get('id') == 'reader-btn':
                    bad.decompose()
            
            for nav in container.find_all('div', class_='nav-links'):
                nav.decompose()

            text = container.get_text(separator="\n\n", strip=True)
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.replace('اكمال القراءة', '')
            text = text.replace('إعدادات القراءة', '') 
            
            if len(text) < 200 and 'سجل' in text:
                print("⚠️ Warning: Chapter content seems blocked by login wall.")
                
            return text
        return None
    except: return None

def worker_madara_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_madara(metadata.get('novel_id'), url)
    
    if not all_chapters:
        print(f"No chapters found for {metadata['title']}")
        return

    print(f"Processing {len(all_chapters)} chapters.")
    
    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue
            
        print(f"Scraping {metadata['title']} - Ch {chap['number']}...")
        content = scrape_chapter_madara(chap['url'])
        
        if content:
            batch.append({
                'number': chap['number'],
                'title': chap['title'],
                'content': content
            })
            
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1.5)
        
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})

# ==========================================
# 🟠 3. Novel Fire (novelfire.net) Logic
# ==========================================

def fetch_metadata_novelfire(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Update: Use dedicated classes if possible based on new HTML
        title_tag = soup.select_one('h1.novel-title')
        if not title_tag:
            # Fallback to OG
            meta_title = soup.find("meta", property="og:title")
            title = meta_title["content"] if meta_title else "Unknown Title"
        else:
            title = title_tag.get_text(strip=True)
            
        title = title.replace(' - Novel Fire', '').strip()

        # Cover (Updated selector)
        cover = ""
        img_tag = soup.select_one('figure.cover img')
        if img_tag:
            cover = img_tag.get('src')
        
        if not cover:
            og_img = soup.find("meta", property="og:image")
            if og_img: cover = og_img["content"]
            
        cover = fix_image_url(cover, base_url='https://novelfire.net')

        # Description (Updated selector for .summary .content)
        desc_div = soup.select_one('.summary .content')
        if not desc_div:
            desc_div = soup.find('div', class_='description') or soup.find('div', id='novel-summary')
            
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""

        tags = []
        # Updated genre selector
        genre_links = soup.select('.categories ul li a')
        if not genre_links:
            genre_links = soup.select('.novel-genres a')
            
        for link in genre_links:
            tags.append(link.get_text(strip=True))
        category = tags[0] if tags else "عام"

        # 🔥🔥 STATUS CHECK - NOVEL FIRE SPECIFIC 🔥🔥
        status = "مستمرة"
        completed_tag = soup.find('strong', class_='completed')
        if completed_tag and 'Completed' in completed_tag.get_text(strip=True):
            status = "مكتملة"

        # 🔥 Extract Last Update Time
        last_update = datetime.now().isoformat()
        update_node = soup.select_one('.chapter-latest-container .update')
        if update_node:
            pd = parse_relative_date(update_node.get_text(strip=True))
            if pd: last_update = pd

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags, 'sourceUrl': url,
            'lastUpdate': last_update
        }
    except Exception as e:
        print(f"Error NovelFire Meta: {e}")
        return None

def fetch_chapter_list_novelfire(novel_url):
    """سحب جميع الفصول من NovelFire مع دعم التنقل بين الصفحات (Pagination)"""
    chapters = []
    # التأكد من الذهاب لصفحة الفصول
    if not novel_url.rstrip('/').endswith('/chapters'):
        list_url = novel_url.rstrip('/') + '/chapters'
    else:
        list_url = novel_url

    try:
        # البدء من الصفحة الأولى
        current_page = 1
        
        while True:
            # تكوين رابط الصفحة الحالية
            page_url = f"{list_url}?page={current_page}"
            print(f"🔍 Fetching chapters from NovelFire Page: {current_page}")
            
            res = requests.get(page_url, headers=get_headers(), timeout=15)
            if res.status_code != 200: break
            
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # استخراج الفصول من الصفحة الحالية
            items = soup.select('ul.chapter-list li')
            if not items:
                break # لا توجد فصول، توقف
                
            for item in items:
                a = item.find('a')
                if a:
                    href = a.get('href', '')
                    link = 'https://novelfire.net' + href if href.startswith('/') else href
                    raw_title = a.get_text(strip=True)
                    
                    # استخراج رقم الفصل من الرابط أو العنوان
                    num_match = re.search(r'chapter-(\d+)', link)
                    if not num_match: num_match = re.search(r'(\d+)', raw_title)
                    
                    number = int(num_match.group(1)) if num_match else 0
                    if number > 0:
                        chapters.append({'number': number, 'url': link, 'title': raw_title})
            
            # التحقق مما إذا كانت هناك صفحة تالية (Next)
            # نبحث عن زر Next في Pagination
            next_btn = soup.select_one('li.page-item a[rel="next"]')
            if next_btn:
                current_page += 1
                time.sleep(0.5) # تأخير بسيط لتجنب الضغط على السيرفر
            else:
                break # لا توجد صفحة تالية، انتهينا

        # ترتيب جميع الفصول المجمعة من كل الصفحات
        chapters.sort(key=lambda x: x['number'])
        print(f"✅ Total chapters found across all pages: {len(chapters)}")
        return chapters
    except Exception as e:
        print(f"Error list NovelFire with pagination: {e}")
        return []

def scrape_chapter_novelfire(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=15)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.content, 'html.parser')
        
        container = soup.find('div', id='content') or soup.find('div', class_='chapter-content')
        if container:
            for bad in container.find_all(['div', 'script', 'style', 'ins', 'button']):
                if bad.get('class') and ('ads' in str(bad.get('class'))):
                    bad.decompose()

            text = container.get_text(separator="\n\n", strip=True)
            text = re.sub(r'Read.*online.*now!', '', text)
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text
        return None
    except: return None

def worker_novelfire_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    # Always update metadata to sync status (Completed), sourceUrl AND lastUpdate
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_novelfire(url)
    if not all_chapters:
        print(f"No chapters found for {metadata['title']}")
        return

    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue
            
        print(f"Scraping NovelFire: Ch {chap['number']}...")
        content = scrape_chapter_novelfire(chap['url'])
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
        
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})

# ==========================================
# 🔵 4. WuxiaBox / WuxiaSpot Logic
# ==========================================

def fetch_metadata_wuxiabox(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Title
        title_tag = soup.select_one('h1.novel-title')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"
        
        # Cover
        cover = ""
        img_tag = soup.select_one('figure.cover img')
        if img_tag:
            cover = img_tag.get('data-src') or img_tag.get('src')
        
        # Domain parsing for base url
        parsed_uri = urlparse(url)
        base_url = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        cover = fix_image_url(cover, base_url=base_url)

        # Description
        desc_div = soup.select_one('.summary .content') or soup.select_one('.description')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""

        # Tags & Category
        tags = []
        tags_container = soup.select('.tags a.tag')
        for t in tags_container:
            tags.append(t.get_text(strip=True))
        
        category = "عام"
        cat_tag = soup.select_one('.categories a')
        if cat_tag:
            category = cat_tag.get_text(strip=True)

        status_tag = soup.select_one('.header-stats strong')
        status = "مستمرة"
        if status_tag:
            txt = status_tag.get_text(strip=True).lower()
            if 'completed' in txt: status = "مكتملة"

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'base_url': base_url, 'sourceUrl': url,
            'lastUpdate': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error WuxiaBox Meta: {e}")
        return None

def fetch_chapter_list_wuxiabox(url, metadata):
    chapters = []
    base_url = metadata.get('base_url', 'https://wuxiabox.com')
    
    try:
        current_url = url
        
        while True:
            print(f"🔍 Fetching chapters from WuxiaBox: {current_url}")
            response = requests.get(current_url, headers=get_headers(), timeout=15)
            if response.status_code != 200: break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract chapters
            chapter_list = soup.select('ul.chapter-list li a')
            if not chapter_list:
                # Sometimes list is dynamic, but usually on these sites it's paginated
                break
                
            for a in chapter_list:
                href = a.get('href')
                full_link = urljoin(base_url, href)
                title = a.get('title') or a.get_text(strip=True)
                
                # Extract number
                # Often format is "Chapter 123 title" or just "Chapter 123"
                # Using regex to find the first integer in the text
                num_match = re.search(r'Chapter\s+(\d+)', title, re.IGNORECASE)
                if not num_match:
                    num_match = re.search(r'(\d+)', title)
                
                if num_match:
                    number = int(num_match.group(1))
                    chapters.append({'number': number, 'url': full_link, 'title': title})
            
            # Find Next Page
            # The pagination is usually in ul.pagination
            next_btn = None
            pagination_links = soup.select('ul.pagination li a')
            for link in pagination_links:
                if '>' in link.get_text() or 'Next' in link.get_text():
                    next_btn = link
                    break
                # Sometimes it is just the last link if not numbered
                
            if next_btn:
                next_href = next_btn.get('href')
                current_url = urljoin(base_url, next_href)
                time.sleep(0.5)
            else:
                break
        
        # Remove duplicates based on number
        unique_chapters = {c['number']: c for c in chapters}.values()
        chapters = list(unique_chapters)
        chapters.sort(key=lambda x: x['number'])
        
        return chapters

    except Exception as e:
        print(f"Error WuxiaBox List: {e}")
        return []

def scrape_chapter_wuxiabox(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=15)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.content, 'html.parser')
        
        content_div = soup.select_one('.chapter-content')
        if not content_div: return None
        
        # Clean ads
        for script in content_div.find_all('script'):
            script.decompose()
        for div in content_div.find_all('div'):
            # Usually ads are in divs inside content
            div.decompose()
        for style in content_div.find_all('style'):
            style.decompose()
            
        text = content_div.get_text(separator="\n\n", strip=True)
        # Cleanup
        text = re.sub(r'\(End of this chapter\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    except: return None

def worker_wuxiabox_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_wuxiabox(url, metadata)
    if not all_chapters:
        print("No chapters found")
        return

    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue
            
        print(f"Scraping WuxiaBox: Ch {chap['number']}...")
        content = scrape_chapter_wuxiabox(chap['url'])
        
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
                
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})

# ==========================================
# 🔴 5. FreeWebNovel Logic
# ==========================================

def fetch_metadata_freewebnovel(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Title
        title_tag = soup.find("meta", property="og:title")
        title = title_tag["content"] if title_tag else soup.select_one('h1.tit').get_text(strip=True)
        # Remove site suffix
        title = title.split(' - ')[0].strip()

        # Cover
        cover_tag = soup.find("meta", property="og:image")
        cover = cover_tag["content"] if cover_tag else ""
        
        # Description
        desc_div = soup.select_one('.m-desc .txt .inner')
        if desc_div:
            description = desc_div.get_text(separator="\n\n", strip=True)
        else:
            desc_meta = soup.find("meta", property="og:description")
            description = desc_meta["content"] if desc_meta else ""

        # Status
        status = "مستمرة"
        status_node = soup.select_one('.m-imgtxt .item span.s3 a')
        if status_node and 'Completed' in status_node.get_text():
            status = "مكتملة"

        # Categories
        tags = []
        genre_links = soup.select('.m-imgtxt .item a[href*="genre"]')
        for link in genre_links:
            tags.append(link.get_text(strip=True))
        category = tags[0] if tags else "عام"

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags, 'sourceUrl': url,
            'lastUpdate': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error Freewebnovel Meta: {e}")
        return None

def fetch_chapter_list_freewebnovel(url):
    chapters = []
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return []
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # List items
        items = soup.select('ul#idData li a')
        for a in items:
            href = a.get('href')
            full_link = urljoin('https://freewebnovel.com', href)
            title = a.get('title') or a.get_text(strip=True)
            
            # Extract number
            match = re.search(r'Chapter\s+(\d+)', title, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                chapters.append({'number': num, 'url': full_link, 'title': title})
        
        # Deduplicate and sort
        unique = {c['number']: c for c in chapters}.values()
        chapters = list(unique)
        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"Error Freewebnovel List: {e}")
        return []

def scrape_chapter_freewebnovel(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content_div = soup.select_one('.m-read .txt')
        if not content_div: return None
        
        # Clean specific trash found in file
        for bad in content_div.find_all(['script', 'style', 'subtxt', 'div', 'center']):
            bad.decompose()
            
        # Clean text
        text = content_div.get_text(separator="\n\n", strip=True)
        # Remove common ads in text if any remain
        text = re.sub(r'Find.*novels.*at.*freewebnovel.*', '', text, flags=re.IGNORECASE)
        return text
    except: return None

def worker_freewebnovel_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_freewebnovel(url)
    
    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters: continue
        
        print(f"Scraping Freewebnovel: Ch {chap['number']}...")
        content = scrape_chapter_freewebnovel(chap['url'])
        
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
                
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})


# ==========================================
# 🟡 6. FanMTL Logic
# ==========================================

def fetch_metadata_fanmtl(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')

        # Title
        title_tag = soup.select_one('h1.novel-title')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        # Cover
        cover = ""
        img_tag = soup.select_one('figure.cover img')
        if img_tag:
            cover = img_tag.get('data-src') or img_tag.get('src')
        if not cover:
            og_img = soup.find("meta", property="og:image")
            if og_img:
                cover = og_img.get('content', '')
        cover = fix_image_url(cover, base_url='https://fanmtl.com')

        # Description
        desc_div = soup.select_one('.summary .content')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""

        # Categories + Tags
        categories = []
        for a in soup.select('.categories a.property-item'):
            txt = a.get_text(strip=True)
            if txt:
                categories.append(txt)

        tags = []
        for a in soup.select('.tags a.tag, .categories a.tag'):
            txt = a.get_text(strip=True)
            if txt:
                tags.append(txt)

        category = categories[0] if categories else (tags[0] if tags else "عام")
        all_tags = categories + [t for t in tags if t not in categories]

        # Status
        status = "مستمرة"
        for strong in soup.select('.header-stats strong'):
            txt = strong.get_text(strip=True).lower()
            if 'completed' in txt or 'complete' in txt or 'مكتملة' in txt:
                status = "مكتملة"
                break

        # Last Update
        last_update = None
        update_node = soup.select_one('ul.chapter-list li time.chapter-update')
        if update_node:
            last_update = parse_relative_date(update_node.get_text(strip=True))

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': all_tags,
            'sourceUrl': url, 'lastUpdate': last_update
        }
    except Exception as e:
        print(f"Error FanMTL Meta: {e}")
        return None

def fetch_chapter_list_fanmtl(url):
    chapters = []
    visited_pages = set()

    try:
        current_url = url

        while current_url and current_url not in visited_pages:
            visited_pages.add(current_url)
            print(f"🔍 Fetching chapters from FanMTL: {current_url}")

            response = requests.get(current_url, headers=get_headers(), timeout=15)
            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select('ul.chapter-list li a')
            if not items:
                break

            for a in items:
                href = a.get('href')
                if not href:
                    continue

                full_link = urljoin('https://fanmtl.com', href)
                raw_title = a.get('title') or a.get_text(" ", strip=True)

                chapter_no = a.select_one('.chapter-no')
                number = 0
                if chapter_no:
                    try:
                        number = int(chapter_no.get_text(strip=True))
                    except:
                        number = 0

                if number == 0:
                    num_match = re.search(r'_(\d+)\.html', full_link)
                    if not num_match:
                        num_match = re.search(r'Chapter\s+(\d+)', raw_title, re.IGNORECASE)
                    if not num_match:
                        num_match = re.search(r'(\d+)', raw_title)
                    if num_match:
                        number = int(num_match.group(1))

                title_node = a.select_one('.chapter-title')
                chapter_title = title_node.get_text(strip=True) if title_node else raw_title

                if number > 0:
                    chapters.append({'number': number, 'url': full_link, 'title': chapter_title})

            next_url = None
            pagination_links = soup.select('.pagination li a')
            for link in pagination_links:
                text = link.get_text(strip=True)
                href = link.get('href')
                if href and text == '>':
                    next_url = urljoin('https://fanmtl.com', href)
                    break

            current_url = next_url
            if current_url:
                time.sleep(0.5)

        unique_chapters = {c['number']: c for c in chapters}.values()
        chapters = list(unique_chapters)
        chapters.sort(key=lambda x: x['number'])
        print(f"✅ Total FanMTL chapters found: {len(chapters)}")
        return chapters
    except Exception as e:
        print(f"Error FanMTL List: {e}")
        return []

def scrape_chapter_fanmtl(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')

        content_div = soup.select_one('.chapter-content')
        if not content_div: return None

        for bad in content_div.find_all(['script', 'style', 'ins', 'iframe', 'button', 'div']):
            bad.decompose()

        text = content_div.get_text(separator="\n\n", strip=True)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text if text else None
    except:
        return None

def worker_fanmtl_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0

    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_fanmtl(url)
    if not all_chapters:
        print(f"No chapters found for {metadata['title']}")
        return

    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue

        print(f"Scraping FanMTL: Ch {chap['number']}...")
        content = scrape_chapter_fanmtl(chap['url'])

        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)

    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})

# ==========================================
# 🟤 7. ErCiYuan (二次元小说网) Logic (Chinese Site)
# ==========================================

def fetch_metadata_erciyuan(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.content, 'html.parser')

        # Title from h1 in info box
        title_tag = soup.select_one('div.info h1')
        if not title_tag:
            title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        # Cover image
        cover = ""
        img_tag = soup.select_one('div.imgbox img')
        if img_tag:
            cover = img_tag.get('src')
        if not cover:
            og_img = soup.find("meta", property="og:image")
            if og_img:
                cover = og_img["content"]
        # Build full URL if relative
        if cover and cover.startswith('/'):
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            cover = base + cover

        # Description
        desc_div = soup.select_one('div.desc')
        if not desc_div:
            desc_div = soup.select_one('div.m-desc')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""

        # Status and category from page text
        status = "مستمرة"  # default ongoing
        category = "عام"
        tags = []

        # Get all text in info div to extract status and category
        info_div = soup.select_one('div.info')
        if info_div:
            info_text = info_div.get_text()
            # Look for status: "状态：连载" (ongoing) or "状态：完结" (completed)
            status_match = re.search(r'状态[：:]\s*([^\s]+)', info_text)
            if status_match:
                status_text = status_match.group(1)
                if '完结' in status_text or 'مكتملة' in status_text or 'completed' in status_text.lower():
                    status = "مكتملة"
            # Look for category: "类　别：奇幻" etc.
            cat_match = re.search(r'类[：:]\s*([^\s]+)', info_text)
            if cat_match:
                category = cat_match.group(1)
            # Tags might be multiple, but we can add category as first tag
            tags = [category] if category != "عام" else []

        # Last update
        last_update = None
        update_text = None
        # Find "最后更新：" and parse date
        update_match = re.search(r'最后更新[：:]\s*(\d{4}-\d{1,2}-\d{1,2}\s*\d{1,2}:\d{1,2}:\d{1,2})', soup.get_text())
        if update_match:
            update_text = update_match.group(1)
            try:
                # Convert to ISO format
                dt = datetime.strptime(update_text, '%Y-%m-%d %H:%M:%S')
                last_update = dt.isoformat()
            except:
                pass

        return {
            'title': title,
            'description': description,
            'cover': cover,
            'status': status,
            'category': category,
            'tags': tags,
            'sourceUrl': url,
            'lastUpdate': last_update
        }
    except Exception as e:
        print(f"Error ErCiYuan metadata: {e}")
        return None

def fetch_chapter_list_erciyuan(url):
    chapters = []
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return chapters
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the chapter list (ul.section-list inside section-box)
        section_box = soup.select_one('div.section-box')
        if not section_box:
            return chapters
        chapter_items = section_box.select('ul.section-list li a')
        if not chapter_items:
            # Alternative: look for .section-list directly
            chapter_items = soup.select('ul.section-list li a')

        base_url = get_base_url(url)

        for a in chapter_items:
            href = a.get('href')
            if not href:
                continue
            full_url = urljoin(base_url, href)
            raw_title = a.get_text(strip=True)

            # Extract chapter number from Chinese format: "第1章 title"
            # Use regex to find number after "第" and before "章"
            num_match = re.search(r'第(\d+)章', raw_title)
            number = 0
            if num_match:
                number = int(num_match.group(1))
            else:
                # Fallback: try to find any number
                num_fallback = re.search(r'(\d+)', raw_title)
                if num_fallback:
                    number = int(num_fallback.group(1))

            # Clean title: remove the "第X章" part
            clean_title = re.sub(r'^第\d+章\s*', '', raw_title).strip()
            if not clean_title:
                clean_title = raw_title

            if number > 0:
                chapters.append({'number': number, 'url': full_url, 'title': clean_title})

        # Sort by number
        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"Error ErCiYuan chapter list: {e}")
        return chapters

def scrape_chapter_erciyuan(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find content div
        content_div = soup.find('div', id='content')
        if not content_div:
            content_div = soup.find('div', class_='content')

        if not content_div:
            return None

        # Remove unwanted elements
        for bad in content_div.find_all(['script', 'style', 'ins', 'iframe', 'div', 'a']):
            # Remove ads or navigation elements if they have specific classes
            if bad.get('class') and any(c in ['appguide-wrap', 'btn-addbs', 'section-opt'] for c in bad.get('class')):
                bad.decompose()
            # Also remove any element with id 'content' inside? no

        # Get text from paragraphs
        paragraphs = content_div.find_all('p')
        if paragraphs:
            text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            text = "\n\n".join(text_parts)
        else:
            # If no p tags, just get the whole text
            text = content_div.get_text(separator="\n\n", strip=True)

        # Clean common Chinese ad phrases
        text = re.sub(r'本章未完，点击下一页继续阅读', '', text)
        text = re.sub(r'请收藏本站：https?://\S+', '', text)
        text = re.sub(r'最新章节请.*', '', text, flags=re.IGNORECASE)

        return text if len(text.strip()) > 50 else None
    except Exception as e:
        print(f"Error scraping ErCiYuan chapter: {e}")
        return None

def worker_erciyuan_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0

    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_erciyuan(url)
    if not all_chapters:
        print(f"No chapters found for {metadata['title']}")
        return

    print(f"Processing {len(all_chapters)} chapters from ErCiYuan.")

    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue

        print(f"Scraping ErCiYuan: Ch {chap['number']}...")
        content = scrape_chapter_erciyuan(chap['url'])

        if content:
            batch.append({
                'number': chap['number'],
                'title': chap['title'],
                'content': content
            })
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)

    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})

# ==========================================
# Main Orchestrator
# ==========================================

@app.route('/', methods=['GET'])
def health_check():
    return "ZEUS Scraper Service is Running", 200

@app.route('/scheduler/config', methods=['POST'])
def configure_scheduler():
    auth_header = request.headers.get('Authorization')
    if auth_header != API_SECRET: return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.json
    SCHEDULER_CONFIG['active'] = data.get('active', False)
    SCHEDULER_CONFIG['interval_seconds'] = int(data.get('interval', 86400))
    SCHEDULER_CONFIG['admin_email'] = data.get('adminEmail', 'system@auto')
    
    # If activating, set next run immediately if not set
    if SCHEDULER_CONFIG['active'] and SCHEDULER_CONFIG['next_run'] < time.time():
        SCHEDULER_CONFIG['next_run'] = time.time() + 5 # Run in 5 seconds
        
    return jsonify({
        'message': 'Scheduler Updated',
        'config': SCHEDULER_CONFIG
    })

@app.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    return jsonify(SCHEDULER_CONFIG)

@app.route('/scrape', methods=['POST'])
def trigger_scrape():
    auth_header = request.headers.get('Authorization')
    if auth_header != API_SECRET: return jsonify({'message': 'Unauthorized'}), 401

    try:
        data = request.json
        url = data.get('url', '').strip()
        admin_email = data.get('adminEmail')
        
        if not url: return jsonify({'message': 'No URL provided'}), 400

        # Ensure URL is clean
        if 'rewayat.club' in url:
            meta = fetch_metadata_rewayat(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_rewayat_probe, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (Rewayat Club).'}), 200
            
        elif 'ar-no.com' in url:
            meta = fetch_metadata_madara(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_madara_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (Ar-Novel).'}), 200

        elif 'markazriwayat.com' in url:
            meta = fetch_metadata_markaz(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_madara_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (Markaz Riwayat).'}), 200

        elif 'novelfire.net' in url:
            meta = fetch_metadata_novelfire(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_novelfire_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (Novel Fire).'}), 200

        elif 'wuxiabox.com' in url or 'wuxiaspot.com' in url:
            meta = fetch_metadata_wuxiabox(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_wuxiabox_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (WuxiaBox/Spot).'}), 200

        elif 'freewebnovel.com' in url:
            meta = fetch_metadata_freewebnovel(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_freewebnovel_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (FreeWebNovel).'}), 200

        elif 'fanmtl.com' in url:
            meta = fetch_metadata_fanmtl(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_fanmtl_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (FanMTL).'}), 200

        elif 'erciyan.com' in url or '二次元' in url:  # detect Chinese site
            meta = fetch_metadata_erciyuan(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_erciyuan_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (ErCiYuan - Chinese Site).'}), 200

        else:
            return jsonify({'message': 'Unsupported Domain'}), 400
            
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Server Error: {error_trace}")
        return jsonify({'message': 'Internal Server Error', 'details': str(e), 'trace': error_trace}), 500

# ==========================================
# 🔄 MAIN AUTOMATIC SCHEDULER LOGIC
# ==========================================

def perform_single_scrape(url, admin_email):
    """Executes scraping for a single URL without creating new threads (synchronous for scheduler)"""
    try:
        if not url: return
        print(f"⏰ Scheduler Checking: {url}")
        
        if 'rewayat.club' in url:
            meta = fetch_metadata_rewayat(url)
            if meta: worker_rewayat_probe(url, admin_email, meta)
        elif 'ar-no.com' in url:
            meta = fetch_metadata_madara(url)
            if meta: worker_madara_list(url, admin_email, meta)
        elif 'markazriwayat.com' in url:
            meta = fetch_metadata_madara(url)
            if meta: worker_madara_list(url, admin_email, meta)
        elif 'novelfire.net' in url:
            meta = fetch_metadata_novelfire(url)
            if meta: worker_novelfire_list(url, admin_email, meta)
        elif 'wuxiabox.com' in url or 'wuxiaspot.com' in url:
            meta = fetch_metadata_wuxiabox(url)
            if meta: worker_wuxiabox_list(url, admin_email, meta)
        elif 'freewebnovel.com' in url:
            meta = fetch_metadata_freewebnovel(url)
            if meta: worker_freewebnovel_list(url, admin_email, meta)
        elif 'fanmtl.com' in url:
            meta = fetch_metadata_fanmtl(url)
            if meta: worker_fanmtl_list(url, admin_email, meta)
        elif 'erciyan.com' in url or '二次元' in url:
            meta = fetch_metadata_erciyuan(url)
            if meta: worker_erciyuan_list(url, admin_email, meta)
    except Exception as e:
        print(f"⚠️ Scheduler Error for {url}: {e}")

def scheduler_loop():
    """Background thread that runs forever"""
    while True:
        try:
            now = time.time()
            if SCHEDULER_CONFIG['active'] and now >= SCHEDULER_CONFIG['next_run']:
                SCHEDULER_CONFIG['status'] = 'running'
                print("🚀 [Scheduler] Starting Auto Update Job...")
                
                # 1. Fetch Watchlist from Node.js using API Key
                try:
                    headers = {'x-api-secret': API_SECRET}
                    res = requests.get(f"{NODE_BACKEND_URL}/api/admin/watchlist", headers=headers, timeout=30)
                    if res.status_code == 200:
                        watchlist = res.json()
                        print(f"📋 [Scheduler] Found {len(watchlist)} novels.")
                        
                        for item in watchlist:
                            if item.get('sourceUrl') and item.get('status') == 'ongoing':
                                perform_single_scrape(item['sourceUrl'], SCHEDULER_CONFIG['admin_email'])
                                time.sleep(2) # Politeness delay
                        
                        print("✅ [Scheduler] Job Completed.")
                    else:
                        print(f"❌ [Scheduler] Failed to fetch watchlist: HTTP {res.status_code}")
                except Exception as req_err:
                    print(f"❌ [Scheduler] Connection Error: {req_err}")

                # Update next run time
                SCHEDULER_CONFIG['last_run'] = now
                SCHEDULER_CONFIG['next_run'] = now + SCHEDULER_CONFIG['interval_seconds']
                SCHEDULER_CONFIG['status'] = 'idle'
            
            time.sleep(5) # Check every 5 seconds
        except Exception as e:
            print(f"🔥 [Scheduler] Critical Loop Error: {e}")
            time.sleep(60)

# Start Scheduler Thread immediately
scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
scheduler_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)