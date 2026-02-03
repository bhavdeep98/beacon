# 🔄 Restart Instructions for Counselor Dashboard

## Current Issue
The dashboard shows empty conversations and N/A values because:
1. Backend needs to be restarted to load new endpoints
2. Data needs to be reseeded with correct session hashes

## ✅ Complete Fix (5 minutes)

### Step 1: Stop the Backend
In the terminal running the backend, press `Ctrl+C` to stop it.

### Step 2: Run the Fix Script
```bash
fix_dashboard.bat
```

This will:
- Clear old conversation data
- Reseed with correct session hashes
- Verify data integrity

### Step 3: Restart the Backend
```bash
cd backend
python main.py
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

### Step 4: Refresh the Frontend
In your browser, refresh the Counselor Dashboard page (F5 or Ctrl+R)

### Step 5: Verify It Works

**Test 1: Students Tab**
1. Click on "Jordan" in the student roster
2. You should see:
   - ✅ Active Themes: Academic Stress (3x), Family Issues (2x)
   - ✅ Conversation History with multiple conversations
3. Click "▶ Expand Details" on any conversation
4. You should see:
   - ✅ Diagnostic Analysis with layer scores (not N/A)
   - ✅ AI Reasoning text
   - ✅ Detected Patterns as colored tags
   - ✅ Metadata with session ID and latency

**Test 2: Crisis Alerts Tab**
1. Click "🚨 Crisis Alerts (3)" button
2. You should see 3 crisis events with red borders
3. Click "▶ View Details" on any event
4. You should see:
   - ✅ Full student message and Connor's response
   - ✅ Multi-Layer Analysis with percentages (not N/A)
   - ✅ AI Reasoning Trace
   - ✅ Crisis Patterns as red tags
   - ✅ Performance Metrics with latency in ms (not "N/A ms")

## 🐛 If It Still Doesn't Work

### Check 1: Backend is Running
```bash
curl http://localhost:8000/health
```
Should return: `{"status":"healthy",...}`

### Check 2: Data Exists
```bash
python test_dashboard_data.py
```
Should show:
- ✓ Students: 3
- ✓ Conversations: 10
- ✓ Crisis Events: 3
- ✓ Themes: 6

### Check 3: Endpoint Works
```bash
curl http://localhost:8000/crisis-events?limit=1
```
Should return JSON with crisis event data (not empty)

### Check 4: Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for errors (red text)
4. If you see errors, share them for debugging

## 📝 What Was Fixed

1. **Session Hash Mismatch**: Conversations now use student's hash as session hash
2. **JSON Parsing**: Frontend now parses `matched_patterns` from JSON strings
3. **Null Checks**: Added comprehensive null/undefined checks
4. **New Endpoint**: Added `/conversations/{conversation_id}` endpoint

## 🎯 Expected Behavior

After the fix, the dashboard should show:

### For Each Student:
- Conversation count matches actual conversations displayed
- All conversations have complete data (message, response, scores)
- Expandable details show full diagnostic information
- No "N/A" values (except for optional Mistral scores if timeout occurred)

### For Each Crisis Event:
- Full conversation context (what student said + Connor's response)
- All three layer scores as percentages
- Complete reasoning trace
- Performance metrics with actual millisecond values
- No blank pages or crashes

## 🚀 Quick Commands

```bash
# Full reset and fix
fix_dashboard.bat

# Just restart backend
cd backend
python main.py

# Verify data
python test_dashboard_data.py

# Test endpoint
curl http://localhost:8000/crisis-events?limit=1
```

## 📚 Related Documentation

- [DASHBOARD_FIX_SUMMARY.md](./DASHBOARD_FIX_SUMMARY.md) - Technical details of the fix
- [COUNSELOR_DASHBOARD_DEMO.md](./COUNSELOR_DASHBOARD_DEMO.md) - How to use the dashboard
- [DEMO_CONVERSATIONS.md](./DEMO_CONVERSATIONS.md) - Details of seeded conversations

---

**Need Help?** Check the browser console (F12) for errors and share them for debugging.
