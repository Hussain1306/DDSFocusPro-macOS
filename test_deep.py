"""
Deep Contabo proxy test — 7 scenarios covering all edge cases.
Uses test@gmail.com as requested.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import ssl, certifi, urllib.request, urllib.parse, boto3, time
from botocore.config import Config

ACCESS_KEY = "6ea825cf4e68a7087af3d57f667dd66e"
SECRET_KEY = "9cd10c8e7f0a4e32b8ba9cc044ba8027"
PROXY_URL = "https://contabo-proxy.ddsfocuspro.workers.dev"
PROXY_TOKEN = "ASD79138246asd#"

ssl_ctx = ssl.create_default_context(cafile=certifi.where())

client = boto3.client('s3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    endpoint_url="https://eu2.contabostorage.com",
    region_name="eu2",
    config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4')
)

tests = [
    ("1-Turkish-lowercase",    "users_screenshots/2026-03-25/test_at_gmail.com/Sanal_Asistanl\u0131k_S\u00fcreci/test.webp", "image/webp"),
    ("2-Turkish-uppercase",    "users_screenshots/2026-03-25/test_at_gmail.com/\u00c7ALI\u015eMA_\u0130\u015e_TAK\u0130P/test.webp", "image/webp"),
    ("3-Turkish-mixed-long",   "users_screenshots/2026-03-25/test_at_gmail.com/DDS_MART_2026_Sanal_Asistanl\u0131k_S\u00fcreci_G\u00f6revi/2026-03-25_19-01-49.webp", "image/webp"),
    ("4-Pure-ASCII",           "users_screenshots/2026-03-25/test_at_gmail.com/Normal_Task_Name/test.webp", "image/webp"),
    ("5-JSON-log",             "users_logs/2026-03-25/test_at_gmail.com/G\u00fcnl\u00fck_Rapor/daily_log.json", "application/json"),
    ("6-Activity-data",        "logs/2026-03-25/test_at_gmail.com/\u00d6\u011fle_Molasi_Takip/activity.json", "application/json"),
    ("7-Special-chars",        "users_screenshots/2026-03-25/test_at_gmail.com/Task_(v2.1)_Final-Rev/test.webp", "image/webp"),
]

passed = 0
failed = 0

for name, key, ctype in tests:
    print(f"\n{'='*60}")
    print(f"TEST {name}")
    print(f"  Key: {key}")
    
    # Step A: Generate presigned URL
    try:
        presigned_url = client.generate_presigned_url('put_object',
            Params={'Bucket': 'focuspro', 'Key': key, 'ContentType': ctype},
            ExpiresIn=300, HttpMethod='PUT'
        )
        print(f"  [A] Presigned URL generated ({len(presigned_url)} chars)")
    except Exception as e:
        print(f"  [A] FAILED generating presigned URL: {e}")
        failed += 1
        continue

    # Step B: URL-encode
    safe_key = urllib.parse.quote(key, safe='/')
    proxy_url = f"{PROXY_URL}/focuspro/{safe_key}"
    safe_presigned = urllib.parse.quote(presigned_url, safe=':/?&=@%+')
    is_ascii = proxy_url.isascii() and safe_presigned.isascii()
    print(f"  [B] URL-encoded. All ASCII? {is_ascii}")
    if not is_ascii:
        print(f"  [B] FAILED — non-ASCII in encoded URL!")
        failed += 1
        continue

    # Step C: Build request
    body = f"Deep test: {name} at {time.strftime('%H:%M:%S')}".encode('utf-8')
    req = urllib.request.Request(proxy_url, data=body, method='PUT')
    req.add_header('Content-Type', ctype)
    req.add_header('X-Proxy-Token', PROXY_TOKEN)
    req.add_header('X-Target-Url', safe_presigned)
    req.add_header('User-Agent', 'DDSFocusPro/1.7')
    print(f"  [C] Request built ({len(body)} bytes)")

    # Step D: Upload with SSL context
    try:
        t0 = time.time()
        resp = urllib.request.urlopen(req, timeout=60, context=ssl_ctx)
        dur = time.time() - t0
        print(f"  [D] HTTP {resp.status} in {dur:.2f}s — PASSED")
        passed += 1
    except Exception as e:
        print(f"  [D] FAILED: {type(e).__name__}: {e}")
        failed += 1

print(f"\n{'='*60}")
print(f"FINAL: {passed}/{len(tests)} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"WARNING: {failed} FAILED!")
