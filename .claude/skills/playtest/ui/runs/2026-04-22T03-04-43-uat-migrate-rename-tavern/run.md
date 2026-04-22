# Playtest run: migrate-rename-tavern

- **Target:** uat (https://uat.eldritchmush.com)
- **Character:** Quest Tester
- **Start:** 2026-04-22T03:04:43.456Z
- **Duration:** 8.6s
- **Result:** ✅ PASS

## Screenshots
- `uat-migrate-rename-tavern-01-migration-done.png`
- `uat-migrate-rename-tavern-01-post-load.png`
- `uat-migrate-rename-tavern-02-verify.png`

## Game feed (server [qtest]/[test] lines)
```
sg(f&quot;[migrate] rooms named Songbird&#x27;s Rest: {[(r.id, r.key) for r in rs]}&quot;)"], {"type": "py_input"}]
"text", ["[migrate] rooms named Songbird's Rest: [(2051, \"Songbird's Rest\")]"], {}]
```

## Browser console errors
_(none)_
