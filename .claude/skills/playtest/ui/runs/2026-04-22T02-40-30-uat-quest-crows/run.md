# Playtest run: quest-crows

- **Target:** uat (https://uat.eldritchmush.com)
- **Character:** UAT Bot
- **Start:** 2026-04-22T02:40:30.023Z
- **Duration:** 33.0s
- **Result:** ❌ FAIL — locator.click: Timeout 30000ms exceeded.
Call log:
[2m  - waiting for locator('.charsel-card-create')[22m
[2m    - locator resolved to <button type="button" class="charsel-card charsel-card-create">…</button>[22m
[2m  - attempting click action[22m
[2m    2 × waiting for element to be visible, enabled and stable[22m
[2m      - element is visible, enabled and stable[22m
[2m      - scrolling into view if needed[22m
[2m      - done scrolling[22m
[2m      - <div class="charsel-modal-backdrop">…</div> intercepts pointer events[22m
[2m    - retrying click action[22m
[2m    - waiting 20ms[22m
[2m    2 × waiting for element to be visible, enabled and stable[22m
[2m      - element is visible, enabled and stable[22m
[2m      - scrolling into view if needed[22m
[2m      - done scrolling[22m
[2m      - <div class="charsel-modal-backdrop">…</div> intercepts pointer events[22m
[2m    - retrying click action[22m
[2m      - waiting 100ms[22m
[2m    58 × waiting for element to be visible, enabled and stable[22m
[2m       - element is visible, enabled and stable[22m
[2m       - scrolling into view if needed[22m
[2m       - done scrolling[22m
[2m       - <div class="charsel-modal-backdrop">…</div> intercepts pointer events[22m
[2m     - retrying click action[22m
[2m       - waiting 500ms[22m


## Screenshots
- `uat-quest-crows-01-post-load.png`
- `uat-quest-crows-02a-charsel-empty.png`
- `uat-quest-crows-99-failure.png`

## Game feed (server [qtest]/[test] lines)
_(none captured)_

## Browser console errors
_(none)_
