# Testing Crisis Alerts

## Quick Test

Open `test_crisis_endpoint.html` in your browser and click the buttons to verify:

1. **Test /crisis-events** - Should show crisis event with parsed patterns array
2. **Test /conversations/1** - Should show full conversation with message and response
3. **Test Full Crisis Event** - Should show both combined

## Expected Results

### Crisis Event:
```json
{
  "id": 1,
  "conversation_id": 1,
  "risk_score": 0.98,
  "matched_patterns": ["suicidal_ideation", "intent_with_plan", "timeline_specified"],
  "reasoning": "CRISIS DETECTED: Message contains explicit suicidal ideation..."
}
```

### Conversation:
```json
{
  "id": 1,
  "message": "I can't do this anymore. I've been thinking about ending it all...",
  "response": "I hear that you're in a lot of pain right now...",
  "risk_score": 0.98,
  "regex_score": 0.95,
  "semantic_score": 0.92,
  "mistral_score": 0.97
}
```

## If Crisis Alerts Still Don't Work

### Check 1: Browser Console
1. Open DevTools (F12)
2. Go to Console tab
3. Look for errors when clicking on crisis events

### Check 2: Network Tab
1. Open DevTools (F12)
2. Go to Network tab
3. Click on a crisis event
4. Look for the `/conversations/{id}` request
5. Check if it returns data or errors

### Check 3: Backend Logs
Look at the backend terminal for any errors when crisis events are expanded.

## Common Issues

### Issue: "No message available" / "No response available"
**Cause**: Conversation endpoint returning empty data
**Fix**: Check backend logs for errors

### Issue: Page goes blank when expanding
**Cause**: JavaScript error in frontend
**Fix**: Check browser console for errors

### Issue: N/A values in layer scores
**Cause**: Data not being parsed correctly
**Fix**: Verify backend is restarted with latest code

## Verification Checklist

- [ ] Students tab shows conversations ✅ (You confirmed this works)
- [ ] Crisis Alerts tab shows 3 events
- [ ] Clicking "▶ View Details" expands without crashing
- [ ] Student message is visible (not "No message available")
- [ ] Connor's response is visible (not "No response available")
- [ ] Layer scores show percentages (not N/A)
- [ ] Performance metrics show milliseconds (not "N/A ms")

---

**If everything in the test HTML works but the dashboard doesn't, the issue is in the frontend React code, not the backend.**
