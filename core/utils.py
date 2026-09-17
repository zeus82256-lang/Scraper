# -*- coding: utf-8 -*-
"""
==========================================
🛠️ أدوات السحب المشتركة (Shared Scraper Tools)
==========================================
كل الدوال المساعدة التي تستخدمها جميع ملفات المواقع:
- الترويسات والجلسات (Headers/Sessions)
- إصلاح روابط الصور
- تحويل التواريخ النسبية
- استخراج أرقام الفصول
- مساعد قالب Madara العام (يستخدمه أكثر من موقع)
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin

from .config import MARKAZ_COOKIES

# ==========================================
# 🪪 هويات المستخدم (User Agents) للتبديل بينها
# ==========================================
UA_CHROME = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
UA_FIREFOX = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0'
UA_MOBILE = 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'


def get_headers(referer=None, use_cookies=False, ua=None, lang='ar,en-US;q=0.7,en;q=0.3'):
    """توليد ترويسات كاملة تحاكي المتصفح"""
    headers = {
        'User-Agent': ua or UA_CHROME,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': lang,
        'Connection': 'keep-alive',
    }
    if referer:
        headers['Referer'] = referer

    if use_cookies and MARKAZ_COOKIES and MARKAZ_COOKIES != 'ضع_هنا_الكوكيز_الخاصة_بك_كاملة':
        headers['Cookie'] = MARKAZ_COOKIES

    return headers


def http_get(url, referer=None, use_cookies=False, ua=None, lang='ar,en-US;q=0.7,en;q=0.3',
             timeout=20, encoding=None):
    """طلب GET موحّد يعيد Response أو None عند الفشل"""
    try:
        r = requests.get(
            url,
            headers=get_headers(referer=referer, use_cookies=use_cookies, ua=ua, lang=lang),
            timeout=timeout,
            allow_redirects=True,
        )
        if encoding:
            r.encoding = encoding
        return r
    except Exception as e:
        print(f"❌ GET failed {url[:80]}: {e}")
        return None


def parse_html(content_or_response, parser='html.parser'):
    """تحويل محتوى/استجابة إلى BeautifulSoup مع ترميز صحيح"""
    if content_or_response is None:
        return None
    if hasattr(content_or_response, 'content'):
        return BeautifulSoup(content_or_response.content, parser)
    return BeautifulSoup(content_or_response, parser)


def get_base_url(url):
    """استخراج العنوان الأساسي من أي رابط (scheme://domain)"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def fix_image_url(url, base_url='https://api.rewayat.club'):
    """إصلاح روابط الصور النسبية/المبتورة"""
    if not url:
        return ""
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        if 'novelfire.net' in base_url:
            return 'https://novelfire.net' + url
        elif 'wuxiabox.com' in base_url or 'wuxiaspot.com' in base_url or 'wuxiaworld.site' in base_url:
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}" + url
        return base_url + url
    elif not url.startswith('http'):
        return base_url + '/' + url
    return url


def parse_relative_date(date_str):
    """تحويل التواريخ النسبية (منذ 5 ساعات، يومين ago) إلى تاريخ حقيقي ISO"""
    try:
        if not date_str:
            return None

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
        match = re.search(
            r'(\d+)\s*(sec|min|hour|day|week|month|year|ثانية|ثواني|دقيقة|دقائق|ساعة|ساعات|يوم|أيام|ايام|أسبوع|اسبوع|أسابيع|اسابيع|شهر|أشهر|اشهر|سنة|سنوات)',
            text
        )

        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            delta = timedelta(seconds=0)

            if 'sec' in unit: delta = timedelta(seconds=amount)
            elif 'min' in unit: delta = timedelta(minutes=amount)
            elif 'hour' in unit: delta = timedelta(hours=amount)
            elif 'day' in unit: delta = timedelta(days=amount)
            elif 'week' in unit: delta = timedelta(weeks=amount)
            elif 'month' in unit: delta = timedelta(days=amount * 30)
            elif 'year' in unit: delta = timedelta(days=amount * 365)
            elif 'ثان' in unit: delta = timedelta(seconds=amount)
            elif 'دقيق' in unit: delta = timedelta(minutes=amount)
            elif 'ساع' in unit: delta = timedelta(hours=amount)
            elif 'يوم' in unit or 'أيام' in unit or 'ايام' in unit: delta = timedelta(days=amount)
            elif 'أسبوع' in unit or 'اسبوع' in unit or 'أسابيع' in unit: delta = timedelta(weeks=amount)
            elif 'شهر' in unit or 'أشهر' in unit: delta = timedelta(days=amount * 30)
            elif 'سنة' in unit or 'سنوات' in unit: delta = timedelta(days=amount * 365)

            return (now - delta).isoformat()

        # محاولة قراءة تاريخ ثابت (May 20, 2024 / 2025/12/15)
        for fmt in ['%B %d, %Y', '%Y/%m/%d', '%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S']:
            try:
                dt = datetime.strptime(text, fmt)
                return dt.isoformat()
            except Exception:
                continue

        return None
    except Exception:
        return None


def extract_chapter_number(text, url=''):
    """استخراج رقم الفصل من عنوان أو رابط بأي صيغة (Chapter N / الفصل N / 第N章 / _N)"""
    combined = f"{url} {text or ''}"
    patterns = [
        r'chapter[-_\s.]?(\d+)',
        r'الفصل\s*[-_#]?\s*(\d+)',
        r'فصل\s*[-_#]?\s*(\d+)',
        r'第(\d+)章',
        r'_(\d+)\.html',
        r'/(\d+)(?:/|\.|$)',
    ]
    for pat in patterns:
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                continue
    return 0


def clean_text(text):
    """تنظيف النص من الأسطر الزائدة المتكررة"""
    if not text:
        return ""
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def get_meta(soup, prop=None, name=None):
    """قراءة قيمة meta من الصفحة (og:title / description ...)"""
    if soup is None:
        return ""
    try:
        if prop:
            tag = soup.find('meta', property=prop)
        else:
            tag = soup.find('meta', attrs={'name': name})
        if tag and tag.get('content'):
            return tag['content'].strip()
    except Exception:
        pass
    return ""


# ==========================================
# 🏗️ قالب Madara العام (WordPress Madara Theme)
# ==========================================
# يستخدمه: Ar-Novel / Markaz Riwayat / WuxiaWorld.site وأي موقع Madara جديد
# ==========================================

def clean_madara_title(raw_title):
    cleaned = re.sub(r'^\s*(?:Chapter|الفصل|فصل)?\s*\d+\s*[:\-–]\s*', '', raw_title or '', flags=re.IGNORECASE).strip()
    return cleaned if cleaned else raw_title


def madara_extract_novel_id(soup):
    """استخراج معرف الرواية من صفحة Madara (طرق متعددة)"""
    novel_id = None
    shortlink = soup.find("link", rel="shortlink")
    if shortlink:
        match = re.search(r'p=(\d+)', shortlink.get('href', ''))
        if match:
            novel_id = match.group(1)
    if not novel_id:
        id_input = soup.find('input', class_='rating-post-id')
        if id_input:
            novel_id = id_input.get('value')
    if not novel_id:
        body_tag = soup.find('body')
        if body_tag and body_tag.has_attr('class'):
            for c in body_tag.get('class', []):
                if c.startswith('manga-id-'):
                    novel_id = c.replace('manga-id-', '')
    return novel_id


def madara_fetch_metadata(url, use_cookies=False):
    """جلب بيانات رواية من قالب Madara (التصميم القديم والجديد)"""
    try:
        response = http_get(url, use_cookies=use_cookies, timeout=15)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        # --- فحص وجود صفحة "Coming Soon" (مركز الروايات أُغلق) ---
        page_text = soup.get_text()[:3000]
        if 'coming soon' in page_text.lower() and 'wordpress' not in page_text.lower():
            print(f"🚫 Site appears CLOSED (Coming Soon page): {url[:80]}")
            return None

        # --- التصميم الجديد (قوالب المانجا الجديدة) ---
        is_new_design = bool(soup.select_one('.manga-title'))

        if is_new_design:
            title_tag = soup.select_one('h1.manga-title')
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"

            cover = ""
            img_tag = soup.select_one('.manga-cover-wrap img')
            if img_tag:
                cover = img_tag.get('data-src') or img_tag.get('src')
            cover = fix_image_url(cover, base_url=get_base_url(url))

            desc_div = soup.find('div', id='manga-summary')
            description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""

            status = "مستمرة"
            status_pill = soup.select_one('.manga-status-pill')
            if status_pill:
                txt = status_pill.get_text(strip=True)
                if "مكتملة" in txt or "Completed" in txt:
                    status = "مكتملة"

            tags = [pill.get_text(strip=True) for pill in soup.select('.pill-list .pill')]
            category = tags[0] if tags else "عام"

            novel_id = None
            like_btn = soup.select_one('.manga-like-btn')
            if like_btn and like_btn.has_attr('data-manga-id'):
                novel_id = like_btn['data-manga-id']
            if not novel_id:
                rating_btn = soup.select_one('.manga-stat--rating')
                if rating_btn and rating_btn.has_attr('data-manga-id'):
                    novel_id = rating_btn['data-manga-id']

            last_update = None
            first_ch_row = soup.select_one('.ch-list .ch-row .ch-date')
            if first_ch_row:
                last_update = parse_relative_date(first_ch_row.get_text(strip=True))
        else:
            # --- التصميم القياسي القديم (Madara) ---
            title_tag = soup.find(class_='post-title')
            title = title_tag.find('h1').get_text(strip=True) if title_tag else "Unknown"
            title = re.sub(r'\s*~.*$', '', title)

            cover = ""
            og_img = soup.find("meta", property="og:image")
            if og_img:
                cover = og_img["content"]
            if not cover:
                img_container = soup.find(class_='summary_image')
                if img_container:
                    img_tag = img_container.find('img')
                    if img_tag:
                        cover = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('srcset', '').split(' ')[0]
            cover = fix_image_url(cover, base_url=get_base_url(url))

            novel_id = madara_extract_novel_id(soup)

            desc_div = soup.find(class_='summary__content') or soup.find(class_='description-summary')
            description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""
            description = re.sub(r'\n{3,}', '\n\n', description)

            genres_content = soup.find(class_='genres-content')
            category = "عام"
            tags = []
            if genres_content:
                links = genres_content.find_all('a')
                tags = [a.get_text(strip=True) for a in links]
                if tags:
                    category = tags[0]

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
                last_update = parse_relative_date(timediff_span.get_text(strip=True))
            if not last_update:
                update_node = soup.select_one('.post-on span') or soup.select_one('.post-on')
                if update_node:
                    last_update = parse_relative_date(update_node.get_text(strip=True))

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


def madara_parse_chapters(soup):
    """تحليل قائمة الفصول من HTML (تصميم Madara القديم والجديد)"""
    chapters = []

    # 1. التصميم الجديد (.ch-list .ch-row)
    new_rows = soup.select('.ch-list .ch-row')
    if new_rows:
        for row in new_rows:
            a = row.find('a')
            if not a:
                continue
            link = a.get('href')
            num_div = row.select_one('.ch-num')
            number = 0
            if num_div:
                try:
                    number = int(num_div.get_text(strip=True))
                except ValueError:
                    pass
            if number == 0 and link:
                num_match = re.search(r'(\d+)', link)
                if num_match:
                    number = int(num_match.group(1))
            title_div = row.select_one('.ch-title')
            raw_title = title_div.get_text(strip=True) if title_div else f"Chapter {number}"
            if number > 0:
                chapters.append({'number': number, 'url': link, 'title': clean_madara_title(raw_title)})
        return chapters

    # 2. التصميم القديم (li.wp-manga-chapter)
    items = soup.find_all('li', class_='wp-manga-chapter')
    if items:
        for item in items:
            a = item.find('a')
            if a:
                link = a.get('href')
                raw_title = a.get_text(strip=True)
                num_match = re.search(r'(\d+)', raw_title)
                number = int(num_match.group(1)) if num_match else extract_chapter_number(raw_title, link or '')
                if number > 0:
                    chapters.append({'number': number, 'url': link, 'title': clean_madara_title(raw_title)})
        return chapters

    return chapters


def madara_fetch_chapter_list(novel_id, novel_url, use_cookies=False):
    """جلب قائمة فصول Madara عبر 3 طرق (AJAX ثم admin-ajax ثم HTML مباشر)"""
    chapters = []
    base_url = get_base_url(novel_url)

    # 1. طلب AJAX القياسي
    if novel_url:
        ajax_endpoint = f"{novel_url.rstrip('/')}/ajax/chapters/"
        try:
            headers = get_headers(use_cookies=use_cookies)
            headers['X-Requested-With'] = 'XMLHttpRequest'
            res = requests.post(ajax_endpoint, headers=headers, timeout=20)
            if res.status_code == 200:
                soup = parse_html(res.content)
                chapters = madara_parse_chapters(soup)
                if chapters:
                    print(f"✅ Chapters fetched via /ajax/chapters/ ({len(chapters)})")
        except Exception as e:
            print(f"AJAX endpoint failed: {e}")

    # 2. admin-ajax (بديل)
    if not chapters and novel_id:
        try:
            admin_ajax_url = f"{base_url}/wp-admin/admin-ajax.php"
            data = {'action': 'manga_get_chapters', 'manga': novel_id}
            res = requests.post(admin_ajax_url, data=data,
                                headers=get_headers(novel_url, use_cookies=use_cookies), timeout=20)
            if res.status_code == 200:
                soup = parse_html(res.content)
                chapters = madara_parse_chapters(soup)
                if chapters:
                    print(f"✅ Chapters fetched via admin-ajax ({len(chapters)})")
        except Exception as e:
            print(f"admin-ajax failed: {e}")

    # 3. تحليل صفحة الرواية مباشرة
    if not chapters and novel_url:
        try:
            res = http_get(novel_url, use_cookies=use_cookies, timeout=15)
            if res is not None and res.status_code == 200:
                soup = parse_html(res)
                chapters = madara_parse_chapters(soup)
                if chapters:
                    print(f"✅ Chapters fetched via direct HTML ({len(chapters)})")
        except Exception as e:
            print(f"Direct HTML fetch failed: {e}")

    if chapters:
        chapters.sort(key=lambda x: x['number'])

    return chapters


def madara_scrape_chapter(url, use_cookies=False):
    """سحب محتوى فصل من قالب Madara مع تنظيف شامل"""
    try:
        res = http_get(url, use_cookies=use_cookies, timeout=15)
        if res is None or res.status_code != 200:
            return None
        soup = parse_html(res)

        container = soup.find(class_='reader-target') or \
            soup.find(class_='reading-content') or \
            soup.find(class_='text-left') or \
            soup.find(class_='text-right') or \
            soup.find(class_='entry-content')

        if not container:
            return None

        inner_text_right = container.find(class_='text-right')
        if inner_text_right:
            container = inner_text_right

        for bad in container.find_all(['div', 'script', 'style', 'input', 'ins', 'iframe', 'button']):
            if bad.get('class') and any(
                c in ['nav-links', 'code-block', 'adsbygoogle', 'pf-ad', 'wpmcr-under-title-row']
                for c in bad.get('class')
            ):
                bad.decompose()
            if bad.get('id') == 'reader-btn':
                bad.decompose()

        for nav in container.find_all('div', class_='nav-links'):
            nav.decompose()

        text = container.get_text(separator="\n\n", strip=True)
        text = clean_text(text)
        text = text.replace('اكمال القراءة', '')
        text = text.replace('إعدادات القراءة', '')

        if len(text) < 200 and 'سجل' in text:
            print("⚠️ Warning: Chapter content seems blocked by login wall.")

        return text or None
    except Exception:
        return None


def madara_worker(url, admin_email, metadata, use_cookies=False):
    """العامل الكامل لمواقع Madara"""
    from .backend import send_data_to_backend, check_existing_chapters

    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0

    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = madara_fetch_chapter_list(metadata.get('novel_id'), url, use_cookies=use_cookies)

    if not all_chapters:
        print(f"No chapters found for {metadata['title']}")
        return

    print(f"Processing {len(all_chapters)} chapters.")

    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue

        print(f"Scraping {metadata['title']} - Ch {chap['number']}...")
        content = madara_scrape_chapter(chap['url'], use_cookies=use_cookies)

        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1.5)

    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})


# ==========================================
# 🔄 عامل سحب عام (Generic Worker)
# ==========================================
# يستخدمه معظم المواقع الجديدة: يكفي تمرير دالتي القائمة والمحتوى
# ==========================================

def generic_worker(url, admin_email, metadata, chapters_fn, content_fn,
                   batch_size=5, delay=1.0, base_url_for_join=None):
    """
    عامل سحب موحّد لأي موقع:
    1. يفحص الفصول الموجودة في الباك إند
    2. يرسل بيانات الرواية
    3. يسحب الفصول على دفعات ويرسلها

    chapters_fn(url) -> [{'number': int, 'url': str, 'title': str}, ...]
    content_fn(url)  -> str or None
    """
    from .backend import send_data_to_backend, check_existing_chapters

    try:
        existing_chapters = check_existing_chapters(metadata['title'])
    except Exception:
        existing_chapters = []
    skip_meta = len(existing_chapters) > 0

    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    try:
        all_chapters = chapters_fn(url)
    except Exception as e:
        print(f"❌ chapters_fn failed: {e}")
        all_chapters = []

    if not all_chapters:
        print(f"No chapters found for {metadata['title']}")
        return

    print(f"Processing {len(all_chapters)} chapters.")

    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue

        print(f"Scraping {metadata.get('title', '?')}: Ch {chap['number']}...")
        try:
            content = content_fn(chap['url'])
        except Exception as e:
            print(f"❌ content_fn failed: {e}")
            content = None

        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= batch_size:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(delay)

    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
