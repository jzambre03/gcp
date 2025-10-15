# Where to See Logs - Config-Only Branch Creation

## 📍 **Where Logs Appear**

### **Terminal Where You Run `python main.py`**

All logs will now appear **directly in your terminal** where you started the FastAPI server.

---

## 🖥️ **Example Terminal Output**

When you click "Certify" or "Analyze", you'll see output like this in your terminal:

```bash
$ python main.py

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)

# ... when you click "Certify" ...

================================================================================
🌿 CREATING CONFIG-ONLY BRANCH: golden_prod_20251015_120000_abc123
📂 Temp directory: /tmp/git_config_branch_xyz789
🎯 Source branch: main
📋 Config patterns to include:
   1. *.yml
   2. *.yaml
   3. *.properties
   4. *.toml
   5. *.ini
   6. *.cfg
   7. *.conf
   8. *.config
   9. Dockerfile
   10. docker-compose.yml
   11. .env.example
   12. pom.xml
   13. build.gradle
   14. build.gradle.kts
   15. settings.gradle
   16. settings.gradle.kts
   17. package.json
   18. requirements.txt
   19. pyproject.toml
   20. go.mod
================================================================================
Step 1: Initializing empty Git repository...
✅ Repository initialized at: /tmp/git_config_branch_xyz789
Step 2: Adding remote 'origin'...
✅ Remote added: https://gitlab.verizon.com/saja9l7/cxp-ordering-services.git
Step 3: Enabling sparse-checkout...
✅ Sparse-checkout enabled (non-cone mode for wildcard support)
Step 4: Writing sparse-checkout patterns to: /tmp/git_config_branch_xyz789/.git/info/sparse-checkout
✅ Sparse-checkout patterns written:
*.yml
*.yaml
*.properties
*.toml
*.ini
*.cfg
*.conf
*.config
Dockerfile
docker-compose.yml
.env.example
pom.xml
build.gradle
build.gradle.kts
settings.gradle
settings.gradle.kts
package.json
requirements.txt
pyproject.toml
go.mod

Step 5: Fetching main with sparse-checkout filter...
   Using: git fetch origin main --depth=1
✅ Fetch completed
Step 6: Checking out main (sparse-checkout will filter files)...
✅ Checkout completed
Step 7: Verifying sparse-checkout results...
✅ Sparse-checkout result: 47 files checked out
📄 Files in working directory:
   1. Dockerfile
   2. config/application-dev.yml
   3. config/application-prod.yml
   4. config/application.yml
   5. config/database.properties
   6. config/redis.conf
   7. docker-compose.yml
   8. pom.xml
   9. src/main/resources/application.yml
   ... (all config files listed)
Step 8: Creating new branch: golden_prod_20251015_120000_abc123
✅ Branch created and checked out
Step 9: Pushing config-only branch to remote...
✅ Branch pushed to remote
================================================================================
🎉 SUCCESS: Config-only branch golden_prod_20251015_120000_abc123 created!
   Files included: 47
   Branch pushed to: https://gitlab.verizon.com/saja9l7/cxp-ordering-services.git
================================================================================
🧹 Cleaned up temp directory: /tmp/git_config_branch_xyz789

INFO:     127.0.0.1:54321 - "POST /api/services/cxp_ordering_services/set-golden/prod HTTP/1.1" 200 OK
```

---

## 🎯 **Key Metrics to Look For**

### **1. File Count** (Most Important!)
```
✅ Sparse-checkout result: 47 files checked out
```

**What to check**:
- ✅ **Good**: 50-100 files (config only)
- ❌ **Bad**: 3,500+ files (all files - sparse-checkout not working)

---

### **2. File List**
```
📄 Files in working directory:
   1. Dockerfile
   2. config/application.yml
   3. pom.xml
```

**What to check**:
- ✅ **Good**: Only config files (`.yml`, `.properties`, `pom.xml`, etc.)
- ❌ **Bad**: Seeing `.java`, `.class`, `node_modules/`, `target/`

---

### **3. Success Message**
```
🎉 SUCCESS: Config-only branch golden_prod_20251015_120000_abc123 created!
   Files included: 47
```

**What to check**:
- ✅ **Good**: "SUCCESS" message with low file count
- ❌ **Bad**: Error messages or high file count

---

## 🔍 **If You Don't See Logs**

### **Possible Issues**:

1. **Terminal not visible**
   - Make sure you're looking at the terminal where you ran `python main.py`
   - Don't look at the browser console - logs are in the terminal

2. **Logs scrolled away**
   - Scroll up in your terminal
   - Logs appear when you click "Certify" or "Analyze"

3. **Server not running in foreground**
   - If running in background, logs might go to a file
   - Run in foreground: `python main.py`

---

## 📋 **Step-by-Step: How to See Logs**

### **Step 1: Start Server**
```bash
cd "/Users/jayeshzambre/Downloads/AI Project/strands-multi-agent-system"
python main.py
```

**You should see**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)
```

### **Step 2: Open Browser**
- Go to: `http://localhost:3000`
- Navigate to: Branch & Environment page
- Click: "Certify" button for any environment

### **Step 3: Watch Terminal**
- **Immediately** look at your terminal (where you ran `python main.py`)
- You should see the detailed logs appear
- Look for the `🌿 CREATING CONFIG-ONLY BRANCH` header

### **Step 4: Check File Count**
- Find this line: `✅ Sparse-checkout result: XX files checked out`
- **XX should be ~50-100** (not 3,500+)

---

## 🎨 **Log Sections Explained**

### **Header Section**
```
================================================================================
🌿 CREATING CONFIG-ONLY BRANCH: golden_prod_20251015_120000_abc123
📂 Temp directory: /tmp/git_config_branch_xyz789
🎯 Source branch: main
📋 Config patterns to include:
   1. *.yml
   ...
================================================================================
```
**Purpose**: Shows what branch is being created and what patterns will be used

---

### **Steps 1-6: Git Operations**
```
Step 1: Initializing empty Git repository...
✅ Repository initialized

Step 2: Adding remote 'origin'...
✅ Remote added

Step 3: Enabling sparse-checkout...
✅ Sparse-checkout enabled (non-cone mode for wildcard support)

Step 4: Writing sparse-checkout patterns...
✅ Sparse-checkout patterns written:
*.yml
*.properties
...

Step 5: Fetching main with sparse-checkout filter...
✅ Fetch completed

Step 6: Checking out main (sparse-checkout will filter files)...
✅ Checkout completed
```
**Purpose**: Shows Git operations happening step-by-step

---

### **Step 7: Verification (MOST IMPORTANT)**
```
Step 7: Verifying sparse-checkout results...
✅ Sparse-checkout result: 47 files checked out
📄 Files in working directory:
   1. Dockerfile
   2. config/application.yml
   ...
```
**Purpose**: **This is the key section!** It shows:
- How many files were checked out
- What files were checked out
- Verifies sparse-checkout worked correctly

**What to check**:
- File count should be ~50-100
- File list should only show config files

---

### **Steps 8-9: Branch Creation**
```
Step 8: Creating new branch...
✅ Branch created

Step 9: Pushing config-only branch to remote...
✅ Branch pushed
```
**Purpose**: Shows branch being created and pushed to GitLab

---

### **Success Summary**
```
================================================================================
🎉 SUCCESS: Config-only branch golden_prod_20251015_120000_abc123 created!
   Files included: 47
   Branch pushed to: https://gitlab.verizon.com/...
================================================================================
```
**Purpose**: Confirms success and shows final file count

---

## ⚠️ **Troubleshooting**

### **Issue: No logs appearing**

**Solution 1**: Check you're looking at the right terminal
```bash
# Make sure you're in the terminal where you ran:
python main.py

# NOT the browser console
```

**Solution 2**: Restart the server
```bash
# Stop server (Ctrl+C)
# Start again:
python main.py
```

**Solution 3**: Check if server is running
```bash
# In a new terminal:
curl http://localhost:3000/api/info
# Should return JSON response
```

---

### **Issue: Logs show 3,500+ files**

**This means sparse-checkout is NOT working**

**Check logs for**:
```
✅ Sparse-checkout enabled (non-cone mode for wildcard support)
```

If you see this but still getting all files, check:
1. Git version: `git --version` (should be >= 2.25)
2. Patterns were written correctly
3. No errors in Step 4-6

---

### **Issue: Error messages in logs**

**Look for**:
```
❌ GIT ERROR creating config-only branch
```

**Common errors**:
- Authentication failed → Check `GITLAB_TOKEN` in `.env`
- Branch already exists → Normal if re-certifying
- Network error → Check internet connection

---

## ✅ **Quick Verification**

Run through this checklist:

1. [ ] Server running: `python main.py` shows "Uvicorn running"
2. [ ] Click "Certify" in browser
3. [ ] Terminal shows logs starting with `🌿 CREATING CONFIG-ONLY BRANCH`
4. [ ] Step 7 shows file count ~50-100 (not 3,500+)
5. [ ] File list shows only config files
6. [ ] Success message appears: `🎉 SUCCESS`

---

## 🎉 **Summary**

**Where to see logs**: Terminal where you run `python main.py`

**When logs appear**: When you click "Certify" or "Analyze"

**Key metric**: `✅ Sparse-checkout result: XX files checked out`
- ✅ XX = 50-100 → Working correctly!
- ❌ XX = 3,500+ → Not working, check logs for errors

**All logs now use `print()` so they WILL appear in your terminal!** 📺

