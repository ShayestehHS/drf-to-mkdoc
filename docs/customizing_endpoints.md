
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

#### Configuration

```python
DRF_TO_MKDOC = {
    'ENABLE_AUTO_AUTH': True,  # Enable auto-authentication (default: False)
    'AUTH_FUNCTION_JS': '''
        function getAuthHeader() {
            // Read from global config or try-it-out settings
            const config = window.DRF_TO_MKDOC_AUTH_CONFIG || {};
            const username = config.defaultUsername || 'admin';
            const password = config.defaultPassword || 'password';
            
            // Generate auth header (e.g., Basic Auth, Bearer token, etc.)
            const credentials = btoa(username + ':' + password);
            return {
                headerName: 'Authorization',
                headerValue: 'Basic ' + credentials
            };
        }
    ''',  # JavaScript code or path to JS file
    'AUTH_USERNAME': 'admin',  # Default username (optional)
    'AUTH_PASSWORD': 'password',  # Default password (optional)
}
```

#### JavaScript Function Requirements

The `getAuthHeader` function must:
- Be named exactly `getAuthHeader`
- Accept no parameters
- Return an object with `headerName` and `headerValue` properties
- Read credentials from `window.DRF_TO_MKDOC_AUTH_CONFIG` or try-it-out settings

#### Security Override in Custom Schema

You can override security requirements for specific endpoints in `custom_schema.json`:

```json
{
  "your_operation_id": {
    "is_secure": true,  // Force authentication requirement
    "need_authentication": false  // Alternative flag name
  }
}
```

- `is_secure: true` or `need_authentication: true` - Endpoint requires authentication
- `is_secure: false` or `need_authentication: false` - Endpoint does not require authentication (overrides OpenAPI security)

#### Behavior

- **When enabled**: Authentication headers are automatically added to requests for secured endpoints. The function reads from try-it-out settings if available, otherwise uses default settings.
- **When disabled**: Users can manually set authentication credentials in the try-it-out settings modal (username/password fields are shown).

#### Example: Bearer Token Authentication

```python
DRF_TO_MKDOC = {
    'ENABLE_AUTO_AUTH': True,
    'AUTH_FUNCTION_JS': '''
        function getAuthHeader() {
            // Get token from settings or make API call
            const config = window.DRF_TO_MKDOC_AUTH_CONFIG || {};
            const token = config.defaultPassword || 'your-token-here';
            return {
                headerName: 'Authorization',
                headerValue: 'Bearer ' + token
            };
        }
    ''',
    'AUTH_PASSWORD': 'your-default-token',
}
```

#### Example: Custom Authentication Service

```python
DRF_TO_MKDOC = {
    'ENABLE_AUTO_AUTH': True,
    'AUTH_FUNCTION_JS': 'path/to/auth.js',  # Path to JavaScript file
    'AUTH_USERNAME': 'user@example.com',
    'AUTH_PASSWORD': 'secret',
}
```

Where `auth.js` contains:

```javascript
async function getAuthHeader() {
    const config = window.DRF_TO_MKDOC_AUTH_CONFIG || {};
    const username = config.defaultUsername;
    const password = config.defaultPassword;
    
    // Call your authentication service
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    return {
        headerName: 'Authorization',
        headerValue: 'Bearer ' + data.token
    };
}
```
