from pathlib import Path
p=Path("mcai/server.py"); s=p.read_text(encoding="utf-8")
s=s.replace('''        ip = self.client_address[0]''','''        ip = self.client_address[0]
        # 经过隧道/反向代理时，记录真实来源
        forwarded = (self.headers.get("CF-Connecting-IP")
                     or (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip())
        if forwarded:
            ip = forwarded''')
p.write_text(s,encoding="utf-8")
print("forwarded ip logging added")