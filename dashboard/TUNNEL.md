# Remote dashboard access over Cloudflare Tunnel

How to reach this dashboard from another machine or from home without exposing
the weighbridge to the plant LAN.

## What stays local, always

| Thing | Where it listens | Exposed to the Internet? |
|---|---|---|
| Dashboard UI + API | `127.0.0.1:8000` | yes, but only through the tunnel and only with a token |
| OPC-UA server (`pso`) | `127.0.0.1:5501` | **no** |
| `weighbridge.db` | file | **no** |
| `dashboard/tcp_status.json` | file | **no** |

The dashboard process is the only thing that talks to OPC-UA. Nothing here
proxies port 5501, and `dashboard/static/` is never served, so the database and
the TCP beacon cannot be downloaded over HTTP.

## 1. One-time setup

```bash
# a) Generate a token and keep it secret (32+ chars)
python -c "import secrets;print(secrets.token_urlsafe(32))"

# b) Create dashboard/.env  (this file is git-ignored)
cp dashboard/.env.example dashboard/.env
```

Then edit `dashboard/.env`:

```ini
DASHBOARD_AUTH_TOKEN=<paste the generated token>
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8000
```

Leave `DASHBOARD_HOST` at `127.0.0.1`. cloudflared runs on this machine, so it
can reach loopback while the plant LAN cannot. This is what removed the old
`0.0.0.0` bind, which had put an OPC-UA **write** proxy on every interface.

**Behaviour change to be aware of:** other machines on the LAN can no longer
open `http://<this-ip>:8000`. Only this PC can. If you truly need LAN access,
set `DASHBOARD_HOST=0.0.0.0` — the app then refuses to start without a token,
which is the intended fail-closed behaviour.

## 2. Cloudflare side (once per hostname)

```bash
cloudflared tunnel login
cloudflared tunnel create weighbridge
```

`config.yml` in the cloudflared config directory:

```yaml
tunnel: weighbridge
credentials-file: C:\Users\<user>\.cloudflared\<TUNNEL-ID>.json

ingress:
  - hostname: weighbridge.example.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

Note the service is `http://127.0.0.1:8000` — the dashboard itself. Never add
`5501` here.

In the Cloudflare dashboard: **Zero Trust → Networks → Tunnels**, add the
hostname, and enable **SSL/TLS → Full (strict)** with an origin certificate, or
**Full** if you rely on Cloudflare's edge certificate.

Then run it as a Windows service so it survives reboots:

```powershell
cloudflared service install
# token-based, if you did not use a credentials-file:
# cloudflared service install <TUNNEL-TOKEN>
```

`cloudflared service install` copies the tunnel into Windows so it autostarts.

## 3. Start the dashboard

Through the existing launcher (`main.py`) as before, or standalone:

```bash
python dashboard/app.py
```

Open `https://weighbridge.example.com`, enter the token, and you are in.
`http://localhost:8000` still works on this machine exactly as before.

At startup it prints what it decided:

```
[CONFIG] listen            : 127.0.0.1:8000
[CONFIG] authentication    : enabled (shared token)
[CONFIG] API docs          : disabled
```

## How the login works

- One shared secret, `DASHBOARD_AUTH_TOKEN`, never stored in code and never sent
  over the wire in a readable form. Enter it at the login prompt; it is never
  written to the database or logged.
- The token is exchanged for an HMAC-signed session cookie (`HttpOnly`,
  `SameSite=Strict`, and `Secure` whenever the public request is HTTPS).
- Sign out revokes the session server-side, so a copied cookie stops working
  immediately rather than lasting until it expires.
- Cookie-authenticated writes must also echo an `X-CSRF-Token` header, so
  another website cannot make your browser issue OPC-UA writes.
- Failed logins are throttled per client IP (5 attempts per 5 minutes).
- Scripted clients can skip cookies with `Authorization: Bearer <token>`; the
  WebSocket accepts `?token=` for the same reason, since browsers cannot set
  headers on a WebSocket handshake.

## Verification checklist

```bash
# 1. the dashboard is NOT on the LAN anymore
netstat -ano | findstr :8000        # expect 127.0.0.1:8000, never 0.0.0.0:8000

# 2. API refuses anonymous callers
curl -i http://127.0.0.1:8000/api/tags            # expect 401
curl -i http://127.0.0.1:8000/healthz             # expect 200 (no token needed)

# 3. HTTPS public entry point
curl -I https://weighbridge.example.com/          # expect 200 + Strict-Transport-Security

# 4. no API documentation is published
curl -i http://127.0.0.1:8000/docs                # expect 404
```

From a phone on mobile data, not office Wi-Fi: log in, confirm live weights
update, toggle one lane control, and confirm the page shows data without any
VPN. Then sign out and confirm the page locks again.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Login prompt never appears, page is empty of data | `DASHBOARD_AUTH_TOKEN` not set, or the `.env` is not in `dashboard/` |
| `401` immediately after a correct token | Session cookie rejected: confirm `DASHBOARD_TRUSTED_PROXY_IPS` includes `127.0.0.1`, and that you are not behind another reverse proxy |
| Browser warns the cookie is not `Secure` | Cloudflare is not sending `X-Forwarded-Proto`; set `DASHBOARD_SECURE_COOKIES=true` |
| Live data stops updating but the page loads | WebSocket blocked: confirm `wss://<hostname>/ws` upgrades. The frontend uses `location.protocol`, so it follows HTTPS automatically |
| Buttons show "Write failed: Unknown tag" | The tag is not in `config/weighbridgeConfig.json`; writes are restricted to that allowlist on purpose |
| App exits at startup with `[CONFIG ERROR]` | Non-loopback bind without a token, or a token under 16 characters. Both are refused deliberately |
| Page loads but styling/icons are missing | Content-Security-Policy is too strict for the CDN assets: open the browser console, then set `DASHBOARD_CSP=` to disable it and report what failed |

## Notes and limits

- One shared token means every authorised operator sees the same session
  policy; there are no per-user accounts or roles. That matches the single
  operator workstation this dashboard is used on. Per-user accounts would be
  the next step if several people need separate audit trails.
- Logout revocations are held in memory, so restarting the dashboard forgets
  them. A cookie's own 12-hour lifetime still bounds the exposure.
- The dashboard still polls all configured OPC tags twice a second. Remote
  viewing does not change that, and a lost Internet connection has no effect on
  local operation.
