# -*- coding: utf-8 -*-
"""
==========================================
🟥 المواقع الصينية (Chinese Novel Sites)
==========================================
المواقع المسجلة في هذا الملف:
1.  Quanben      - quanben.io            ⚠️ يعمل (محجوب عن IP السيرفرات فقط)
2.  52shuku      - 52shuku.net           ✅ يعمل (تم إعادة كتابته للتصميم الجديد)
3.  ErCiYuan     - erciyan.com           ⚠️ يعمل (WAF كابتشا من IP السيرفرات فقط)
4.  69shu        - 69shu.xyz / 69shuba.com   ✅ جديد (Cloudflare أحياناً)
5.  ixdzs8       - ixdzs8.com            ✅ جديد ويعمل بالكامل (爱下电子书)
6.  Linovel      - linovel.net           ✅ جديد ويعمل بالكامل
7.  Linovelib TW - tw.linovelib.com      ✅ جديد ويعمل بالكامل (繁體)
8.  Novel543     - novel543.com          ✅ جديد (Cloudflare متقلب أحياناً)
"""

import re
import time
import json
import requests
from urllib.parse import urljoin, urlparse

from core.registry import register_site
from core.utils import (
    http_get, parse_html, get_headers, get_base_url, fix_image_url,
    parse_relative_date, extract_chapter_number, clean_text, get_meta,
    UA_FIREFOX,
    generic_worker,
)


# ==========================================
# 🔵 1. Quanben.io (全本网)
# ==========================================
# ⚠️ الموقع يعمل لكنه يحجب IP مراكز البيانات (403 Apache).

def fetch_metadata_quanben(url):
    try:
        # إذا كان رابط فصل، حوّله لصفحة الكتاب
        if '/n/' in url:
            match = re.search(r'/n/([^/]+)/', url)
            if match:
                slug = match.group(1)
            else:
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                if 'n' in path_parts:
                    idx = path_parts.index('n')
                    if idx + 1 < len(path_parts):
                        slug = path_parts[idx + 1]
                    else:
                        return None
                else:
                    return None
            info_url = f"https://www.quanben.io/n/{slug}/"
        else:
            info_url = url

        response = http_get(info_url, timeout=15)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        title = ""
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        if not title:
            title_span = soup.select_one('.list2 h3 span')
            if title_span:
                title = title_span.get_text(strip=True)
        if not title:
            title = "Unknown Title"

        cover = ""
        img = soup.select_one('.list2 img')
        if img:
            cover = img.get('src')
            if cover:
                if cover.startswith('//'):
                    cover = 'https:' + cover
                elif cover.startswith('/'):
                    cover = 'https://www.quanben.io' + cover

        description = ""
        desc_p = soup.select_one('.description p')
        if desc_p:
            description = desc_p.get_text(strip=True)
        else:
            description = get_meta(soup, name='description')

        status = "مستمرة"
        page_text = soup.get_text()
        if '完结' in page_text:
            status = "مكتملة"

        category = "عام"
        cat_span = soup.select_one('.list2 p:-soup-contains("类别") span')
        if cat_span:
            category = cat_span.get_text(strip=True)

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': [],
            'sourceUrl': info_url,
            'lastUpdate': None
        }
    except Exception as e:
        print(f"Error quanben metadata: {e}")
        return None


def fetch_chapter_list_quanben(url):
    chapters = []
    try:
        if '/n/' in url and url.endswith('.html'):
            list_url = url.rsplit('/', 1)[0] + '/list.html'
        elif '/n/' in url and not url.endswith('/list.html'):
            if url.endswith('/'):
                list_url = url + 'list.html'
            else:
                list_url = url + '/list.html'
        else:
            list_url = url

        response = http_get(list_url, timeout=15)
        if response is None or response.status_code != 200:
            return chapters
        soup = parse_html(response)

        links = soup.select('ul.list3 li a')
        for a in links:
            href = a.get('href')
            if not href:
                continue
            full_url = urljoin('https://www.quanben.io', href)
            text = a.get_text(strip=True)
            num_match = re.search(r'/(\d+)\.html', href)
            if not num_match:
                num_match = re.search(r'第(\d+)章', text)
            number = int(num_match.group(1)) if num_match else 0
            if number > 0:
                chapters.append({'number': number, 'url': full_url, 'title': text.strip()})

        # ملء الفصول الناقصة بالتخمين المباشر (الترقيم متسلسل)
        if chapters:
            max_num = max(c['number'] for c in chapters)
            existing_nums = {c['number'] for c in chapters}
            base_url = re.sub(r'\d+\.html$', '', chapters[0]['url'])
            for i in range(1, max_num + 1):
                if i not in existing_nums:
                    chapters.append({'number': i, 'url': f"{base_url}{i}.html", 'title': f'第{i}章'})
            chapters.sort(key=lambda x: x['number'])

        return chapters
    except Exception as e:
        print(f"Error quanben chapter list: {e}")
        return chapters


def scrape_chapter_quanben(url):
    try:
        response = http_get(url, timeout=15)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        content_div = soup.find('div', id='content')
        if not content_div:
            return None

        for bad in content_div.find_all(['script', 'style', 'ins', 'iframe']):
            bad.decompose()

        paragraphs = content_div.find_all('p')
        if paragraphs:
            text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            text = content_div.get_text(separator='\n\n', strip=True)

        text = re.sub(r'<!--PAGE \d+-->', '', text)
        text = clean_text(text)

        if len(text.strip()) < 50:
            return None
        return text
    except Exception as e:
        print(f"Error scraping quanben chapter: {e}")
        return None


def worker_quanben(url, admin_email, metadata):
    generic_worker(url, admin_email, metadata, fetch_chapter_list_quanben, scrape_chapter_quanben)


# ==========================================
# ⚪ 2. 52shuku.net (52书库) - التصميم الجديد بالكامل
# ==========================================
# الموقع غيّر بنيته: الكتاب الآن /{تصنيف}/{id}.html والفصول
# صفحات متتابعة /{تصنيف}/{id}_{صفحة}.html

def fetch_metadata_52shuku(url):
    try:
        response = http_get(url, timeout=15)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        # العنوان من h1 بصيغة: 书名_作者【状态】
        title = "Unknown Title"
        author = ""
        h1 = soup.select_one('h1.article-title') or soup.find('h1') or soup.find('title')
        if h1:
            title = h1.get_text(strip=True).split('_')[0].strip()
            full = h1.get_text(strip=True)
            parts = full.split('_')
            if len(parts) > 1:
                author = parts[1].strip()

        status = "مستمرة"
        if '完结' in title or '完本' in title:
            status = "مكتملة"

        # الوصف من الفقرة بعد "小说简介："
        description = ""
        article = soup.find('article', class_='article-content') or soup.find('div', class_='article-content')
        if article:
            for p in article.find_all('p'):
                txt = p.get_text(strip=True)
                if '小说简介' in txt:
                    # الوصف داخل نفس الفقرة بعد النقطتين أو الفقرة التالية
                    after = txt.split('小说简介：')[-1].strip()
                    if after:
                        description = after
                    else:
                        next_p = p.find_next_sibling('p')
                        if next_p:
                            description = next_p.get_text(strip=True)
                    break
            if not description:
                # خذ أول فقرة معتبرة
                for p in article.find_all('p'):
                    txt = p.get_text(strip=True)
                    if len(txt) > 40 and '传送门' not in txt:
                        description = txt
                        break

        # الغلاف من og:image إن وجد
        cover = get_meta(soup, prop='og:image')

        # معرف الكتاب للتسلسل
        book_match = re.search(r'/(\w+)/(\d+)\.html', url)

        return {
            'title': title, 'description': description, 'cover': cover,
            'author': author, 'status': status, 'category': "عام", 'tags': [],
            'sourceUrl': url,
            'lastUpdate': None
        }
    except Exception as e:
        print(f"Error 52shuku metadata: {e}")
        return None


def fetch_chapter_list_52shuku(url):
    """
    قائمة "الفصول" = صفحات الكتاب المتتابعة:
    صفحة 2، 3، 4... إلى آخر صفحة (نتبع رابط الصفحة التالية)
    """
    chapters = []
    try:
        m = re.match(r'(https?://[^/]+/.+?)/(\d+)\.html', url)
        if not m:
            return chapters
        base_path, book_id = m.group(1), m.group(2)

        current_page = 2  # الصفحة الأولى هي صفحة الكتاب نفسها (مقدمة)
        while current_page and current_page < 5000:
            page_url = f"{base_path}/{book_id}_{current_page}.html"
            res = http_get(page_url, timeout=15)
            if res is None or res.status_code != 200:
                break
            soup = parse_html(res)

            chapters.append({
                'number': current_page - 1,  # نبدأ الترقيم من 1
                'url': page_url,
                'title': f"صفحة {current_page - 1}",
            })

            # البحث عن رابط الصفحة التالية
            next_page = None
            for a in soup.find_all('a', href=True):
                hm = re.search(rf'/{book_id}_(\d+)\.html', a['href'])
                if hm and int(hm.group(1)) == current_page + 1:
                    next_page = int(hm.group(1))
                    break

            # إن لم يوجد رابط تالٍ مباشر، جرّب الأعلى المذكور
            if not next_page:
                all_nums = [
                    int(x) for x in re.findall(rf'/{book_id}_(\d+)\.html', str(soup))
                    if int(x) > current_page
                ]
                if all_nums:
                    next_page = min(all_nums)

            if not next_page:
                break
            current_page = next_page
            time.sleep(0.4)

        print(f"✅ Total 52shuku pages found: {len(chapters)}")
        return chapters
    except Exception as e:
        print(f"Error 52shuku page list: {e}")
        return chapters


def scrape_chapter_52shuku(url):
    try:
        response = http_get(url, timeout=15)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        content_div = soup.find('article', class_='article-content') or soup.find('div', id='nr1')
        if not content_div:
            return None

        for bad in content_div.find_all(['script', 'style', 'ins', 'iframe', 'button']):
            bad.decompose()
        for div in content_div.find_all('div'):
            if div.get('id') and div.get('id').startswith('pf-'):
                div.decompose()
            elif div.get('class') and any(c in ['pagination2', 'breadcrumbs', 'nr_set', 'meta', 'article-nav', 'related_top'] for c in div.get('class', [])):
                div.decompose()

        paragraphs = content_div.find_all('p')
        if paragraphs:
            text_parts = []
            for p in paragraphs:
                pt = p.get_text(strip=True)
                if pt and not re.match(r'^Tips：|^传送门：|^哦豁，小伙伴们', pt):
                    text_parts.append(pt)
            text = '\n\n'.join(text_parts)
        else:
            text = content_div.get_text(separator='\n\n', strip=True)

        text = clean_text(text)
        if len(text.strip()) < 20:
            return None
        return text
    except Exception as e:
        print(f"Error scraping 52shuku page: {e}")
        return None


def worker_52shuku(url, admin_email, metadata):
    generic_worker(url, admin_email, metadata, fetch_chapter_list_52shuku, scrape_chapter_52shuku)


# ==========================================
# 🟤 3. ErCiYuan (二次元小说网 - erciyan.com)
# ==========================================
# ⚠️ الموقع يعمل لكن WAF يعرض كابتشا لعناوين مراكز البيانات.

ZH_HEADERS_LANG = 'zh-CN,zh;q=0.9'


def fetch_metadata_erciyuan(url):
    try:
        response = http_get(url, timeout=15, lang=ZH_HEADERS_LANG)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        title_tag = soup.select_one('div.info h1') or soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        cover = ""
        img_tag = soup.select_one('div.imgbox img')
        if img_tag:
            cover = img_tag.get('src')
        if not cover:
            cover = get_meta(soup, prop='og:image')
        if cover and cover.startswith('/'):
            cover = get_base_url(url) + cover

        desc_div = soup.select_one('div.desc') or soup.select_one('div.m-desc')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""

        status = "مستمرة"
        category = "عام"
        tags = []
        info_div = soup.select_one('div.info')
        if info_div:
            info_text = info_div.get_text()
            status_match = re.search(r'状态[：:]\s*([^\s]+)', info_text)
            if status_match and ('完结' in status_match.group(1)):
                status = "مكتملة"
            cat_match = re.search(r'类[：:]\s*([^\s]+)', info_text)
            if cat_match:
                category = cat_match.group(1)
            tags = [category] if category != "عام" else []

        last_update = None
        update_match = re.search(r'最后更新[：:]\s*(\d{4}-\d{1,2}-\d{1,2}\s*\d{1,2}:\d{1,2}:\d{1,2})', soup.get_text())
        if update_match:
            try:
                from datetime import datetime
                dt = datetime.strptime(update_match.group(1), '%Y-%m-%d %H:%M:%S')
                last_update = dt.isoformat()
            except Exception:
                pass

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'sourceUrl': url, 'lastUpdate': last_update
        }
    except Exception as e:
        print(f"Error ErCiYuan metadata: {e}")
        return None


def fetch_chapter_list_erciyuan(url):
    chapters = []
    try:
        response = http_get(url, timeout=15, lang=ZH_HEADERS_LANG)
        if response is None or response.status_code != 200:
            return chapters
        soup = parse_html(response)

        section_box = soup.select_one('div.section-box')
        chapter_items = section_box.select('ul.section-list li a') if section_box else soup.select('ul.section-list li a')

        base_url = get_base_url(url)

        for a in chapter_items:
            href = a.get('href')
            if not href:
                continue
            full_url = urljoin(base_url, href)
            raw_title = a.get_text(strip=True)

            num_match = re.search(r'第(\d+)章', raw_title)
            number = int(num_match.group(1)) if num_match else extract_chapter_number(raw_title, href)

            clean_title = re.sub(r'^第\d+章\s*', '', raw_title).strip() or raw_title

            if number > 0:
                chapters.append({'number': number, 'url': full_url, 'title': clean_title})

        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"Error ErCiYuan chapter list: {e}")
        return chapters


def scrape_chapter_erciyuan(url):
    try:
        response = http_get(url, timeout=15, lang=ZH_HEADERS_LANG)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        content_div = soup.find('div', id='content') or soup.find('div', class_='content')
        if not content_div:
            return None

        for bad in content_div.find_all(['script', 'style', 'ins', 'iframe']):
            bad.decompose()

        paragraphs = content_div.find_all('p')
        if paragraphs:
            text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            text = content_div.get_text(separator="\n\n", strip=True)

        text = re.sub(r'本章未完，点击下一页继续阅读', '', text)
        text = re.sub(r'请收藏本站：https?://\S+', '', text)
        text = re.sub(r'最新章节请.*', '', text, flags=re.IGNORECASE)
        text = clean_text(text)

        return text if len(text.strip()) > 50 else None
    except Exception as e:
        print(f"Error scraping ErCiYuan chapter: {e}")
        return None


def worker_erciyuan(url, admin_email, metadata):
    generic_worker(url, admin_email, metadata, fetch_chapter_list_erciyuan, scrape_chapter_erciyuan)


# ==========================================
# 🐉 4. 69shu / 69shuba (69书吧)
# ==========================================
# جديد! المصدر من LNReader. الدومين يتغير بين:
# 69shu.xyz / 69shu.com / 69shuba.com / 69shuba.cx
# الموقع يستخدم ترميز GBK!

SHU69_DOMAINS = ['www.69shu.xyz', 'www.69shu.com', 'www.69shuba.com', '69shuba.com', '69shu.xyz']


def _shu69_base(url=''):
    """تحديد الدومين الأساسي: من الرابط نفسه أو أول دومين يعمل"""
    if url:
        parsed = urlparse(url)
        if parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    for domain in SHU69_DOMAINS:
        base = f"https://{domain}"
        r = http_get(base, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=12)
        if r is not None and r.status_code == 200 and 'just a moment' not in r.text[:3000].lower():
            return base
    return 'https://www.69shu.xyz'


def _shu69_get(url, timeout=15):
    """طلب مع ترميز GBK الصحيح"""
    r = http_get(url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=timeout)
    if r is not None:
        r.encoding = 'gbk'
    return r


def fetch_metadata_69shu(url):
    try:
        r = _shu69_get(url)
        if r is None or r.status_code != 200:
            return None
        soup = parse_html(r.text)

        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        cover = ""
        cover_img = soup.select_one('div.cover > img, .book-img img')
        if cover_img:
            cover = cover_img.get('src') or cover_img.get('data-src') or ""
        cover = fix_image_url(cover, base_url=get_base_url(url))

        summary_div = soup.select_one('#bookIntro, .book-intro')
        description = summary_div.get_text("\n", strip=True) if summary_div else ""
        description = re.sub(r'^简介[:：]?\s*', '', description)

        author = ""
        status = "مستمرة"
        info_p = soup.select_one('div.caption-bookinfo p, .book-info')
        if info_p:
            a_tag = info_p.find('a')
            if a_tag:
                author = a_tag.get('title') or a_tag.get_text(strip=True)
            if '连载' not in info_p.get_text():
                status = "مكتملة"

        # معرف الكتاب لقائمة الفصول
        book_id_match = re.search(r'/txt/(\d+)', url)

        return {
            'title': title, 'description': description, 'cover': cover,
            'author': author, 'status': status, 'category': "عام", 'tags': [],
            'book_id': book_id_match.group(1) if book_id_match else None,
            'sourceUrl': url,
            'lastUpdate': None
        }
    except Exception as e:
        print(f"Error 69shu metadata: {e}")
        return None


def fetch_chapter_list_69shu(url):
    """قائمة الفصول: من صفحة الفهرس الكامل (مع ترقيم صفحات داخلي)"""
    chapters = []
    try:
        base = get_base_url(url)

        # 1. إيجاد رابط الفهرس الكامل (dd.all > a)
        r = _shu69_get(url)
        if r is None or r.status_code != 200:
            return []
        soup = parse_html(r.text)

        all_link = soup.select_one('dd.all > a')
        if not all_link or not all_link.get('href'):
            # جرّب مباشرة نمط /txt/{id}/all.html أو /txt/{id}.html
            m = re.search(r'/txt/(\d+)', url)
            if m:
                catalog_url = f"{base}/txt/{m.group(1)}/all.html"
            else:
                return []
        else:
            catalog_url = urljoin(base, all_link['href'])

        # 2. التنقل بين صفحات الفهرس
        current_url = catalog_url
        visited = set()
        while current_url and current_url not in visited:
            visited.add(current_url)
            rc = _shu69_get(current_url)
            if rc is None or rc.status_code != 200:
                break
            csoup = parse_html(rc.text)

            for dd in csoup.select('dl.panel-chapterlist dd'):
                a = dd.find('a')
                if not a or not a.get('href'):
                    continue
                href = a['href']
                full_link = href if href.startswith('http') else urljoin(base, href)
                title = a.get_text(strip=True)
                number = extract_chapter_number(title, full_link)
                if number > 0 and not any(c['number'] == number for c in chapters):
                    chapters.append({'number': number, 'url': full_link, 'title': title})

            # رابط الصفحة التالية (下一页)
            next_link = None
            for a in csoup.select('div.listpage a'):
                if '下一页' in a.get_text() and a.get('href') and 'javascript' not in a['href']:
                    next_link = urljoin(base, a['href'])
                    break
            current_url = next_link
            if current_url:
                time.sleep(0.5)

        chapters.sort(key=lambda x: x['number'])
        print(f"✅ Total 69shu chapters found: {len(chapters)}")
        return chapters
    except Exception as e:
        print(f"Error 69shu chapter list: {e}")
        return chapters


def scrape_chapter_69shu(url):
    try:
        r = _shu69_get(url)
        if r is None or r.status_code != 200:
            return None
        soup = parse_html(r.text)

        content_div = soup.select_one('#chaptercontent') or soup.select_one('.txtnav')
        if not content_div:
            return None

        for bad in content_div.find_all(['script', 'style', 'ins', 'iframe']):
            bad.decompose()

        ps = content_div.find_all('p')
        if ps:
            lines = [p.get_text(strip=True) for p in ps]
        else:
            lines = content_div.get_text('\n').split('\n')

        lines = [ln.strip() for ln in lines]
        lines = [ln for ln in lines if ln and '69书吧' not in ln and '69書吧' not in ln]
        text = '\n\n'.join(lines)
        text = clean_text(text)

        if len(text.strip()) < 50:
            return None
        return text
    except Exception:
        return None


def worker_69shu(url, admin_email, metadata):
    generic_worker(url, admin_email, metadata, fetch_chapter_list_69shu, scrape_chapter_69shu)


# ==========================================
# 📖 5. ixdzs8 (爱下电子书 - ixdzs8.com)
# ==========================================
# جديد ويعمل بالكامل! واجهة API للفصول + معالجة تحدي الأمان.

def fetch_metadata_ixdzs8(url):
    try:
        response = http_get(url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=15)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        title_tag = soup.select_one('.n-text h1') or soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        cover = ""
        img_tag = soup.select_one('.n-img img')
        if img_tag:
            cover = img_tag.get('src') or ""
        cover = fix_image_url(cover, base_url='https://ixdzs8.com')

        intro = soup.select_one('p#intro')
        description = intro.get_text('\n', strip=True) if intro else ""

        status = "مستمرة"
        if soup.select_one('.n-text p span.end'):
            status = "مكتملة"

        tags = []
        for a in soup.select('div.panel div.tags a, .n-text .n-tag a'):
            txt = a.get_text(strip=True)
            if txt:
                tags.append(txt)
        category = tags[0] if tags else "عام"

        # معرف الكتاب من الرابط /read/{id}/ أو /baidu/{id}/
        book_match = re.search(r'/(?:read|baidu)/(\d+)', url)

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'book_id': book_match.group(1) if book_match else None,
            'sourceUrl': url,
            'lastUpdate': None
        }
    except Exception as e:
        print(f"Error ixdzs8 metadata: {e}")
        return None


def fetch_chapter_list_ixdzs8(url):
    """قائمة الفصول عبر POST /novel/clist/ (JSON)"""
    chapters = []
    try:
        book_match = re.search(r'/(?:read|baidu)/(\d+)', url)
        if not book_match:
            print("ixdzs8: cannot extract book id")
            return []
        book_id = book_match.group(1)

        resp = requests.post(
            'https://ixdzs8.com/novel/clist/',
            data=f'bid={book_id}',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': UA_FIREFOX,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            print(f"ixdzs8 clist failed: HTTP {resp.status_code}")
            return []

        data = resp.json()
        if data.get('rs') != 200 or not isinstance(data.get('data'), list):
            print("ixdzs8: invalid clist response")
            return []

        for ch in data['data']:
            try:
                order = int(ch.get('ordernum', 0))
            except (ValueError, TypeError):
                continue
            # فقط الفصول العادية (ctype=0)
            if str(ch.get('ctype', '0')) != '0':
                continue
            title = ch.get('title', f"第{order}章")
            chapters.append({
                'number': order,
                'url': f"https://ixdzs8.com/read/{book_id}/p{order}.html",
                'title': title,
            })

        chapters.sort(key=lambda x: x['number'])
        print(f"✅ ixdzs8 chapters found: {len(chapters)}")
        return chapters
    except Exception as e:
        print(f"Error ixdzs8 chapter list: {e}")
        return chapters


def scrape_chapter_ixdzs8(url):
    """سحب فصل مع معالجة تحدي الأمان (?challenge=token)"""
    try:
        res = http_get(url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=20)
        if res is None or res.status_code != 200:
            return None
        html = res.text

        # فحص صفحة التحدي
        if '正在進行安全驗證' in html or 'challenge' in html[:3000]:
            token_match = re.search(r'let token\s*=\s*"([^"]+)"', html)
            if token_match:
                challenge_url = url + '?challenge=' + token_match.group(1)
                res = http_get(challenge_url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=20)
                if res is None or res.status_code != 200:
                    return None
                html = res.text

        soup = parse_html(html)
        content = soup.select_one('article section')
        if not content:
            return None

        # تنظيف الإعلانات والعناصر الزائدة
        for bad in content.find_all(['script', 'style', 'ins', 'iframe']):
            bad.decompose()
        for p in content.find_all('p'):
            if not p.get_text(strip=True):
                p.decompose()

        text = content.get_text(separator='\n\n', strip=True)
        text = re.sub(r'推薦本書.*', '', text)
        text = clean_text(text)

        if len(text.strip()) < 50:
            return None
        return text
    except Exception:
        return None


def worker_ixdzs8(url, admin_email, metadata):
    generic_worker(url, admin_email, metadata, fetch_chapter_list_ixdzs8, scrape_chapter_ixdzs8)


# ==========================================
# 🌸 6. Linovel (轻小说文库 - linovel.net)
# ==========================================
# جديد ويعمل بالكامل!

def fetch_metadata_linovel(url):
    try:
        response = http_get(url, lang=ZH_HEADERS_LANG, timeout=15)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        title_tag = soup.select_one('h1.book-title') or soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        cover = ""
        img_tag = soup.select_one('.book-cover img, div.cover img')
        if img_tag:
            cover = img_tag.get('src') or ""
        if not cover:
            cover = get_meta(soup, prop='og:image')
        cover = fix_image_url(cover, base_url='https://www.linovel.net')

        description = ""
        desc_div = soup.select_one('#bookSummary, .book-summary, .book-information .summary')
        if desc_div:
            description = desc_div.get_text('\n', strip=True)
        else:
            description = get_meta(soup, name='description')

        status = "مستمرة"
        page_text = soup.get_text()[:5000]
        if '完结' in page_text:
            status = "مكتملة"

        tags = []
        for a in soup.select('.book-info a[href*="/tags/"], .book-meta a[href*="tag"]'):
            txt = a.get_text(strip=True)
            if txt:
                tags.append(txt)
        category = tags[0] if tags else "عام"

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'sourceUrl': url,
            'lastUpdate': None
        }
    except Exception as e:
        print(f"Error linovel metadata: {e}")
        return None


def fetch_chapter_list_linovel(url):
    chapters = []
    try:
        response = http_get(url, lang=ZH_HEADERS_LANG, timeout=15)
        if response is None or response.status_code != 200:
            return chapters
        soup = parse_html(response)

        base_url = get_base_url(url)
        seen = set()
        index = 0

        # قائمة الفصول داخل #chapter-list أو .chapter-list
        chapter_links = soup.select('#chapter-list a, .chapter-list a, .cate-item a')
        for a in chapter_links:
            href = a.get('href')
            if not href or not re.search(r'/book/\d+/\d+\.html', href):
                continue
            full_url = href if href.startswith('http') else urljoin(base_url, href)
            if full_url in seen:
                continue
            seen.add(full_url)
            index += 1
            raw_title = a.get_text(strip=True)
            clean_title = re.sub(r'^第\d+[章节]\s*', '', raw_title).strip() or raw_title

            # ✅ روابط linovel تستخدم معرفات غير متسلسلة - نعتمد الترتيب
            chapters.append({'number': index, 'url': full_url, 'title': clean_title})

        chapters.sort(key=lambda x: x['number'])
        print(f"✅ linovel chapters found: {len(chapters)}")
        return chapters
    except Exception as e:
        print(f"Error linovel chapter list: {e}")
        return chapters


def scrape_chapter_linovel(url):
    try:
        response = http_get(url, lang=ZH_HEADERS_LANG, timeout=15)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        content_div = soup.select_one('#aContent') or soup.select_one('.read-content')
        if not content_div:
            return None

        for bad in content_div.find_all(['script', 'style', 'ins', 'iframe']):
            bad.decompose()

        text = content_div.get_text(separator='\n\n', strip=True)
        text = re.sub(r'本章未完.*', '', text)
        text = clean_text(text)

        if len(text.strip()) < 50:
            return None
        return text
    except Exception:
        return None


def worker_linovel(url, admin_email, metadata):
    generic_worker(url, admin_email, metadata, fetch_chapter_list_linovel, scrape_chapter_linovel)


# ==========================================
# 🇹🇼 7. Linovelib TW (轻小说文库繁体 - tw.linovelib.com)
# ==========================================
# جديد ويعمل بالكامل!

def fetch_metadata_linovelib_tw(url):
    try:
        response = http_get(url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=15)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        title_tag = soup.select_one('h1.book-title') or soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        cover = ""
        img_tag = soup.select_one('.book-info img, .cover img')
        if img_tag:
            cover = img_tag.get('src') or img_tag.get('data-src') or ""
        if not cover:
            cover = get_meta(soup, prop='og:image')
        cover = fix_image_url(cover, base_url='https://tw.linovelib.com')

        description = ""
        desc_div = soup.select_one('.book-info .intro, #bookIntro, .book-intro')
        if desc_div:
            description = desc_div.get_text('\n', strip=True)
        else:
            description = get_meta(soup, name='description')

        status = "مستمرة"
        page_text = soup.get_text()[:5000]
        if '完結' in page_text or '完结' in page_text:
            status = "مكتملة"

        tags = []
        for a in soup.select('.book-info a[href*="/tags/"], .book-info a[href*="wenku"]'):
            txt = a.get_text(strip=True)
            if txt and len(txt) < 20:
                tags.append(txt)
        category = tags[0] if tags else "عام"

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'sourceUrl': url,
            'lastUpdate': None
        }
    except Exception as e:
        print(f"Error linovelib_tw metadata: {e}")
        return None


def fetch_chapter_list_linovelib_tw(url):
    """قائمة الفصول من صفحة الفهرس /novel/{id}/catalog (بترقيم تسلسلي)"""
    chapters = []
    try:
        base_url = get_base_url(url)
        book_match = re.search(r'/novel/(\d+)', url)
        if not book_match:
            return []
        book_id = book_match.group(1)

        catalog_url = f"{base_url}/novel/{book_id}/catalog"
        response = http_get(catalog_url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=15)
        if response is None or response.status_code != 200:
            # جرّب صفحة الكتاب نفسها
            response = http_get(url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=15)
            if response is None or response.status_code != 200:
                return []
        soup = parse_html(response)

        seen = set()
        index = 0
        for a in soup.find_all('a', href=True):
            href = a['href']
            # روابط الفصول: /novel/{id}/{cid}.html (نستثني vol_ و _N.html)
            if not re.search(rf'/novel/{book_id}/\d+\.html$', href):
                continue
            full_url = href if href.startswith('http') else urljoin(base_url, href)
            if full_url in seen:
                continue
            seen.add(full_url)
            index += 1
            raw_title = a.get_text(strip=True)
            clean_title = re.sub(r'^第\d+[章节][\s　]*', '', raw_title).strip() or raw_title

            # ✅ المعرف في الرابط غير متسلسل - نعتمد ترتيب الفهرس
            chapters.append({'number': index, 'url': full_url, 'title': clean_title})

        chapters.sort(key=lambda x: x['number'])
        print(f"✅ linovelib_tw chapters found: {len(chapters)}")
        return chapters
    except Exception as e:
        print(f"Error linovelib_tw chapter list: {e}")
        return chapters


def scrape_chapter_linovelib_tw(url):
    """سحب فصل من linovelib TW مع دعم الفصول متعددة الصفحات (_2.html ...)"""
    try:
        all_text = []
        current_url = url
        visited = set()

        while current_url and current_url not in visited:
            visited.add(current_url)
            response = http_get(current_url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=15)
            if response is None or response.status_code != 200:
                break
            soup = parse_html(response)

            # ✅ الحاوية الصحيحة هي #acontent
            content_div = soup.select_one('#acontent') or soup.select_one('#cContent') or soup.select_one('#content')
            if content_div:
                for bad in content_div.find_all(['script', 'style', 'ins', 'iframe']):
                    bad.decompose()
                txt = content_div.get_text(separator='\n\n', strip=True)
                if txt:
                    all_text.append(txt)

            # البحث عن صفحة تالية للفصل الواحد (chapter_2.html)
            next_url = None
            for a in soup.find_all('a', href=True):
                href = a['href']
                if re.search(r'_\d+\.html', href) and ('下一頁' in a.get_text() or '下一页' in a.get_text() or 'next' in a.get_text().lower()):
                    next_url = urljoin(current_url, href)
                    break
            current_url = next_url
            if current_url:
                time.sleep(0.5)

        text = clean_text('\n\n'.join(all_text))
        if len(text.strip()) < 50:
            return None
        return text
    except Exception:
        return None


def worker_linovelib_tw(url, admin_email, metadata):
    generic_worker(url, admin_email, metadata, fetch_chapter_list_linovelib_tw, scrape_chapter_linovelib_tw)


# ==========================================
# 📚 8. Novel543 (novel543.com) - 稷下書院
# ==========================================
# جديد! الموقع من عائلة MTLNation بالتصميم البوليسار (Quasar).

def fetch_metadata_novel543(url):
    try:
        response = http_get(url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=20)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        # العنوان من قسم التفاصيل
        title = ""
        info_h1 = soup.select_one('section#detail div.media-content.info h1.title') or soup.find('h1')
        if info_h1:
            title = info_h1.get_text(strip=True)
        if not title:
            title = get_meta(soup, prop='og:title') or "Unknown Title"

        cover = ""
        cover_img = soup.select_one('section#detail div.cover img')
        if cover_img:
            cover = cover_img.get('src') or ""
        if not cover:
            cover = get_meta(soup, prop='og:image')
        cover = fix_image_url(cover, base_url='https://www.novel543.com')

        description = ""
        intro_div = soup.select_one('section#detail div.mod div.intro')
        if intro_div:
            description = intro_div.get_text('\n', strip=True)
        else:
            description = get_meta(soup, name='description')

        author = ""
        author_span = soup.select_one('section#detail p.meta span.author')
        if author_span:
            author = author_span.get_text(strip=True)

        tags = []
        for a in soup.select('section#detail p.meta a[href*="/bookstack/"]'):
            txt = a.get_text(strip=True)
            if txt:
                tags.append(txt)
        category = tags[0] if tags else "عام"

        status = "مستمرة"
        page_text = soup.get_text()[:6000]
        if '完結' in page_text or '完结' in page_text:
            status = "مكتملة"

        return {
            'title': title, 'description': description, 'cover': cover,
            'author': author, 'status': status, 'category': category, 'tags': tags,
            'sourceUrl': url,
            'lastUpdate': None
        }
    except Exception as e:
        print(f"Error novel543 metadata: {e}")
        return None


def fetch_chapter_list_novel543(url):
    """قائمة الفصول: من رابط الفهرس ({id}/dir) داخل صفحة الرواية"""
    chapters = []
    try:
        base_url = get_base_url(url)
        response = http_get(url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=20)
        if response is None or response.status_code != 200:
            return []
        soup = parse_html(response)

        # البحث عن رابط الفهرس (ينتهي بـ /dir)
        catalog_link = None
        for a in soup.select('a[href]'):
            href = a['href']
            if href.rstrip('/').endswith('/dir'):
                catalog_link = urljoin(base_url, href)
                break

        if not catalog_link:
            # بناء الرابط مباشرة من معرف الرواية /{id}/
            m = re.search(r'novel543\.com/(\d+)/?', url)
            if m:
                catalog_link = f"{base_url}/{m.group(1)}/dir"
            else:
                return []

        # جلب صفحة الفهرس
        r2 = http_get(catalog_link, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=20)
        if r2 is None or r2.status_code != 200:
            return []
        csoup = parse_html(r2.text)

        index = 0
        for a in csoup.select('div.chaplist ul.all li a'):
            href = a.get('href')
            if not href:
                continue
            index += 1
            full_url = href if href.startswith('http') else urljoin(base_url, href)
            title = a.get_text(strip=True) or f"第{index}章"
            chapters.append({'number': index, 'url': full_url, 'title': title})

        # فحص ترتيب القائمة (倒序 = عكسي)
        sort_btn = csoup.select_one('div.chaplist .header button.reverse span:last-child')
        if sort_btn and sort_btn.get_text(strip=True) == '倒序' and chapters:
            # القائمة معروضة من الأحدث؛ نرتّبها تصاعدياً حسب الرقم
            chapters.reverse()

        chapters.sort(key=lambda x: x['number'])
        print(f"✅ novel543 chapters found: {len(chapters)}")
        return chapters
    except Exception as e:
        print(f"Error novel543 chapter list: {e}")
        return chapters


def scrape_chapter_novel543(url):
    try:
        response = http_get(url, ua=UA_FIREFOX, lang=ZH_HEADERS_LANG, timeout=20)
        if response is None or response.status_code != 200:
            return None
        soup = parse_html(response)

        content_div = soup.select_one('div.content.py-5') or soup.select_one('.chap-content')
        if not content_div:
            return None

        for bad in content_div.find_all(['script', 'style', 'ins', 'iframe']):
            bad.decompose()

        lines = []
        for p in content_div.find_all('p'):
            txt = p.get_text(strip=True)
            if not txt:
                continue
            if any(k in txt for k in ['請記住本站域名', '手機版閱讀網址', 'novel543', '稷下書院']):
                continue
            lines.append(txt)

        text = '\n\n'.join(lines)
        text = clean_text(text)

        if len(text.strip()) < 50:
            return None
        return text
    except Exception:
        return None


def worker_novel543(url, admin_email, metadata):
    generic_worker(url, admin_email, metadata, fetch_chapter_list_novel543, scrape_chapter_novel543)


# ==========================================
# 📋 تسجيل المواقع الصينية
# ==========================================

register_site(
    domain_patterns=['quanben.io'],
    name='Quanben (全本网)',
    language='chinese',
    fetch_metadata=fetch_metadata_quanben,
    fetch_chapters=fetch_chapter_list_quanben,
    fetch_content=scrape_chapter_quanben,
    worker=worker_quanben,
    status='blocked',
    notes='الموقع يعمل لكن يحجب IP مراكز البيانات (403). يعمل من Railway أو IP سكني.'
)

register_site(
    domain_patterns=['52shuku.net'],
    name='52shuku (52书库)',
    language='chinese',
    fetch_metadata=fetch_metadata_52shuku,
    fetch_chapters=fetch_chapter_list_52shuku,
    fetch_content=scrape_chapter_52shuku,
    worker=worker_52shuku,
    status='active',
    notes='تم إعادة كتابته بالكامل للتصميم الجديد: الكتاب /{تصنيف}/{id}.html والفصول صفحات متتابعة.'
)

register_site(
    domain_patterns=['erciyan.com'],
    name='ErCiYuan (二次元小说网)',
    language='chinese',
    fetch_metadata=fetch_metadata_erciyuan,
    fetch_chapters=fetch_chapter_list_erciyuan,
    fetch_content=scrape_chapter_erciyuan,
    worker=worker_erciyuan,
    status='blocked',
    notes='الموقع يعمل لكن WAF يعرض كابتشا لعناوين مراكز البيانات. يعمل من IP سكني.'
)

register_site(
    domain_patterns=['69shu.xyz', '69shu.com', '69shuba.com', '69shuba.cx'],
    name='69shu / 69shuba (69书吧)',
    language='chinese',
    fetch_metadata=fetch_metadata_69shu,
    fetch_chapters=fetch_chapter_list_69shu,
    fetch_content=scrape_chapter_69shu,
    worker=worker_69shu,
    status='active',
    notes='جديد (من LNReader)! دعم الدومينات المتعددة + ترميز GBK. Cloudflare يظهر أحياناً من IP السيرفرات.'
)

register_site(
    domain_patterns=['ixdzs8.com'],
    name='ixdzs8 (爱下电子书)',
    language='chinese',
    fetch_metadata=fetch_metadata_ixdzs8,
    fetch_chapters=fetch_chapter_list_ixdzs8,
    fetch_content=scrape_chapter_ixdzs8,
    worker=worker_ixdzs8,
    status='active',
    notes='جديد (من LNReader)! يعمل بالكامل - واجهة API للفصول + معالجة تحدي الأمان.'
)

register_site(
    domain_patterns=['linovel.net'],
    name='Linovel (轻小说文库)',
    language='chinese',
    fetch_metadata=fetch_metadata_linovel,
    fetch_chapters=fetch_chapter_list_linovel,
    fetch_content=scrape_chapter_linovel,
    worker=worker_linovel,
    status='active',
    notes='جديد (من LNReader)! يعمل بالكامل - بيانات + فصول + محتوى.'
)

register_site(
    domain_patterns=['tw.linovelib.com', 'linovelib.com', 'bilinovel.com'],
    name='Linovelib TW (轻小说文库繁體)',
    language='chinese',
    fetch_metadata=fetch_metadata_linovelib_tw,
    fetch_chapters=fetch_chapter_list_linovelib_tw,
    fetch_content=scrape_chapter_linovelib_tw,
    worker=worker_linovelib_tw,
    status='active',
    notes='جديد (من LNReader)! النسخة التقليدية (繁體) تعمل بالكامل عبر صفحة catalog.'
)

register_site(
    domain_patterns=['novel543.com'],
    name='Novel543 (稷下書院)',
    language='chinese',
    fetch_metadata=fetch_metadata_novel543,
    fetch_chapters=fetch_chapter_list_novel543,
    fetch_content=scrape_chapter_novel543,
    worker=worker_novel543,
    status='active',
    notes='جديد (من LNReader)! فهرس عبر /{id}/dir. Cloudflare متقلب أحياناً من IP السيرفرات.'
)
