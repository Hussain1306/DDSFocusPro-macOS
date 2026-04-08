#!/usr/bin/env python3
"""
DEEP ADVERSARIAL TEST SUITE for Contabo Proxy Upload
=====================================================
Tests happy paths, edge cases, error handling, and failure modes.
30 tests covering every realistic and unrealistic scenario.
"""
import sys, os, time, ssl, json, hashlib
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import urllib.request
import urllib.parse
import urllib.error
import certifi
import boto3
from botocore.config import Config

# ── Constants (identical to production code) ──
PROXY_URL   = "https://contabo-proxy.ddsfocuspro.workers.dev"
PROXY_TOKEN = "ASD79138246asd#"
ACCESS_KEY  = "6ea825cf4e68a7087af3d57f667dd66e"
SECRET_KEY  = "9cd10c8e7f0a4e32b8ba9cc044ba8027"
HOSTNAME    = "eu2.contabostorage.com"
BUCKET      = "focuspro"
REGION      = "eu2"

ssl_ctx = ssl.create_default_context(cafile=certifi.where())

results = []
total_start = time.time()

def gen_presigned(key, ct="application/octet-stream", expires=300):
    client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        endpoint_url=f"https://{HOSTNAME}",
        region_name=REGION,
        config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4')
    )
    return client.generate_presigned_url(
        'put_object',
        Params={'Bucket': BUCKET, 'Key': key, 'ContentType': ct},
        ExpiresIn=expires
    )

def upload_via_proxy(data_bytes, key, ct="application/octet-stream"):
    """Exact replica of production _upload_to_contabo logic (single attempt)."""
    presigned = gen_presigned(key, ct)
    safe_key = urllib.parse.quote(key, safe='/')
    proxy_url = f"{PROXY_URL}/{BUCKET}/{safe_key}"
    req = urllib.request.Request(proxy_url, data=data_bytes, method='PUT')
    req.add_header('Content-Type', ct)
    req.add_header('X-Proxy-Token', PROXY_TOKEN)
    req.add_header('X-Target-Url', urllib.parse.quote(presigned, safe=':/?&=@%+'))
    req.add_header('User-Agent', 'DDSFocusPro/1.7')
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60, context=ssl_ctx) as resp:
        body = resp.read()
        return resp.status, time.time() - t0, body

def run_test(num, name, func, expect_pass=True):
    """Run a single test, catch exceptions, record result."""
    print(f"\n{'='*70}")
    print(f"TEST {num}: {name}")
    print(f"  Expected: {'PASS (HTTP 200)' if expect_pass else 'FAIL (error/rejection)'}")
    try:
        status, dur, body = func()
        passed = (status in (200, 201)) == expect_pass
        if expect_pass:
            print(f"  Result: HTTP {status} in {dur:.2f}s")
        else:
            print(f"  Result: HTTP {status} (expected rejection but got success)")
        tag = "PASS" if passed else "FAIL"
        print(f"  >>> {tag}")
        results.append((num, name, tag, f"HTTP {status}, {dur:.2f}s"))
    except Exception as e:
        etype = type(e).__name__
        emsg = str(e)[:200]
        if not expect_pass:
            print(f"  Result: {etype}: {emsg}")
            print(f"  >>> PASS (correctly rejected/errored)")
            results.append((num, name, "PASS", f"{etype}: {emsg[:80]}"))
        else:
            print(f"  Result: {etype}: {emsg}")
            print(f"  >>> FAIL (unexpected error)")
            results.append((num, name, "FAIL", f"{etype}: {emsg[:80]}"))

# ══════════════════════════════════════════════════════════
# CATEGORY 1: TURKISH CHARACTER TESTS (the original bug)
# ══════════════════════════════════════════════════════════

def test_01():
    key = "test_deep/test_at_gmail.com/Asistanlık_Süreci/shot.webp"
    data = b"x" * 42
    return upload_via_proxy(data, key)

def test_02():
    key = "test_deep/test_at_gmail.com/ÇALIŞMA_İŞ_TAKİP_PROGRAMI/shot.webp"
    data = b"x" * 42
    return upload_via_proxy(data, key)

def test_03():
    key = "test_deep/test_at_gmail.com/Öğle_arası_değerlendirme_günlüğü/rapor.json"
    data = json.dumps({"görev": "Öğle molası", "süre": 30, "çalışan": "İsmail"}).encode('utf-8')
    return upload_via_proxy(data, key, "application/json")

def test_04():
    # Every single Turkish special char individually
    key = "test_deep/test_at_gmail.com/ç_ğ_ı_ö_ş_ü_Ç_Ğ_İ_Ö_Ş_Ü/test.txt"
    data = b"Turkish chars test"
    return upload_via_proxy(data, key)

def test_05():
    # Real-world Turkish task name from error log: Asistanlık_Süreci
    key = "users_screenshots/2026-03-25/test_at_gmail.com/Asistanlık_Süreci/2026-03-25_14-30-00.webp"
    data = b"\x00" * 100  # fake webp bytes
    return upload_via_proxy(data, key, "image/webp")

# ══════════════════════════════════════════════════════════
# CATEGORY 2: OTHER UNICODE / INTERNATIONAL CHARACTERS
# ══════════════════════════════════════════════════════════

def test_06():
    # Arabic
    key = "test_deep/test_at_gmail.com/مشروع_العمل/report.json"
    return upload_via_proxy(b'{"test": true}', key, "application/json")

def test_07():
    # Chinese
    key = "test_deep/test_at_gmail.com/工作项目_测试/data.json"
    return upload_via_proxy(b'{"test": true}', key, "application/json")

def test_08():
    # Russian
    key = "test_deep/test_at_gmail.com/Рабочий_Проект/file.txt"
    return upload_via_proxy(b"Russian test", key)

def test_09():
    # Japanese
    key = "test_deep/test_at_gmail.com/作業プロジェクト/file.txt"
    return upload_via_proxy(b"Japanese test", key)

def test_10():
    # Korean
    key = "test_deep/test_at_gmail.com/작업_프로젝트/file.txt"
    return upload_via_proxy(b"Korean test", key)

def test_11():
    # German umlauts + French accents mixed
    key = "test_deep/test_at_gmail.com/Ärger_über_café_résumé/file.txt"
    return upload_via_proxy(b"European test", key)

# ══════════════════════════════════════════════════════════
# CATEGORY 3: EDGE CASE PATHS
# ══════════════════════════════════════════════════════════

def test_12():
    # Spaces in path (should be encoded to %20)
    key = "test_deep/test_at_gmail.com/Task With Spaces/file name.txt"
    return upload_via_proxy(b"spaces test", key)

def test_13():
    # Special chars: parentheses, dots, hyphens, underscores, plus
    key = "test_deep/test_at_gmail.com/Task_(v2.1)_Final-Rev+hotfix/file.txt"
    return upload_via_proxy(b"special chars test", key)

def test_14():
    # Very long path (250+ chars)
    long_seg = "A" * 200
    key = f"test_deep/test_at_gmail.com/{long_seg}/file.txt"
    return upload_via_proxy(b"long path test", key)

def test_15():
    # Path with consecutive slashes (unusual but possible)
    key = "test_deep//test_at_gmail.com///double_slash/file.txt"
    return upload_via_proxy(b"double slash test", key)

def test_16():
    # Path with @ symbol (emails have this)
    key = "test_deep/user@domain.com/task/file.txt"
    return upload_via_proxy(b"at sign test", key)

def test_17():
    # Path with # (hash) - tricky for URLs
    key = "test_deep/test_at_gmail.com/Task#123/file.txt"
    data = b"hash test"
    presigned = gen_presigned(key, "application/octet-stream")
    safe_key = urllib.parse.quote(key, safe='/')
    proxy_url = f"{PROXY_URL}/{BUCKET}/{safe_key}"
    req = urllib.request.Request(proxy_url, data=data, method='PUT')
    req.add_header('Content-Type', 'application/octet-stream')
    req.add_header('X-Proxy-Token', PROXY_TOKEN)
    req.add_header('X-Target-Url', urllib.parse.quote(presigned, safe=':/?&=@%+'))
    req.add_header('User-Agent', 'DDSFocusPro/1.7')
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60, context=ssl_ctx) as resp:
        body = resp.read()
        return resp.status, time.time() - t0, body

# ══════════════════════════════════════════════════════════
# CATEGORY 4: CONTENT TYPE VARIATIONS
# ══════════════════════════════════════════════════════════

def test_18():
    # image/webp (real screenshot upload)
    key = "test_deep/test_at_gmail.com/Normal_Task/screenshot.webp"
    return upload_via_proxy(b"\x00\x01\x02" * 100, key, "image/webp")

def test_19():
    # application/json (log upload)
    key = "test_deep/test_at_gmail.com/Normal_Task/daily_log.json"
    data = json.dumps({"timestamp": "2026-03-25T14:00:00", "tasks": [{"name": "Test", "duration": 60}]}).encode('utf-8')
    return upload_via_proxy(data, key, "application/json")

def test_20():
    # text/plain
    key = "test_deep/test_at_gmail.com/Normal_Task/notes.txt"
    return upload_via_proxy(b"plain text content here\nline 2\nline 3", key, "text/plain")

# ══════════════════════════════════════════════════════════
# CATEGORY 5: DATA SIZE EDGE CASES
# ══════════════════════════════════════════════════════════

def test_21():
    # Empty body (0 bytes) — should still succeed
    key = "test_deep/test_at_gmail.com/empty_test/empty.txt"
    return upload_via_proxy(b"", key)

def test_22():
    # 1 byte
    key = "test_deep/test_at_gmail.com/tiny_test/one_byte.txt"
    return upload_via_proxy(b"X", key)

def test_23():
    # ~100KB (typical screenshot)
    key = "test_deep/test_at_gmail.com/medium_test/100kb.webp"
    return upload_via_proxy(os.urandom(100_000), key, "image/webp")

# ══════════════════════════════════════════════════════════
# CATEGORY 6: SECURITY / ERROR HANDLING (SHOULD FAIL)
# ══════════════════════════════════════════════════════════

def test_24():
    # WRONG proxy token — should be rejected by Worker
    key = "test_deep/test_at_gmail.com/wrong_token/file.txt"
    presigned = gen_presigned(key)
    safe_key = urllib.parse.quote(key, safe='/')
    proxy_url = f"{PROXY_URL}/{BUCKET}/{safe_key}"
    req = urllib.request.Request(proxy_url, data=b"wrong token test", method='PUT')
    req.add_header('Content-Type', 'application/octet-stream')
    req.add_header('X-Proxy-Token', 'WRONG_TOKEN_12345')  # <-- WRONG
    req.add_header('X-Target-Url', urllib.parse.quote(presigned, safe=':/?&=@%+'))
    req.add_header('User-Agent', 'DDSFocusPro/1.7')
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
        return resp.status, time.time() - t0, resp.read()

def test_25():
    # NO proxy token header — should be rejected
    key = "test_deep/test_at_gmail.com/no_token/file.txt"
    presigned = gen_presigned(key)
    safe_key = urllib.parse.quote(key, safe='/')
    proxy_url = f"{PROXY_URL}/{BUCKET}/{safe_key}"
    req = urllib.request.Request(proxy_url, data=b"no token test", method='PUT')
    req.add_header('Content-Type', 'application/octet-stream')
    # No X-Proxy-Token header!
    req.add_header('X-Target-Url', urllib.parse.quote(presigned, safe=':/?&=@%+'))
    req.add_header('User-Agent', 'DDSFocusPro/1.7')
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
        return resp.status, time.time() - t0, resp.read()

def test_26():
    # Target URL pointing to NON-Contabo domain (should be rejected by Worker)
    key = "test_deep/test_at_gmail.com/bad_target/file.txt"
    safe_key = urllib.parse.quote(key, safe='/')
    proxy_url = f"{PROXY_URL}/{BUCKET}/{safe_key}"
    req = urllib.request.Request(proxy_url, data=b"bad target test", method='PUT')
    req.add_header('Content-Type', 'application/octet-stream')
    req.add_header('X-Proxy-Token', PROXY_TOKEN)
    req.add_header('X-Target-Url', 'https://evil.example.com/steal-data')  # <-- NOT Contabo
    req.add_header('User-Agent', 'DDSFocusPro/1.7')
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
        return resp.status, time.time() - t0, resp.read()

def test_27():
    # GET method instead of PUT — Worker should reject
    key = "test_deep/test_at_gmail.com/get_test/file.txt"
    presigned = gen_presigned(key)
    safe_key = urllib.parse.quote(key, safe='/')
    proxy_url = f"{PROXY_URL}/{BUCKET}/{safe_key}"
    req = urllib.request.Request(proxy_url, method='GET')  # <-- wrong method
    req.add_header('X-Proxy-Token', PROXY_TOKEN)
    req.add_header('X-Target-Url', urllib.parse.quote(presigned, safe=':/?&=@%+'))
    req.add_header('User-Agent', 'DDSFocusPro/1.7')
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
        return resp.status, time.time() - t0, resp.read()

# ══════════════════════════════════════════════════════════
# CATEGORY 7: SSL VERIFICATION
# ══════════════════════════════════════════════════════════

def test_28():
    # SSL with certifi context (should work) — same as all above but explicit
    key = "test_deep/test_at_gmail.com/ssl_test/cert_ok.txt"
    return upload_via_proxy(b"ssl certifi test", key)

def test_29():
    # SSL WITHOUT certifi (bare default) — tests if system certs work too
    # This is informational: in PyInstaller, this WOULD fail
    key = "test_deep/test_at_gmail.com/ssl_test/no_certifi.txt"
    presigned = gen_presigned(key)
    safe_key = urllib.parse.quote(key, safe='/')
    proxy_url = f"{PROXY_URL}/{BUCKET}/{safe_key}"
    req = urllib.request.Request(proxy_url, data=b"no certifi test", method='PUT')
    req.add_header('Content-Type', 'application/octet-stream')
    req.add_header('X-Proxy-Token', PROXY_TOKEN)
    req.add_header('X-Target-Url', urllib.parse.quote(presigned, safe=':/?&=@%+'))
    req.add_header('User-Agent', 'DDSFocusPro/1.7')
    t0 = time.time()
    # Use default SSL context (no certifi) — may or may not work depending on system
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, time.time() - t0, resp.read()

# ══════════════════════════════════════════════════════════
# CATEGORY 8: REALISTIC PRODUCTION SCENARIOS
# ══════════════════════════════════════════════════════════

def test_30():
    # Simulate a full realistic scenario: screenshot with Turkish task + correct content-type
    key = "users_screenshots/2026-03-25/test_at_gmail.com/Müşteri_İlişkileri_Yönetimi/2026-03-25_15-45-22.webp"
    # Fake but realistic-sized webp
    fake_webp = os.urandom(50_000)
    return upload_via_proxy(fake_webp, key, "image/webp")


# ══════════════════════════════════════════════════════════
# RUN ALL TESTS
# ══════════════════════════════════════════════════════════

tests = [
    # (num, name, func, expect_pass)
    (1,  "Turkish lowercase: ıüöçşğ in path",          test_01, True),
    (2,  "Turkish uppercase: ÇŞİ in path",             test_02, True),
    (3,  "Turkish JSON body + path",                    test_03, True),
    (4,  "Every Turkish special char individually",     test_04, True),
    (5,  "Real error-log path: Asistanlık_Süreci",     test_05, True),
    (6,  "Arabic characters in path",                   test_06, True),
    (7,  "Chinese characters in path",                  test_07, True),
    (8,  "Russian characters in path",                  test_08, True),
    (9,  "Japanese characters in path",                 test_09, True),
    (10, "Korean characters in path",                   test_10, True),
    (11, "German + French accented chars",              test_11, True),
    (12, "Spaces in path segments",                     test_12, True),
    (13, "Special chars: () . - _ +",                   test_13, True),
    (14, "Very long path (250+ chars)",                 test_14, True),
    (15, "Consecutive double slashes in path",          test_15, True),
    (16, "@ symbol in path (email)",                    test_16, True),
    (17, "# hash in path (URL-tricky)",                 test_17, True),
    (18, "Content-Type: image/webp",                    test_18, True),
    (19, "Content-Type: application/json",              test_19, True),
    (20, "Content-Type: text/plain",                    test_20, True),
    (21, "Empty body (0 bytes)",                        test_21, True),
    (22, "Tiny body (1 byte)",                          test_22, True),
    (23, "Medium body (~100KB)",                        test_23, True),
    (24, "WRONG proxy token (should reject)",           test_24, False),
    (25, "NO proxy token (should reject)",              test_25, False),
    (26, "Non-Contabo target URL (should reject)",      test_26, False),
    (27, "GET method instead of PUT (should reject)",   test_27, False),
    (28, "SSL with certifi (explicit check)",           test_28, True),
    (29, "SSL without certifi (system certs)",          test_29, True),  # informational
    (30, "Full realistic Turkish screenshot upload",    test_30, True),
]

print("=" * 70)
print("DEEP ADVERSARIAL TEST SUITE — DDSFocusPro Contabo Proxy Upload")
print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Proxy: {PROXY_URL}")
print(f"SSL CA certs loaded: {len(ssl_ctx.get_ca_certs())}")
print(f"Total tests: {len(tests)}")
print("=" * 70)

for num, name, func, expect_pass in tests:
    run_test(num, name, func, expect_pass)

# ── Summary ──
total_dur = time.time() - total_start
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

passed = [r for r in results if r[2] == "PASS"]
failed = [r for r in results if r[2] == "FAIL"]

for num, name, tag, detail in results:
    icon = "OK" if tag == "PASS" else "XX"
    print(f"  [{icon}] Test {num:2d}: {name} — {detail}")

print(f"\n  Total: {len(results)}/{len(tests)} run")
print(f"  Passed: {len(passed)}")
print(f"  Failed: {len(failed)}")
print(f"  Duration: {total_dur:.1f}s")
print()

if failed:
    print("FAILED TESTS:")
    for num, name, tag, detail in failed:
        print(f"  Test {num}: {name} — {detail}")
    print("\n*** SOME TESTS FAILED ***")
    sys.exit(1)
else:
    print("*** ALL 30 TESTS PASSED ***")
    sys.exit(0)
