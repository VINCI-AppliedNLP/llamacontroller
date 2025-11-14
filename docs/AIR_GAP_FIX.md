# Air-Gap Machine Fix

## Problem Identified

The web application was loading three external JavaScript libraries from CDNs, which would fail on air-gapped (offline) machines:

1. **Tailwind CSS** - from `https://cdn.tailwindcss.com`
2. **HTMX 1.9.10** - from `https://unpkg.com/htmx.org@1.9.10`
3. **Alpine.js 3.x** - from `https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js`

Additionally, the FastAPI application was missing static file serving configuration, which caused the error:
```
starlette.routing.NoMatchFound: No route exists for name "static" and params "path".
```

## Solution Applied

### 1. Downloaded Local Copies

All three libraries have been downloaded and saved locally in `src/llamacontroller/web/static/js/`:

- `htmx-1.9.10.min.js` (47,755 bytes)
- `alpinejs-3.14.1.min.js` (44,659 bytes)
- `tailwindcss.js` (407,279 bytes)

### 2. Updated Templates

Modified `src/llamacontroller/web/templates/base.html` to load from local files instead of CDNs:

**Before:**
```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- HTMX -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>

<!-- Alpine.js -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

**After:**
```html
<!-- Tailwind CSS (Local) -->
<script src="{{ url_for('static', path='/js/tailwindcss.js') }}"></script>

<!-- HTMX (Local) -->
<script src="{{ url_for('static', path='/js/htmx-1.9.10.min.js') }}"></script>

<!-- Alpine.js (Local) -->
<script defer src="{{ url_for('static', path='/js/alpinejs-3.14.1.min.js') }}"></script>
```

### 3. Configured Static File Serving

Modified `src/llamacontroller/main.py` to mount the static files directory:

**Added imports:**
```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles
```

**Added static file mounting:**
```python
# Mount static files directory
static_dir = Path(__file__).parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
```

This configuration allows the FastAPI application to serve files from `/static` and enables the `url_for('static', ...)` function in templates.

## Testing

To verify the fix works on an air-gapped machine:

1. Start the application
2. Disconnect from the internet
3. Access the web interface at `http://localhost:8000`
4. All pages should render correctly without any missing styles or functionality

## Files Modified

- `src/llamacontroller/web/templates/base.html` - Updated CDN URLs to local references
- `src/llamacontroller/main.py` - Added static file serving configuration

## Files Added

- `src/llamacontroller/web/static/js/htmx-1.9.10.min.js`
- `src/llamacontroller/web/static/js/alpinejs-3.14.1.min.js`
- `src/llamacontroller/web/static/js/tailwindcss.js`

## Notes

- The Tailwind CSS Play CDN script is suitable for development/prototyping but includes the full compiler (~400KB). For production, consider using the Tailwind CLI to generate a smaller, optimized CSS file.
- All child templates (dashboard.html, login.html, logs.html, tokens.html) inherit from base.html, so they will automatically use the local resources.
- The inline JavaScript in tokens.html for token generation uses browser-native APIs (crypto.getRandomValues, btoa) and will work offline.

## Future Improvements (Optional)

For production optimization:

1. **Tailwind CSS**: Use Tailwind CLI to build a static CSS file:
   ```bash
   npx tailwindcss -o static/css/tailwind.min.css --minify
   ```
   Then replace the script tag with a link to the CSS file.

2. **Minification**: The current files are already minified, but you could further optimize by removing unused CSS/JS.

3. **Versioning**: Consider adding version numbers to filenames (e.g., `tailwind-4.0.0.min.css`) for cache busting during updates.
