"""
DEEP TEST: Turkish character handling in Contabo proxy upload
Tests the ACTUAL production function _upload_to_contabo from s3_uploader.py
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, r"E:\DDSFocusPro_v1.7.1_Build_corrected_dns")

print("=" * 70)
print("DEEP TEST: Turkish Character Handling in Contabo Proxy Upload")
print("=" * 70)

# ========================================
# TEST 1: Import the actual production module
# ========================================
print("\n[TEST 1] Importing production s3_uploader module...")
try:
    from moduller.moduller.s3_uploader import (
        _upload_to_contabo, 
        _generate_contabo_presigned_url,
        _CONTABO_PROXY_URL,
        _CONTABO_PROXY_TOKEN,
        _CONTABO_BUCKET,
        _CONTABO_HOSTNAME
    )
    print("  OK - Module imported")
    print(f"  Proxy URL: {_CONTABO_PROXY_URL}")
    print(f"  Bucket: {_CONTABO_BUCKET}")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# ========================================
# TEST 2: Verify certifi + ssl works
# ========================================
print("\n[TEST 2] Testing certifi + ssl context...")
try:
    import ssl, certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
    print(f"  OK - certifi path: {certifi.where()}")
    print(f"  OK - cert file exists: {os.path.exists(certifi.where())}")
    print(f"  OK - SSL context created")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# ========================================
# TEST 3: Verify urllib.parse.quote handles Turkish chars
# ========================================
print("\n[TEST 3] Testing URL encoding of Turkish characters...")
import urllib.parse

test_strings = {
    "lowercase dotless i": "\u0131",          # ı
    "u with umlaut": "\u00fc",                # ü  
    "o with umlaut": "\u00f6",                # ö
    "c with cedilla": "\u00e7",               # ç
    "s with cedilla": "\u015f",               # ş
    "g with breve": "\u011f",                 # ğ
    "uppercase I with dot": "\u0130",         # İ
    "uppercase G with breve": "\u011e",       # Ğ
    "uppercase S with cedilla": "\u015e",     # Ş
    "uppercase C with cedilla": "\u00c7",     # Ç
    "uppercase O with umlaut": "\u00d6",      # Ö
    "uppercase U with umlaut": "\u00dc",      # Ü
    "full task name": "DDS_MART_2026_Sanal_Asistanl\u0131k_S\u00fcreci_",
    "mixed Turkish": "G\u00f6rev_\u00c7al\u0131\u015fma_S\u00fcreci_\u0130\u015f",
    "Arabic mixed": "\u0645\u0634\u0631\u0648\u0639_test",
    "Urdu mixed": "\u0627\u0631\u062f\u0648_\u0679\u06cc\u0633\u0679",
    "emoji (extreme)": "task_\U0001f600_name",
    "pure ASCII": "normal_task_name",
    "spaces replaced": "Task_With_Many_Words",
}

all_ok = True
for name, val in test_strings.items():
    encoded = urllib.parse.quote(val, safe='/')
    is_ascii = encoded.isascii()
    status = "OK" if is_ascii else "FAIL"
    if not is_ascii:
        all_ok = False
    print(f"  [{status}] {name}: {val} -> {encoded} (ASCII: {is_ascii})")

if all_ok:
    print("  ALL ENCODING TESTS PASSED")
else:
    print("  SOME ENCODING TESTS FAILED!")
    sys.exit(1)

# ========================================
# TEST 4: Verify presigned URL generation with Turkish chars
# ========================================
print("\n[TEST 4] Presigned URL generation with Turkish key...")
try:
    turkish_key = "users_screenshots/2026-03-25/tuysuzesma10_at_gmail.com/DDS_MART_2026_Sanal_Asistanl\u0131k_S\u00fcreci_/2026-03-25_19-01-49.webp"
    url = _generate_contabo_presigned_url(turkish_key, "image/webp")
    print(f"  OK - Presigned URL generated ({len(url)} chars)")
    print(f"  Contains eu2.contabostorage.com: {'eu2.contabostorage.com' in url}")
    print(f"  Contains X-Amz-Signature: {'X-Amz-Signature' in url}")
    
    # Now quote it like production code does
    safe_url = urllib.parse.quote(url, safe=':/?&=@%+')
    print(f"  Quoted presigned URL is ASCII: {safe_url.isascii()}")
    if not safe_url.isascii():
        print("  FAILED - presigned URL not ASCII after quoting!")
        sys.exit(1)
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# ========================================
# TEST 5: End-to-end upload with REAL Turkish task names
# ========================================
print("\n[TEST 5] End-to-end uploads through Cloudflare proxy...")

test_uploads = [
    {
        "name": "Exact error case from Esma",
        "key": "users_screenshots/2026-03-25/tuysuzesma10_at_gmail.com/DDS_MART_2026_Sanal_Asistanl\u0131k_S\u00fcreci_/test_deep_1.webp",
        "content_type": "image/webp",
    },
    {
        "name": "All Turkish lowercase",
        "key": "users_screenshots/2026-03-25/test_deep/\u00e7al\u0131\u015fma_g\u00f6rev_s\u00fcreci_\u011f\u00fc\u00f6/test_deep_2.webp",
        "content_type": "image/webp",
    },
    {
        "name": "All Turkish uppercase", 
        "key": "users_screenshots/2026-03-25/test_deep/\u00c7ALI\u015eMA_G\u00d6REV_S\u00dcREC\u0130_\u011e\u00dc\u00d6/test_deep_3.webp",
        "content_type": "image/webp",
    },
    {
        "name": "JSON log with Turkish task",
        "key": "users_logs/2026-03-25/test_deep/G\u00f6rev_\u00c7al\u0131\u015fma_\u0130\u015f/activity_log.json",
        "content_type": "application/json",
    },
    {
        "name": "Mixed Turkish + numbers + underscores",
        "key": "users_screenshots/2026-03-25/test_deep/2026_\u0130\u015f_Takip_G\u00f6rev_1234_\u00dc\u00e7\u00fcnc\u00fc/test_deep_5.webp",
        "content_type": "image/webp",
    },
    {
        "name": "Very long Turkish task name",
        "key": "users_screenshots/2026-03-25/test_deep/Bu_\u00c7ok_Uzun_Bir_G\u00f6rev_Ad\u0131_\u00d6zel_Karakterler_\u0130\u00e7eren_\u015e\u00fc_\u011e\u00fc_\u00c7\u00f6_Test/test_deep_6.webp",
        "content_type": "image/webp",
    },
    {
        "name": "Pure ASCII (control case)",
        "key": "users_screenshots/2026-03-25/test_deep/Normal_ASCII_Task/test_deep_7.webp",
        "content_type": "image/webp",
    },
]

passed = 0
failed = 0

for test in test_uploads:
    print(f"\n  --- {test['name']} ---")
    print(f"  Key: {test['key']}")
    
    body = f"Deep test: {test['name']}".encode('utf-8')
    
    try:
        result = _upload_to_contabo(body, test['key'], test['content_type'], max_retries=1)
        if result:
            print(f"  RESULT: PASSED - {result}")
            passed += 1
        else:
            print(f"  RESULT: FAILED - returned None")
            failed += 1
    except Exception as e:
        print(f"  RESULT: FAILED - {type(e).__name__}: {e}")
        failed += 1

# ========================================
# SUMMARY
# ========================================
print("\n" + "=" * 70)
print(f"FINAL RESULTS: {passed} passed, {failed} failed out of {len(test_uploads)}")
if failed == 0:
    print("ALL TESTS PASSED - Turkish characters fully handled!")
    print("Safe to build and deploy.")
else:
    print(f"WARNING: {failed} test(s) FAILED - DO NOT DEPLOY!")
print("=" * 70)
