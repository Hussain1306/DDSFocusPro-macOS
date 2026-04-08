import sys
sys.stdout.reconfigure(encoding='utf-8')

# Check primary s3_uploader
with open('moduller/s3_uploader.py', 'r', encoding='utf-8') as f:
    src = f.read()

checks = [
    ('import certifi', 'import certifi as _certifi' in src),
    ('ssl context created', '_ssl.create_default_context(cafile=_certifi.where())' in src),
    ('context=_ssl_ctx in urlopen', 'context=_ssl_ctx' in src),
    ('quote for contabo_key', '_urllib_parse.quote(contabo_key' in src),
    ('quote for presigned_url', '_urllib_parse.quote(presigned_url' in src),
    ('User-Agent header', 'DDSFocusPro/1.7' in src),
    ('PROXY_URL constant', 'contabo-proxy.ddsfocuspro.workers.dev' in src),
]

print('=== PRIMARY s3_uploader.py ===')
all_ok = True
for name, ok in checks:
    status = 'OK' if ok else 'MISSING'
    if not ok:
        all_ok = False
    print(f'  [{status}] {name}')

# Check duplicate
with open('moduller/moduller/s3_uploader.py', 'r', encoding='utf-8') as f:
    src2 = f.read()

checks2 = [
    ('import certifi', 'import certifi as _certifi' in src2),
    ('ssl context', '_ssl.create_default_context(cafile=_certifi.where())' in src2),
    ('context=_ssl_ctx', 'context=_ssl_ctx' in src2),
    ('quote contabo_key', '_urllib_parse.quote(contabo_key' in src2),
    ('quote presigned_url', '_urllib_parse.quote(presigned_url' in src2),
]

print()
print('=== DUPLICATE s3_uploader.py ===')
for name, ok in checks2:
    status = 'OK' if ok else 'MISSING'
    if not ok:
        all_ok = False
    print(f'  [{status}] {name}')

# Check spec files
with open('connector.spec', 'r', encoding='utf-8') as f:
    cs = f.read()
with open('DDSFocusPro-GUI.spec', 'r', encoding='utf-8') as f:
    gs = f.read()

print()
print('=== SPEC FILES ===')
c_ok = "'certifi'" in cs
g_ok = "'certifi'" in gs
print(f"  [{'OK' if c_ok else 'MISSING'}] connector.spec hiddenimports certifi")
print(f"  [{'OK' if g_ok else 'MISSING'}] DDSFocusPro-GUI.spec hiddenimports certifi")
if not c_ok or not g_ok:
    all_ok = False

# Check certifi actually works
import certifi
import ssl
ctx = ssl.create_default_context(cafile=certifi.where())
print()
print(f'=== RUNTIME CHECK ===')
print(f'  [OK] certifi.where() = {certifi.where()}')
print(f'  [OK] SSL context created with {len(ctx.get_ca_certs())} CA certs')

print()
if all_ok:
    print('ALL CHECKS PASSED')
else:
    print('SOME CHECKS FAILED')
