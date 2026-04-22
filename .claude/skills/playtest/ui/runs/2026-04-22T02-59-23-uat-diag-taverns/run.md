# Playtest run: diag-taverns

- **Target:** uat (https://uat.eldritchmush.com)
- **Character:** Quest Tester
- **Start:** 2026-04-22T02:59:23.065Z
- **Duration:** 6.6s
- **Result:** ✅ PASS

## Screenshots
- `uat-diag-taverns-01-diag.png`
- `uat-diag-taverns-01-post-load.png`

## Game feed (server [qtest]/[test] lines)
```
sg(f&quot;[diag] tavern-ish rooms: {[(r.id, r.db_key) for r in matches]}&quot;)"], {"type": "py_input"}]
"text", ["[diag] tavern-ish rooms: [(2051, 'The Aentact'), (2084, 'Goldleaf \u2014 Innis Encampment')]"], {}]
```

## Browser console errors
_(none)_
