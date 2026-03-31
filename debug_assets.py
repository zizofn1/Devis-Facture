import urllib.request, json
url = 'https://api.github.com/repos/zizofn1/Devis-Facture/releases?per_page=5'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as r:
    data = json.loads(r.read().decode())
    for item in data:
        print(f"Release: {item.get('tag_name')}")
        for asset in item.get('assets', []):
            print(f"  Asset: {asset.get('name')} | URL: {asset.get('browser_download_url')}")
