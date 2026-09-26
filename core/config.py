# -*- coding: utf-8 -*-
"""
==========================================
⚙️ الإعدادات العامة للسكرابر (Shared Config)
==========================================
يحتوي على كل الإعدادات التي تحتاجها بقية الوحدات:
- مفاتيح الحماية
- روابط الخادم الرئيسي
- الكوكيز الخاصة
- حالة الجدولة التلقائية
"""

import os

# ==========================================
# 🔐 مفتاح سري لحماية الروابط (نفس القيمة القديمة تماماً)
# ==========================================
API_SECRET = os.environ.get(
    'API_SECRET',
    'Zeusndndjddnejdjdjdejekk29393838msmskxcm9239484jdndjdnddjj99292938338zeuslojdnejxxmejj82283849'
)

# ==========================================
# 🌐 رابط الخادم الرئيسي (Node.js backend)
# ==========================================
NODE_BACKEND_URL = os.environ.get('NODE_BACKEND_URL', 'https://c-production-6948.up.railway.app')

# ==========================================
# 🍪 إعدادات الكوكيز (تجاوز حماية تسجيل الدخول لمركز الروايات القديم)
# ==========================================
MARKAZ_COOKIES = os.environ.get(
    'MARKAZ_COOKIES',
    'wordpress_sec_198f6e9e82ba200a53325105f201ddc5=mikey%7C1771590380%7CKJphcZkhBFCpXyLUDrDcGPi9XmNOC47IPCSEHAPyfXS%7C5e8e596c5389b65f91a30668be6f16c7134b98b3ae55a007ed360594dd035527; cf_clearance=qYXkJIaj1IiaBKgi561_IQ.9oWgJ3fx10itfVR20lXY-1765278736-1.2.1.1-soYoRwUhDSq_.2cCoaJ22MPadmCmaQ0cW3AkfA1L97BJIbxQQro5hvpmuJxhQaT57TxfEW10l9gQYsmy5QgrwLsiWHScUWVvqYzZufRRYs9LIDPAhyxiOnL2Byevi12fb8iAZWttVNlqYWeKjH06tTp8bNhPx4dsmudPpIh0qzijEZhRk8lK6nWip1SeDFO2Of35W2rBKDEtjidGFyIj1RU3B7Xt.4CVoQbE9pGFaS8gFTMOp.0qmMMiz1UmHoFc; wpmanga-body-contrast=light; wpmanga-reading-history=W3siaWQiOjEyODE3LCJjIjoiMzEzMDgiLCJwIjoxLCJpIjoiIiwidCI6MTc2ODEwMTY3MH1d; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2026-02-06%2012%3A25%3A57%7C%7C%7Cep%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fwww.bing.com%2F; sbjs_first_add=fd%3D2026-02-06%2012%3A25%3A57%7C%7C%7Cep%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fwww.bing.com%2F; sbjs_current=typ%3Dreferral%7C%7C%7Csrc%3Dbing.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7Cid%3D%28none%29%7C%7Cplt%3D%28none%29%7C%7Cfmt%3D%28none%29%7C%7Ctct%3D%28none%29; sbjs_first=typ%3Dreferral%7C%7C%7Csrc%3Dbing.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7Cid%3D%28none%29%7C%7Cplt%3D%28none%29%7C%7Cfmt%3D%28none%29%7C%7Ctct%3D%28none%29; sbjs_udata=vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%206.2%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F109.0.0.0%20Safari%2F537.36%20Edg%2F109.0.1518.140; wordpress_test_cookie=WP%20Cookie%20check; _lscache_vary=8d8d3777c370b0211addc5b0a9411cd9; wordpress_logged_in_198f6e9e82ba200a53325105f201ddc5=mikey%7C1771590380%7CKJphcZkhBFCpXyLUDrDcGPi9XmNOC47IPCSEHAPyfXS%7Cb7d906dce3f0b160d5c2f585bfec331fe7d0cc3e4640a74945cc619df837e5c9; sbjs_session=pgs%3D2%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%3Fnsl_bypass_cache%3D74d71305203b9ce18787813c87e33f8c'
)

# ==========================================
# 🔄 حالة الجدولة التلقائية العامة (Scheduler)
# ==========================================
SCHEDULER_CONFIG = {
    'active': False,
    'interval_seconds': 86400,  # الافتراضي 24 ساعة
    'next_run': 0,
    'last_run': 0,
    'status': 'idle',
    'admin_email': 'system@auto'
}
