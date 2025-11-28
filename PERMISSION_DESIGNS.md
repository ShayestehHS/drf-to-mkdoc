# 5 Design Options for Endpoint Permissions Display
*Updated to match current design system*

## Design 1: Table Format (Matches Existing Style)
```
# POST /api/users/

[POST] `/api/users/`

**View class:** UserViewSet

## Permissions <span class="hint-icon" tabindex="0" data-tooltip="Access control requirements for this endpoint. All listed permissions must be satisfied unless otherwise specified." aria-label="Information about permissions" title="Access control requirements for this endpoint">ℹ️</span>

| Permission | Required | Description |
|------------|----------|-------------|
| `IsAuthenticated` | Yes | User must be authenticated |
| `IsAdminUser` | Yes | User must have administrator privileges |

**Combined Logic:** All permissions must be satisfied (AND)

**Full Permission Classes:**
- `rest_framework.permissions.IsAuthenticated`
- `rest_framework.permissions.IsAdminUser`

## Overview
...
```

**Visual Style:**
- Matches existing table format (same as Path Parameters, Query Parameters)
- Uses hint-icon (ℹ️) with tooltip for explanation
- Shows permission name, required status, and description
- Displays combination logic and full class names below
- Consistent with current design patterns

---

## Design 2: Badge List with Table Details
```
# POST /api/users/

[POST] `/api/users/`

**View class:** UserViewSet

## Permissions <span class="hint-icon" tabindex="0" data-tooltip="Access control requirements for this endpoint." aria-label="Information about permissions" title="Access control requirements for this endpoint">ℹ️</span>

**Required:** `IsAuthenticated` `IsAdminUser`

| Permission | Type | Description |
|------------|------|-------------|
| `IsAuthenticated` | Required | User must be authenticated |
| `IsAdminUser` | Required | User must have administrator privileges |

**Combined Logic:** All permissions must be satisfied (AND)

**Full Permission Classes:**
- `rest_framework.permissions.IsAuthenticated`
- `rest_framework.permissions.IsAdminUser`

## Overview
...
```

**Visual Style:**
- Badge-style inline display at top (using code formatting like method badges)
- Detailed table below for full information
- Quick visual scan with detailed reference
- Matches existing badge + table pattern

---

## Design 3: Simple List Format
```
# POST /api/users/

[POST] `/api/users/`

**View class:** UserViewSet

## Permissions <span class="hint-icon" tabindex="0" data-tooltip="Access control requirements for this endpoint." aria-label="Information about permissions" title="Access control requirements for this endpoint">ℹ️</span>

**Required Permissions:**
- `IsAuthenticated` - User must be authenticated
- `IsAdminUser` - User must have administrator privileges

**Combined Logic:** All permissions must be satisfied (AND)

**Full Permission Classes:**
- `rest_framework.permissions.IsAuthenticated`
- `rest_framework.permissions.IsAdminUser`

## Overview
...
```

**Visual Style:**
- Simple markdown list format
- Clean and minimal
- Easy to read and scan
- Consistent with markdown documentation style
- Less structured than table but more readable

---

## Design 4: Compact Inline with Expandable Section
```
# POST /api/users/

[POST] `/api/users/`

**View class:** UserViewSet

**Permissions:** `IsAuthenticated` `IsAdminUser` <span class="hint-icon" tabindex="0" data-tooltip="Click to view detailed permission information" aria-label="View permission details" title="Click to view detailed permission information">ℹ️</span>

<details>
<summary>View Permission Details</summary>

| Permission | Required | Description |
|------------|----------|-------------|
| `IsAuthenticated` | Yes | User must be authenticated |
| `IsAdminUser` | Yes | User must have administrator privileges |

**Combined Logic:** All permissions must be satisfied (AND)

**Full Permission Classes:**
- `rest_framework.permissions.IsAuthenticated`
- `rest_framework.permissions.IsAdminUser`

</details>

## Overview
...
```

**Visual Style:**
- Compact inline display (similar to "View class" line)
- Expandable details section using HTML `<details>` tag
- Space-efficient for simple cases
- Progressive disclosure for detailed information
- Maintains clean page layout

---

## Design 5: Table with Logic Column (For Complex Permissions)
```
# POST /api/users/

[POST] `/api/users/`

**View class:** UserViewSet

## Permissions <span class="hint-icon" tabindex="0" data-tooltip="Access control requirements for this endpoint. Logic column shows how permissions are combined." aria-label="Information about permissions" title="Access control requirements for this endpoint">ℹ️</span>

| Permission | Required | Logic | Description |
|------------|----------|-------|-------------|
| `IsAuthenticated` | Yes | AND | User must be authenticated |
| `IsAdminUser` | Yes | AND | User must have administrator privileges |

**Combined Logic:** `IsAuthenticated` AND `IsAdminUser`

**Full Permission Classes:**
- `rest_framework.permissions.IsAuthenticated`
- `rest_framework.permissions.IsAdminUser`

### Complex Permission Example (with OR logic):

| Permission | Required | Logic | Description |
|------------|----------|-------|-------------|
| `IsAuthenticated` | Yes | AND | User must be authenticated |
| `IsAdminUser` | No | OR | User must have admin role OR be resource owner |
| `IsOwner` | No | OR | User must be resource owner |

**Combined Logic:** `IsAuthenticated` AND (`IsAdminUser` OR `IsOwner`)

## Overview
...
```

**Visual Style:**
- Table format with additional "Logic" column
- Shows AND/OR relationships directly in table
- Best for complex nested permissions
- Clear visualization of permission combinations
- Still matches existing table styling

---

## Comparison Summary

| Design | Best For | Pros | Cons |
|--------|----------|------|------|
| **1. Table Format** | All cases, consistency | Matches existing style exactly, detailed, familiar | More vertical space |
| **2. Badge List + Table** | Quick reference needed | Quick visual scan + detailed info | Slightly redundant |
| **3. Simple List** | Minimal design preference | Clean, readable, markdown-native | Less structured |
| **4. Compact Inline** | Space-constrained pages | Very space-efficient, progressive disclosure | Requires interaction to see details |
| **5. Table with Logic** | Complex nested permissions | Clear AND/OR visualization, structured | More columns, wider table |

---

## Recommendation for Front-End Developers

For a documentation tool targeting front-end developers, I recommend **Design 1 (Table Format)** because:

1. **Perfect consistency** - Matches existing Path Parameters and Query Parameters tables exactly
2. **Familiar pattern** - Developers already know how to read these tables
3. **Complete information** - Shows all necessary details without requiring interaction
4. **Hint icon support** - Uses existing tooltip system for explanations
5. **Easy implementation** - Follows exact same template pattern as other sections

**Alternative:** If space is a concern, **Design 4 (Compact Inline)** provides a good balance with progressive disclosure, but Design 1 is the safest choice for consistency.

---

## Implementation Notes

All designs follow the current design system:
- ✅ Use markdown format with `##` headers
- ✅ Include hint-icon (ℹ️) with tooltips
- ✅ Use code formatting with backticks for permission names
- ✅ Match table styling from Path/Query Parameters
- ✅ Place after "View class" and before "Overview" section
- ✅ Use consistent spacing and formatting

---

## Visual Context: How Designs Appear on Page

### Current Page Structure (Reference)
```
┌─────────────────────────────────────────────────────────────┐
│  # POST /api/users/                                          │
│                                                               │
│  [POST] `/api/users/`                                        │
│                                                               │
│  **View class:** UserViewSet                                 │
│                                                               │
│  ## Overview                                                 │
│  Create a new user account                                   │
│                                                               │
│  ## Path Parameters                                          │
│  ┌──────────┬──────┬──────────┬─────────────┐             │
│  │ Name     │ Type │ Required │ Description │             │
│  ├──────────┼──────┼──────────┼─────────────┤             │
│  │ `id`     │ int  │ Yes      │ User ID     │             │
│  └──────────┴──────┴──────────┴─────────────┘             │
│                                                               │
│  ## Query Parameters                                         │
│  ### Filter Fields ℹ️                                        │
│  ┌──────────┬──────┬──────────┬─────────────┐             │
│  │ Name     │ Type │ Required │ Description │             │
│  └──────────┴──────┴──────────┴─────────────┘             │
│                                                               │
│  ## Request Body                                             │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

### Design 1 in Context (Table Format - RECOMMENDED)
```
┌─────────────────────────────────────────────────────────────┐
│  # POST /api/users/                                          │
│                                                               │
│  [POST] `/api/users/`                                        │
│                                                               │
│  **View class:** UserViewSet                                 │
│                                                               │
│  ## Permissions ℹ️                                           │
│  ┌──────────────────┬──────────┬──────────────────────────┐ │
│  │ Permission       │ Required │ Description             │ │
│  ├──────────────────┼──────────┼──────────────────────────┤ │
│  │ `IsAuthenticated`│ Yes      │ User must be auth'd      │ │
│  │ `IsAdminUser`    │ Yes      │ Admin privileges needed  │ │
│  └──────────────────┴──────────┴──────────────────────────┘ │
│  **Combined Logic:** All permissions must be satisfied (AND) │
│                                                               │
│  ## Overview                                                 │
│  Create a new user account                                   │
│                                                               │
│  ## Path Parameters                                          │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

### Design 2 in Context (Badge List + Table)
```
┌─────────────────────────────────────────────────────────────┐
│  # POST /api/users/                                          │
│                                                               │
│  [POST] `/api/users/`                                        │
│                                                               │
│  **View class:** UserViewSet                                 │
│                                                               │
│  ## Permissions ℹ️                                           │
│  **Required:** `IsAuthenticated` `IsAdminUser`               │
│                                                               │
│  ┌──────────────────┬──────────┬──────────────────────────┐ │
│  │ Permission       │ Required │ Description             │ │
│  ├──────────────────┼──────────┼──────────────────────────┤ │
│  │ `IsAuthenticated`│ Yes      │ User must be auth'd      │ │
│  │ `IsAdminUser`    │ Yes      │ Admin privileges needed  │ │
│  └──────────────────┴──────────┴──────────────────────────┘ │
│                                                               │
│  ## Overview                                                 │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

### Design 3 in Context (Simple List)
```
┌─────────────────────────────────────────────────────────────┐
│  # POST /api/users/                                          │
│                                                               │
│  [POST] `/api/users/`                                        │
│                                                               │
│  **View class:** UserViewSet                                 │
│                                                               │
│  ## Permissions ℹ️                                           │
│  **Required Permissions:**                                   │
│  - `IsAuthenticated` - User must be authenticated            │
│  - `IsAdminUser` - User must have administrator privileges  │
│                                                               │
│  **Combined Logic:** All permissions must be satisfied (AND) │
│                                                               │
│  ## Overview                                                 │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

### Design 4 in Context (Compact Inline)
```
┌─────────────────────────────────────────────────────────────┐
│  # POST /api/users/                                          │
│                                                               │
│  [POST] `/api/users/`                                        │
│                                                               │
│  **View class:** UserViewSet                                 │
│  **Permissions:** `IsAuthenticated` `IsAdminUser` ℹ️         │
│                                                               │
│  <details>                                                    │
│  <summary>View Permission Details</summary>                   │
│  [Table with full details - hidden by default]               │
│  </details>                                                   │
│                                                               │
│  ## Overview                                                 │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

### Design 5 in Context (Table with Logic Column)
```
┌─────────────────────────────────────────────────────────────┐
│  # POST /api/users/                                          │
│                                                               │
│  [POST] `/api/users/`                                        │
│                                                               │
│  **View class:** UserViewSet                                 │
│                                                               │
│  ## Permissions ℹ️                                           │
│  ┌──────────────┬──────────┬──────┬──────────────────────┐ │
│  │ Permission   │ Required │ Logic│ Description          │ │
│  ├──────────────┼──────────┼──────┼──────────────────────┤ │
│  │ `IsAuth...`  │ Yes      │ AND  │ User must be auth'd  │ │
│  │ `IsAdmin...` │ Yes      │ AND  │ Admin privileges     │ │
│  └──────────────┴──────────┴──────┴──────────────────────┘ │
│                                                               │
│  ## Overview                                                 │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

