# Network Security Guide - Keep Your App Private

## Quick Answer: You're Probably Already Safe!

If you're running the app with `host='0.0.0.0'` on your home network and haven't done any special router configuration, you're **likely already safe**. But let's verify and lock it down properly.

---

## Understanding the Network Setup

### What `host='0.0.0.0'` Means

When you run:
```python
app.run(host='0.0.0.0', port=5000)
```

This means:
- ✅ **Accessible from YOUR computer**: `localhost:5000` or `127.0.0.1:5000`
- ✅ **Accessible from devices on your WiFi**: `192.168.1.X:5000` (your local IP)
- ❌ **NOT accessible from the internet** (unless you configure port forwarding)

### Your Network Layers

```
Internet (Public)
    ↓
[Your Router/Modem]  ← Firewall (blocks incoming connections by default)
    ↓
Your Home Network (Private: 192.168.x.x or 10.x.x.x)
    ↓
Your Computer (Running the app on port 5000)
```

---

## ✅ Verify Your App Is Private

### Step 1: Check Your Private IP Address

**On Mac:**
```bash
# Get your local IP
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**On Linux:**
```bash
hostname -I
# or
ip addr show
```

**On Windows:**
```bash
ipconfig
# Look for "IPv4 Address" under your WiFi adapter
```

You should see something like:
- `192.168.1.100` ← **Private IP (safe)**
- `10.0.0.50` ← **Private IP (safe)**
- `172.16.0.10` ← **Private IP (safe)**

**These are PRIVATE IPs - not accessible from the internet!**

### Step 2: Check Your Public IP

Visit: https://whatismyipaddress.com/

Your public IP will be something like:
- `203.45.67.89` ← **Public IP (what the internet sees)**

### Step 3: Verify Port 5000 Is NOT Exposed

Go to: https://www.yougetsignal.com/tools/open-ports/

- Enter your **public IP** (from Step 2)
- Enter port: `5000`
- Click "Check"

**Expected Result**: ✅ **Port 5000 is closed**

If it says "open", you have port forwarding enabled (see fixes below).

---

## 🔒 Lock It Down: Firewall Configuration

### Option 1: Mac Firewall

**Enable Firewall:**
1. Open **System Settings** → **Network** → **Firewall**
2. Turn on **Firewall**
3. Click **Options**
4. Enable **"Block all incoming connections"** OR
5. Allow Python only for specific networks

**Command Line (Advanced):**
```bash
# Check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Enable firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Block all incoming connections
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setblockall on
```

### Option 2: Linux Firewall (UFW)

```bash
# Install UFW if not present
sudo apt install ufw

# Enable firewall
sudo ufw enable

# Default: deny all incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (if you need remote access to your machine)
sudo ufw allow 22

# Block port 5000 from external access (allow only local)
sudo ufw deny 5000

# Check status
sudo ufw status
```

### Option 3: Windows Firewall

**Using Windows Defender Firewall:**
1. Open **Windows Security** → **Firewall & network protection**
2. Click **Advanced settings**
3. Click **Inbound Rules** → **New Rule**
4. Select **Port** → **TCP** → Specific port: `5000`
5. Select **Block the connection**
6. Apply to all profiles (Domain, Private, Public)
7. Name it: "Block Face Swap App External Access"

**Command Line (PowerShell - Admin):**
```powershell
# Block port 5000 from external access
New-NetFirewallRule -DisplayName "Block Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Block
```

---

## 🏠 Router Configuration - Double Check

### What You DON'T Want (Port Forwarding)

**Check your router settings:**
1. Open router admin page (usually `192.168.1.1` or `192.168.0.1`)
2. Login (check router label for password)
3. Look for **Port Forwarding** or **NAT** section

**Verify:**
- ❌ **No rule forwarding port 5000** to your computer
- ❌ **No DMZ (Demilitarized Zone)** enabled for your computer
- ❌ **No UPnP rules** for port 5000

**If you see any of these, DELETE them!**

### Common Router Locations for Port Forwarding

- **Netgear**: Advanced → Advanced Setup → Port Forwarding
- **Linksys**: Security → Apps and Gaming → Port Forwarding
- **TP-Link**: Forwarding → Virtual Servers
- **Google WiFi**: Google Home app → Settings → Advanced networking → Port management

---

## 🛡️ Best Practices for Home Network Security

### 1. Use Strong WiFi Password

```bash
# Your WiFi password should be:
- At least 16 characters
- Mix of letters, numbers, symbols
- Not dictionary words
- Example: "MyH0me!2025#Secure$WiFi"
```

### 2. Separate Guest Network (Optional but Recommended)

Most routers support guest networks:
- Main network: Your devices + face-swap app
- Guest network: Visitors' devices

**This prevents guests from accessing your app!**

### 3. Disable WPS (WiFi Protected Setup)

WPS is vulnerable to brute force attacks:
1. Router settings → Wireless → WPS
2. Disable WPS

### 4. Keep Router Firmware Updated

Check for updates:
1. Router admin page
2. System or Administration section
3. Check for firmware updates
4. Update if available

---

## 📱 Accessing From iPhone - Safe Methods

### Method 1: Same WiFi (Safest)

```
1. Connect iPhone to your home WiFi
2. On your computer, find local IP: ifconfig / ipconfig
3. On iPhone Safari: http://YOUR_LOCAL_IP:5000
   Example: http://192.168.1.100:5000
4. Bookmark it for easy access
```

**Why it's safe:**
- Traffic never leaves your home network
- No internet exposure
- Fast and private

### Method 2: VPN (For Remote Access)

If you want to access from outside your home:

**Install Tailscale (Easiest):**
```bash
# On your computer
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

# On your iPhone
# Install Tailscale app from App Store
# Connect to same account
# Access via Tailscale IP: http://100.x.x.x:5000
```

**Why it's safe:**
- Encrypted tunnel
- No port forwarding needed
- Access from anywhere securely

### Method 3: Local Network Only (Recommended)

Just use it when you're home:
```
✅ Home WiFi only
✅ No VPN needed
✅ No configuration required
✅ Zero internet exposure
```

---

## 🧪 Test Your Security

### Test 1: Can Friends on Your WiFi Access It?

**Expected:** ✅ **YES** (this is normal and safe if you trust them)

If you want to block this:
```python
# Change app.py line 250
app.run(host='127.0.0.1', port=5000)  # Only accessible from YOUR computer
```

### Test 2: Can Someone on 4G/5G Access It?

**Expected:** ❌ **NO** (cannot connect)

**To test:**
1. Turn off WiFi on your phone
2. Use cellular data (4G/5G)
3. Try to access: http://YOUR_PUBLIC_IP:5000
4. Should fail to connect

If it connects, you have port forwarding enabled → **Disable it immediately!**

### Test 3: Port Scan from External Service

Go to: https://www.grc.com/x/ne.dll?bh0bkyd2

- Click **Proceed**
- Click **All Service Ports**
- Wait for scan (takes 2 minutes)
- Port 5000 should show: **Stealth** or **Closed**

---

## 🚨 Warning Signs You're Exposed

**If you see any of these, you're exposed to the internet:**

1. ❌ Port checker shows port 5000 is **OPEN**
2. ❌ Can access app from cellular data (4G/5G)
3. ❌ Router shows port forwarding rule for port 5000
4. ❌ Firewall is disabled
5. ❌ Computer is in DMZ

**Fix:** Follow the "Lock It Down" section above.

---

## ✅ Recommended Configuration

### For Home Use (iPhone on Same WiFi)

```python
# app.py - line 250
# Option A: Allow anyone on home WiFi (easiest for iPhone access)
app.run(host='0.0.0.0', port=5000, debug=False)

# Option B: Only your computer (most restrictive)
app.run(host='127.0.0.1', port=5000, debug=False)
```

**Plus:**
- ✅ Firewall enabled on your computer
- ✅ No port forwarding on router
- ✅ Strong WiFi password
- ✅ Router firmware updated

### For Paranoid Security

```python
# Only allow specific IP addresses
from flask import request, abort

@app.before_request
def limit_remote_addr():
    # Only allow requests from your local network
    allowed_ips = ['127.0.0.1', '192.168.1.100', '192.168.1.101']  # Add your IPs
    if request.remote_addr not in allowed_ips:
        abort(403)  # Forbidden
```

---

## 📋 Quick Security Checklist

Copy this checklist and verify each item:

- [ ] Checked local IP (should be 192.168.x.x or 10.x.x.x)
- [ ] Checked public IP (different from local IP)
- [ ] Port 5000 shows as **CLOSED** on port checker
- [ ] Cannot access app from cellular data
- [ ] Firewall enabled on computer
- [ ] No port forwarding rules for port 5000 in router
- [ ] No DMZ enabled for your computer
- [ ] WiFi has strong password
- [ ] WPS disabled on router
- [ ] App runs with `debug=False`
- [ ] Can access from iPhone when on same WiFi ✅

---

## 🆘 If You're Still Worried

### Nuclear Option: Bind to Localhost Only

```python
# app.py - line 250
app.run(host='127.0.0.1', port=5000, debug=False)
```

This makes the app **ONLY** accessible from your computer, not even from your iPhone on WiFi.

**To use on iPhone:**
1. Install ngrok: https://ngrok.com
2. Run: `ngrok http 5000`
3. Use the ngrok URL on your iPhone
4. **Note:** This routes through ngrok servers, less private

**Better alternative:** Use Tailscale (mentioned above)

---

## 📞 Need Help?

**To check if you're safe, run this on your computer:**

```bash
# Save as check_network.sh
#!/bin/bash

echo "=== Network Security Check ==="
echo ""
echo "1. Your Local IP:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
else
    hostname -I
fi

echo ""
echo "2. Your Public IP:"
curl -s https://api.ipify.org
echo ""

echo ""
echo "3. Checking if port 5000 is listening:"
if lsof -i :5000 > /dev/null 2>&1; then
    echo "✅ App is running on port 5000"
else
    echo "❌ App is NOT running on port 5000"
fi

echo ""
echo "4. Firewall status:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
else
    sudo ufw status 2>/dev/null || echo "UFW not installed"
fi

echo ""
echo "=== Security Recommendations ==="
echo "✅ Keep the app on 0.0.0.0:5000 (fine for home WiFi)"
echo "✅ Ensure no port forwarding on router"
echo "✅ Verify port 5000 is CLOSED from internet (use yougetsignal.com)"
echo "✅ Use strong WiFi password"
echo ""
echo "You're safe if:"
echo "  - Local IP is 192.168.x.x or 10.x.x.x"
echo "  - Port checker shows 5000 as CLOSED"
echo "  - Can't access from cellular data"
```

Run with:
```bash
chmod +x check_network.sh
./check_network.sh
```

---

## Summary

**You're probably already safe if:**
1. You haven't configured port forwarding on your router
2. Your firewall is enabled
3. You're using `host='0.0.0.0'` which is fine for home WiFi

**The key point:** `0.0.0.0` makes it accessible on your LOCAL network only, NOT the internet (unless you specifically configure port forwarding).

**For iPhone access:** Just connect to same WiFi, use your local IP (192.168.x.x), and you're good to go! 🎉

---

**Still concerned?** Follow the checklist above and run the security check script. If any red flags appear, follow the "Lock It Down" section.
