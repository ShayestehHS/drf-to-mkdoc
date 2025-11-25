
# Customizing API Endpoint Documentation

`drf-to-mkdoc` automatically generates API documentation from your Django REST Framework (DRF) project using the OpenAPI schema from **DRF Spectacular**. You can refine and extend that documentation using a **custom JSON file** and various configuration options.

---

## 1. Where to put your custom schema

By default, the generator looks for:
docs/configs/custom\_schema.json




You can change this path by setting `CUSTOM_SCHEMA_FILE` in your `DRF_TO_MKDOC` settings.

---

## 2. JSON File Format

The file should be a JSON object where **keys are `operationId`s** from your OpenAPI schema. Each key can override or extend the operation’s documentation.

Supported fields for each operation:

- `description` → Text description of the endpoint  
- `parameters` → Array of OpenAPI parameter objects  
- `requestBody` → OpenAPI RequestBody object  
- `responses` → OpenAPI Responses object  
- `append_fields` → A list of keys that should **append to existing lists instead of replacing them**.  
   - Currently, this is only useful for fields that are arrays in the schema (e.g., `parameters`).  
   - If the target field is not a list (like `description`, `responses`, or `requestBody`), `append_fields` is ignored and the value is replaced as usual.  
   - Example: If you want to **keep auto-generated query parameters** and add your own, include `"parameters"` in `append_fields`.  

---

### Example `custom_schema.json` using all supported keys

```json
{
  "clinic_panel_appointments_available_appointment_times_list": {
    "description": "Shows all available appointment times for a clinic.",
    "parameters": [
      {
        "name": "date",
        "in": "query",
        "description": "Filter appointments by date",
        "required": false,
        "schema": { "type": "string", "format": "date" },
        "queryparam_type": "filter_fields"
      },
      {
        "name": "search",
        "in": "query",
        "description": "Search appointments by doctor or patient name",
        "required": false,
        "schema": { "type": "string" },
        "queryparam_type": "search_fields"
      }
    ],
    "requestBody": {
      "description": "Request body for creating an appointment",
      "required": true,
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "doctor_id": { "type": "integer" },
              "patient_id": { "type": "integer" },
              "date": { "type": "string", "format": "date" },
              "time_slot": { "type": "string" }
            },
            "required": ["doctor_id", "patient_id", "date", "time_slot"]
          }
        }
      }
    },
    "responses": {
      "200": {
        "description": "List of available time slots",
        "content": {
          "application/json": {
            "schema": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "date": { "type": "string", "description": "Date in DATE_FORMAT" },
                  "time_slots": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "start_datetime": { "type": "string", "description": "Start datetime" },
                        "end_datetime": { "type": "string", "description": "End datetime" }
                      },
                      "required": ["start_datetime", "end_datetime"]
                    },
                    "description": "Available time slots for the date"
                  }
                },
                "required": ["date", "time_slots"]
              }
            }
          }
        }
      },
      "404": {
        "description": "No appointments found for the given filters",
        "content": {
          "application/json": {
            "schema": {
              "type": "object",
              "properties": {
                "detail": { "type": "string", "example": "Appointments not found" }
              },
              "required": ["detail"]
            }
          }
        }
      }
    },
    "append_fields": ["parameters"]
  }
}
````

---

## 3. Adding Query Parameters

If you add a **query parameter** (`"in": "query"`), include a `queryparam_type` so it’s categorized properly in the generated docs.

Supported `queryparam_type` values:

* `search_fields` → Used for search filters
* `filter_fields` → Standard filters
* `ordering_fields` → Sort fields
* `pagination_fields` → Pagination-related fields

> ⚠️ If `queryparam_type` is missing or invalid, the generator will raise an error.

---

## 4. How the custom schema is applied

1. `drf-to-mkdoc` loads your OpenAPI schema.
2. It reads your `custom_schema.json`.
3. For each `operationId` in your JSON:

   * Finds the corresponding endpoint in the schema
   * Replaces fields like `description`, `responses`, `parameters`, etc.
   * Appends items for fields listed in `append_fields` instead of replacing
4. Generates your markdown documentation using the merged schema

---

## 5. Finding `operationId`s

`operationId`s are generated by DRF Spectacular. You can find them by:

* Checking your API endpoint pages in the browser (each includes the `operationId`)
* Inspecting the OpenAPI JSON/YAML schema (via `/schema/` endpoint or export)

---

## 6. Tips for smooth usage

* Keep `custom_schema.json` in version control so your team benefits.
* Start small: add descriptions first, then parameters, then responses.
* Use `append_fields` if you want to **add extra info** without overwriting auto-generated items.

---

## 7. Advanced Configuration Options

### Field Generators
You can define custom field value generators for better example generation:

```python
DRF_TO_MKDOC = {
    'DJANGO_APPS': ['your_apps'],
    'FIELD_GENERATORS': {
        'created_at': datetime.now.strftime(settings.CUSTOM_DATETIME_FORMAT),
        'phone_number': generate_phone_number_function,
    },
}
```

### Path Parameter Substitution
Customize how path parameters are handled:

```python
DRF_TO_MKDOC = {
    'PATH_PARAM_SUBSTITUTE_FUNCTION': 'your_app.utils.custom_substitute',
    'PATH_PARAM_SUBSTITUTE_MAPPING': {
        'pk': 'id',
        'uuid': 'identifier',
    },
}
```

### Auto-Authentication

The auto-authentication feature automatically generates authentication headers for endpoints that require authentication. This feature can be enabled/disabled and uses a configurable JavaScript function to generate header name and value.

> ⚠️ **Security note:** Auto-auth is intended for local or staging documentation environments only. Never rely on it for production portals that expose real credentials or tokens—ship a production-ready auth experience instead.

#### Configuration

```python
DRF_TO_MKDOC = {
    'ENABLE_AUTO_AUTH': True,  # Enable auto-authentication (default: False)
    'AUTH_FUNCTION_JS': '''
        function getAuthHeader() {
            // Fetch or derive credentials however your docs app requires
            const username = 'docs-user'; // Replace with secure retrieval
            const password = 'password';  // Never store real secrets in source control
            
            // Generate auth header (e.g., Basic Auth, Bearer token, etc.)
            const credentials = btoa(username + ':' + password);
            return {
                headerName: 'Authorization',
                headerValue: 'Basic ' + credentials
            };
        }
    ''',  # JavaScript code or path to JS file
}
```

#### JavaScript Function Requirements

The `getAuthHeader` function must:
- Be named exactly `getAuthHeader`
- Accept no parameters
- Return an object with `headerName` and `headerValue` properties (or a Promise that resolves to that object)
- Handle any credential lookup or authentication flow internally (e.g., call your auth API, read from secure storage, etc.)

#### Security Override in Custom Schema

You can override security requirements for specific endpoints in `custom_schema.json`:

```json
{
  "your_operation_id": {
    "need_authentication": true  // Force authentication requirement
  }
}
```

- `need_authentication: true` - Endpoint requires authentication
- `need_authentication: false` - Endpoint does not require authentication (overrides OpenAPI security)

#### Behavior

- **When enabled**: Secured endpoints show an auto-auth prompt that calls your `getAuthHeader` helper and injects the returned header into the current try-it-out form. Right before submission we run a last-minute `getAuthHeader` call (if needed) to ensure the header field is populated, but the header ultimately lives in the form inputs—not in some hidden transport layer.
- **When disabled**: Users can manually set authentication credentials in the try-it-out settings modal (username/password fields are shown).

#### Example: Bearer Token Authentication

```python
DRF_TO_MKDOC = {
    'ENABLE_AUTO_AUTH': True,
    'AUTH_FUNCTION_JS': '''
        function getAuthHeader() {
            // Get token from settings or make API call
            return {
                headerName: 'Authorization',
                headerValue: 'Bearer ' + 'your-token-here'
            };
        }
    ''',
}
```

#### Example: Custom Authentication Service

```python
DRF_TO_MKDOC = {
    'ENABLE_AUTO_AUTH': True,
    'AUTH_FUNCTION_JS': 'static/js/auth.js',  # Path to JavaScript file (relative to project root)
}
```

> ⚠️ **Security Note:** File paths must be within your project's trusted directories (e.g., `static/`). Avoid loading auth functions from user-controlled or external paths.

Where `auth.js` contains:

```javascript
async function getAuthHeader() {
    // Fetch credentials from whatever secure source you prefer
    const username = 'user@example.com';
    const password = 'password-from-secure-source';

    // Call your authentication service
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
        throw new Error('Authentication failed');
    }

    const data = await response.json();
    return {
        headerName: 'Authorization',
        headerValue: 'Bearer ' + data.token
    };
}
```

#### Content Security Policy (CSP)

If your site uses Content Security Policy headers, you'll need to configure CSP to allow the auto-authentication feature to work. The feature injects inline JavaScript from the `AUTH_FUNCTION_JS` setting.

### Option 1: Allow inline scripts (less secure)

If you're using `django-csp` or similar middleware, you can allow inline scripts:

```python
# settings.py
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'"]
```

> ⚠️ **Security Warning:** Allowing `'unsafe-inline'` reduces CSP protection. Only use this in development or internal documentation environments.

### Option 2: Use nonces (recommended)

For better security, use CSP nonces. The templates automatically support nonces if available:

1. Configure your CSP middleware to generate nonces:

```python
# If using django-csp
CSP_SCRIPT_SRC = ["'self'"]
CSP_INCLUDE_NONCE_IN = ['script-src']
```

2. Make the nonce available in request context:

```python
# middleware.py or view context processor
def csp_nonce(request):
    if hasattr(request, 'csp_nonce'):
        return {'csp_nonce': request.csp_nonce}
    return {}
```

3. The templates will automatically use the nonce:

```html
<script nonce="{{ request.csp_nonce }}">
    // Auth function code
</script>
```

### Option 3: External script file (most secure)

For maximum security, store your auth function in an external JavaScript file and reference it:

> **Why this is more secure:** External files work natively with strict CSP policies (e.g., `CSP_SCRIPT_SRC = ["'self'"]`) without requiring `'unsafe-inline'` or nonces. This prevents inline script injection attacks and is the recommended approach for production or security-sensitive environments.

```python
DRF_TO_MKDOC = {
    'ENABLE_AUTO_AUTH': True,
    'AUTH_FUNCTION_JS': 'static/js/auth-config.js',  # External file
}
```

Then load it as a regular script tag (no inline-script CSP exceptions needed):

```html
<script src="{% static 'js/auth-config.js' %}" defer></script>
```

### Security Best Practices

- Never store production credentials in JavaScript code
- Use external files or secure credential storage for production
- Implement rate limiting on authentication endpoints
- Use HTTPS in production
- Consider using environment-specific configurations
