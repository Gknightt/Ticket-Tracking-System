# A.3 Application Design and Development — Frontend

This document captures the low-level design and implementation details for the frontend of the Ticket-Tracking-System project. It highlights the major libraries, design patterns, key algorithms (pseudocode), and selected code snippets for critical functions.

**Scope**: UI components, frontend frameworks, design patterns and implementation notes.

**Generated:** Automatically extracted from the frontend codebase on build/analysis.

**Contents**
- **Libraries & Versions**
- **High-level architecture & patterns**
- **Key components and flows**
- **Algorithms & pseudocode**
- **Selected code snippets and explanations**
- **Notes & next steps**

**Libraries & Versions**
- **React**: ^18.2.0
- **React DOM**: ^18.2.0
- **Vite**: ^7.1.3 (dev)
- **Axios**: ^1.11.0
- **React Router DOM**: ^7.6.2
- **React Flow / reactflow**: ^11.11.4
- **@reactflow/core**: ^11.11.4
- **Chart.js**: ^4.5.0 and **react-chartjs-2**: ^5.3.0
- **date-fns**: ^4.1.0 and **dayjs**: ^1.11.18
- **Font libraries**: @fortawesome/fontawesome-free ^6.7.2, font-awesome ^4.7.0, react-icons ^5.5.0, lucide-react ^0.523.0
- **PDF viewer**: @react-pdf-viewer/core ^3.12.0
- **Utility**: uuid ^11.1.0, dompurify ^3.3.0, mammoth ^1.9.1
- **Dev / Lint**: eslint ^9.25.0, @vitejs/plugin-react ^4.4.1

Source: `frontend/package.json` (dependencies/devDependencies)

**High-level architecture & patterns**
- Provider pattern / Context API: The app uses React Context Providers for cross-cutting state and services:
  - `AuthProvider` (in `src/api/AuthContext.jsx`) for authentication state, token handling, login/logout, token refresh and profile fetching.
  - `TicketsProvider` (in `src/api/TicketsContext.jsx`) for ticket-listing state and caching.
  - `WorkflowRefreshProvider` (components/workflow/WorkflowRefreshContext) to coordinate workflow UI refresh events.
- Routing: `react-router-dom` is used; `MainRoute.jsx` centralizes public and protected routes.
  - `ProtectedRoute.jsx` implements route protection (redirects when unauthenticated or unauthorized).
  - `ProtectedRegister.jsx` is a specialized guard that validates an external registration token before rendering the registration page.
- API abstraction: A singleton `axios` instance (`src/api/axios.jsx`) centralizes the backend base URL and JSON headers.
- Token utilities: `src/api/TokenUtils.js` contains helper functions to read/store tokens and parse JWT payloads.
- Component composition: Complex pages (e.g. Workflow Editor) are composed from smaller presentational and control components (toolbar, sidebar, content, panel).

**Key components and flows**
- `src/main.jsx` bootstraps the app and wraps `App` with `AuthProvider` and `TicketsProvider`.
- `src/App.jsx` mounts `MainRoute` inside a `BrowserRouter` and wraps with `WorkflowRefreshProvider`.
- `MainRoute.jsx` defines routes for:
  - Public pages: `/login`, reset-password routes, `/report`, websocket test
  - Protected agent routes: wrapped by `<ProtectedRoute requireAgent={true}>` (e.g. `/agent/dashboard`)
  - Protected admin routes: wrapped by `<ProtectedRoute requireAdmin={true}>` (e.g. `/admin/workflow`)
  - Special protected registration route: `/register` handled by `ProtectedRegister`.

Security / auth flow (summary):
- On mount `AuthProvider` runs `checkAuthStatus()` which:
  1. Checks if a token exists via `TokenUtils.hasAccessToken()`.
  2. Verifies token with auth server (`/api/v1/token/verify/`).
  3. If valid, fetches user profile (`/api/v1/users/profile/`) and stores combined data in `user` state.
  4. If verification fails, attempts a refresh (`/api/v1/token/refresh/`) once, stores new token, and retries fetching profile.
  5. If everything fails, clears token and sets user=null.

Ticket list flow (summary):
- `TicketsProvider` fetches `tasks/my-tasks/` and caches the payload using an in-memory cache (`src/utils/memoryCache`) to reduce API calls. A `refreshTickets` function invalidates the cache and re-fetches.

Workflow editor (high-level):
- Uses `reactflow` for node/edge editing. `WorkflowEditorLayout.jsx` manages UI state (selected node/edge, sidebar width, unsaved changes) and delegates graph editing to `WorkflowEditorContent`.
- Local persistence of UI prefs: sidebar width saved in `localStorage` under `workflow-sidebar-width`.

**Algorithms & pseudocode**

1) Auth lifecycle (verify, refresh, profile)

Pseudocode:

```
function checkAuthStatus(force=false):
  if !hasAccessToken():
    set user = null; set loading=false; return false

  isValid = verifyToken()  // POST /api/v1/token/verify/
  if isValid:
    try:
      userData = fetchUserProfile() // GET profile using Bearer token
      set user = merge(tokenUser, userData)
      return true
    catch profileErr:
      // fallback to token data or try refresh

  if not isValid and not refreshAttempted:
    refreshResp = post /api/v1/token/refresh/
    if refreshResp contains access:
      setAccessToken(refreshResp.access)
      refreshAttempted = true
      goto fetchUserProfile

  // if still failing
  removeAccessToken(); set user = null; return false
```

2) ProtectedRoute decision flow

Pseudocode:

```
function ProtectedRoute({requireAdmin, requireAgent}):
  if loading or !initialized: show loading spinner
  if not user: Navigate to /login (preserve state)
  if not hasTtsAccess(): Navigate to /unauthorized
  if requireAdmin and not isAdmin(): Navigate to /unauthorized
  if requireAgent and isAdmin(): Navigate to /admin/dashboard
  otherwise: render children (Outlet)
```

3) Tickets caching (fetchTickets)

Pseudocode:

```
function fetchTickets():
  cacheKey = ' '
  if memoryCache.get(cacheKey):
    setTickets(cached)
    setLoading(false)
  else:
    response = api.get('tasks/my-tasks/')
    memoryCache.set(cacheKey, response.data)
    setTickets(response.data)
```

4) Workflow editor save flow (simplified)

Pseudocode:

```
on Save All:
  if contentRef.saveChanges exists:
    setSaveStatus('saving')
    await contentRef.saveChanges()
    setHasUnsavedChanges(false)
    setSaveStatus('success')
    hide toast after 3s
  on error:
    setSaveStatus('error')
```

**Selected code snippets and explanations**

- `ProtectedRoute` (routing guard)

```jsx
// src/routes/ProtectedRoute.jsx
if (loading || !initialized) return <LoadingSpinner />
if (!user) return <Navigate to="/login" state={{ from: location }} replace />
if (!hasTtsAccess()) return <Navigate to="/unauthorized" replace />
if (requireAdmin && !isAdmin()) return <Navigate to="/unauthorized" replace />
return <Outlet />
```

Explanation: Shows a friendly loading state while auth initializes, enforces system-level access (TTS), then checks role-specific access.

- `AuthContext.checkAuthStatus` (token verification + refresh)

Key points:
- Uses `TokenUtils` to read/store tokens from `localStorage` or cookies.
- Verifies tokens with the auth server and fetches profile via `PROFILE_URL`.
- Attempts a single refresh when verification fails, then retries profile fetch.

- `TicketsContext.fetchTickets` (simple cache-first fetch)

```jsx
const cachedData = memoryCache.get(cacheKey)
if (cachedData) { setTickets(cachedData); return }
const response = await api.get('tasks/my-tasks/')
memoryCache.set(cacheKey, response.data)
setTickets(response.data)
```

Explanation: Simple in-memory cache reduces API load for ticket listing views; `refreshTickets` clears the cache and re-fetches.

- `WorkflowEditorLayout` (interaction patterns)

Key responsibilities:
- Load workflow data via `useWorkflowAPI().getWorkflowDetail(workflowId)`
- Manage editing state (selected node/edge), unsaved-changes flag, sidebar resizing with mouse events, save toast UI and delegation of graph operations to `WorkflowEditorContent`.

**Design decisions and trade-offs**
- Token storage: localStorage is used with a cookie fallback. This simplifies access from JS but exposes tokens to XSS. Consider using secure HttpOnly cookies for higher security.
- Auth verification + refresh: The provider attempts a refresh once to reduce forced logouts — this is user-friendly but requires secure refresh endpoints.
- In-memory cache: `memoryCache` is simple and fast, but doesn't persist across page reloads. If offline/refresh resilience is needed, consider `localStorage` or IndexedDB.

**Developer notes and next steps**
- Add an architectural diagram image (e.g., Auth flow and Workflow editor flow) to this doc for visual clarity.
- Add a short security section documenting token storage risks and mitigation (Content-Security-Policy, HttpOnly cookies, SameSite flags).
- Expand `A.3` with more component-level details (props, events) for `WorkflowEditorContent`, `WorkflowEditorSidebar`, and `WorkflowEditPanel`.
- Consider unit tests for critical logic in `TokenUtils`, `AuthContext` and `ProtectedRoute`.

---

If you want, I can:
- generate an ASCII flowchart to include here,
- expand the doc with additional code excerpts from `WorkflowEditorContent` and other pages,
- or create a small visual diagram file and add it to `frontend/docs/`.

