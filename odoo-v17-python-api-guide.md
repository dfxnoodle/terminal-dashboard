# Odoo v17 Python External API - Comprehensive Guide

## Overview

The Odoo External API provides access to most of Odoo's features and data through XML-RPC, enabling external integration and automation. This guide covers the complete Python implementation for interacting with Odoo v17.

## Prerequisites

- Python with `xmlrpc.client` (built-in module)
- Odoo v17 instance
- Valid user credentials or API key
- Access to external API (available on Custom Odoo pricing plans only)

> **Important Note on Pricing Plans:**
> Access to data via the external API is only available on Custom Odoo pricing plans. Access to the external API is not available on One App Free or Standard plans. For more information visit the [Odoo pricing page](https://www.odoo.com/pricing-plan) or reach out to your Customer Success Manager.

> **PHP8 Compatibility Note:**
> Starting with PHP8, the XML-RPC extension may not be available by default. Check out the [manual](https://www.php.net/manual/en/xmlrpc.installation.php) for the installation steps.

## 1. Connection and Configuration

### Basic Configuration

```python
import xmlrpc.client

# Basic configuration
url = 'https://your-instance.odoo.com'  # or your server URL
db = 'your_database_name'               # database name
username = 'your_username'              # user login
password = 'your_password'              # user password or API key
```

### API Keys (Recommended - Available since v14.0)

API Keys provide secure authentication without exposing passwords:

1. **Generate API Key:**
   - Go to user Preferences → Account Security
   - Click "New API Key"
   - Provide a clear description
   - Copy the generated key immediately (cannot be retrieved later)

2. **Usage:**
```python
# Replace password with API key
api_key = 'your_generated_api_key'
password = api_key  # Use API key instead of password
```

3. **API Key Management:**
   - Description should be clear and complete - it's the only way to identify keys later
   - Store API keys as carefully as passwords - they provide the same access
   - API keys cannot be used to log into the web interface
   - Deleted API keys cannot be undeleted or re-set
   - You'll need to generate a new key and update all places where the old one was used

### Odoo Online Configuration

For Odoo Online instances (domain.odoo.com), users are created without local passwords. To use XML-RPC:

1. Log in with an administrator account
2. Go to Settings → Users & Companies → Users  
3. Click on the user for XML-RPC access
4. Click Action → Change Password
5. Set a New Password → Change Password

**Connection Details:**
- Server URL: instance domain (e.g., https://mycompany.odoo.com)
- Database name: instance name (e.g., mycompany)
- Username: user's login as shown in Change Password screen

## 2. Authentication and Connection

### Establishing Connection

```python
# Connect to common endpoint (no authentication required)
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')

# Check server version
version_info = common.version()
print(f"Server version: {version_info['server_version']}")

# Authenticate and get user ID
uid = common.authenticate(db, username, password, {})
if not uid:
    raise Exception("Authentication failed")

# Connect to object endpoint (requires authentication)
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

### Version Information Response

```python
{
    "server_version": "17.0",
    "server_version_info": [17, 0, 0, "final", 0],
    "server_serie": "17.0",
    "protocol_version": 1,
}
```

## 3. Core API Methods

### The execute_kw Function

All model operations use the `execute_kw` method with these parameters:

```python
result = models.execute_kw(
    db,           # database name
    uid,          # user ID from authentication
    password,     # password or API key
    model_name,   # model name (e.g., 'res.partner')
    method_name,  # method to call (e.g., 'search', 'read')
    args,         # positional arguments (list)
    kwargs        # keyword arguments (dict, optional)
)
```

## 4. CRUD Operations

### 4.1 Search Records

Search for records using domain filters:

```python
# Basic search - returns list of IDs
partner_ids = models.execute_kw(
    db, uid, password, 
    'res.partner', 'search', 
    [[['is_company', '=', True]]]  # domain filter
)
# Result: [7, 18, 12, 14, 17, 19, 8, 31, 26, 16, 13, 20, 30, 22, 29, 15, 23, 28, 74]

# Search with pagination
partner_ids = models.execute_kw(
    db, uid, password,
    'res.partner', 'search',
    [[['is_company', '=', True]]],
    {'offset': 10, 'limit': 5}
)
# Result: [13, 20, 30, 22, 29]
```

### 4.2 Count Records

Count records without retrieving them:

```python
count = models.execute_kw(
    db, uid, password,
    'res.partner', 'search_count',
    [[['is_company', '=', True]]]
)
# Result: 19
```

> **Note on Data Consistency:**
> Calling `search` then `search_count` (or vice versa) may not yield coherent results if other users are using the server: stored data could have changed between the calls.

### 4.3 Read Records

Retrieve record data by IDs:

```python
# Read all fields
ids = models.execute_kw(
    db, uid, password,
    'res.partner', 'search',
    [[['is_company', '=', True]]],
    {'limit': 1}
)
record = models.execute_kw(
    db, uid, password,
    'res.partner', 'read',
    [ids]
)

# Read specific fields only
records = models.execute_kw(
    db, uid, password,
    'res.partner', 'read',
    [ids],
    {'fields': ['name', 'country_id', 'email']}
)
# Result: [{"name": "Agrolait", "country_id": [21, "Belgium"], "email": "contact@agrolait.com", "id": 7}]
```

> **Note:** Even if the `id` field is not requested, it is always returned.

### 4.4 Search and Read (Combined)

Combine search and read in one operation:

```python
records = models.execute_kw(
    db, uid, password,
    'res.partner', 'search_read',
    [[['is_company', '=', True]]],
    {'fields': ['name', 'country_id', 'comment'], 'limit': 5}
)
# Result: [
#     {"comment": false, "country_id": [21, "Belgium"], "id": 7, "name": "Agrolait"},
#     {"comment": false, "country_id": [76, "France"], "id": 18, "name": "Axelor"},
#     ...
# ]
```

### 4.5 Create Records

Create new records:

```python
# Create single record
partner_id = models.execute_kw(
    db, uid, password,
    'res.partner', 'create',
    [{'name': "New Partner", 'email': 'new@partner.com', 'is_company': True}]
)
# Result: 78 (new record ID)

# Create multiple records
partner_ids = models.execute_kw(
    db, uid, password,
    'res.partner', 'create',
    [
        {'name': "Partner 1", 'email': 'partner1@example.com'},
        {'name': "Partner 2", 'email': 'partner2@example.com'}
    ]
)
```

> **Important Field Type Considerations:**
> While most value types are what you'd expect (integer for Integer, string for Char or Text):
> - **Date**, **Datetime** and **Binary** fields use string values
> - **One2many** and **Many2many** use a special command protocol (detailed in the write method section)

### 4.6 Update Records

Update existing records:

```python
# Update single record
success = models.execute_kw(
    db, uid, password,
    'res.partner', 'write',
    [[partner_id], {'name': "Updated Partner Name"}]
)

# Update multiple records
success = models.execute_kw(
    db, uid, password,
    'res.partner', 'write',
    [[id1, id2, id3], {'category_id': [(6, 0, [category_id])]}]
)
```

### 4.7 Delete Records

Delete records:

```python
success = models.execute_kw(
    db, uid, password,
    'res.partner', 'unlink',
    [[partner_id]]
)

# Verify deletion
remaining = models.execute_kw(
    db, uid, password,
    'res.partner', 'search',
    [[['id', '=', partner_id]]]
)
# Result: [] (empty list confirms deletion)
```

## 5. Field Information and Introspection

### 5.1 Get Field Information

Retrieve model field definitions:

```python
fields_info = models.execute_kw(
    db, uid, password,
    'res.partner', 'fields_get',
    [],
    {'attributes': ['string', 'help', 'type', 'required']}
)

# Result example:
# {
#     "name": {
#         "type": "char",
#         "string": "Name",
#         "required": True,
#         "help": ""
#     },
#     "email": {
#         "type": "char",
#         "string": "Email",
#         "required": False,
#         "help": ""
#     },
#     ...
# }
```

### 5.2 Check Access Rights

Verify permissions before operations:

```python
# Check if user can read the model
can_read = models.execute_kw(
    db, uid, password,
    'res.partner', 'check_access_rights',
    ['read'],
    {'raise_exception': False}
)
# Result: True or False

# Check multiple permissions
permissions = {}
for operation in ['read', 'write', 'create', 'unlink']:
    permissions[operation] = models.execute_kw(
        db, uid, password,
        'res.partner', 'check_access_rights',
        [operation],
        {'raise_exception': False}
    )
```

## 6. Domain Filters

### Common Domain Operators

```python
# Equality
[['name', '=', 'Agrolait']]

# Inequality
[['name', '!=', 'Agrolait']]

# Comparison
[['create_date', '>=', '2023-01-01']]
[['id', '>', 10]]

# Pattern matching
[['name', 'like', 'Agro%']]      # starts with 'Agro'
[['name', 'ilike', 'agro%']]     # case-insensitive
[['email', '=like', '%@gmail.com']]

# Set membership
[['id', 'in', [1, 2, 3, 4]]]
[['state', 'not in', ['draft', 'cancel']]]

# Boolean and null
[['active', '=', True]]
[['parent_id', '=', False]]      # null/empty
[['description', '!=', False]]   # not null/empty
```

### Complex Domain Logic

```python
# AND (default)
[['is_company', '=', True], ['country_id', '=', 21]]

# OR logic
['|', ['name', 'ilike', 'odoo'], ['name', 'ilike', 'agrolait']]

# NOT logic
['!', ['is_company', '=', True]]

# Complex combinations
[
    '|',
        ['is_company', '=', True],
        '&',
            ['customer_rank', '>', 0],
            ['supplier_rank', '>', 0]
]
```

## 7. Relational Field Handling

### 7.1 Many2one Fields

```python
# Read Many2one field
partners = models.execute_kw(
    db, uid, password,
    'res.partner', 'search_read',
    [[['country_id', '!=', False]]],
    {'fields': ['name', 'country_id'], 'limit': 5}
)
# Result: [{"name": "Partner", "country_id": [21, "Belgium"], "id": 1}]

# Filter by Many2one
belgian_partners = models.execute_kw(
    db, uid, password,
    'res.partner', 'search',
    [[['country_id.name', '=', 'Belgium']]]
)
```

### 7.2 One2many and Many2many Fields

```python
# Read related records
partner = models.execute_kw(
    db, uid, password,
    'res.partner', 'read',
    [[partner_id]],
    {'fields': ['name', 'category_id', 'child_ids']}
)

# Update Many2many relationships using command protocol
models.execute_kw(
    db, uid, password,
    'res.partner', 'write',
    [[partner_id]],
    {
        'category_id': [
            (6, 0, [category_id1, category_id2])  # Replace all
        ]
    }
)

# Many2many command protocol:
# (0, 0, values)     - create new record
# (1, id, values)    - update existing record
# (2, id)           - delete record (removes from database)
# (3, id)           - unlink record (removes from relation only)
# (4, id)           - link existing record
# (5,)              - unlink all records
# (6, 0, [ids])     - replace all records with provided IDs
```

## 8. Model Introspection and Dynamic Models

### 8.1 Query Available Models

```python
# Get all installed models
models_info = models.execute_kw(
    db, uid, password,
    'ir.model', 'search_read',
    [[['state', '=', 'base']]],
    {'fields': ['name', 'model', 'info']}
)

# Find specific model
partner_model = models.execute_kw(
    db, uid, password,
    'ir.model', 'search_read',
    [[['model', '=', 'res.partner']]],
    {'fields': ['name', 'model', 'field_id']}
)
```

### 8.2 Create Custom Models (Dynamic)

```python
# Create custom model
custom_model_id = models.execute_kw(
    db, uid, password,
    'ir.model', 'create',
    [{
        'name': "Custom Model",
        'model': "x_custom_model",  # Must start with 'x_'
        'state': 'manual',          # Required for custom models
    }]
)

# Add fields to custom model
field_id = models.execute_kw(
    db, uid, password,
    'ir.model.fields', 'create',
    [{
        'model_id': custom_model_id,
        'name': 'x_custom_field',
        'field_description': 'Custom Field',
        'ttype': 'char',
        'state': 'manual',
        'required': True,
    }]
)

# Use the custom model
record_id = models.execute_kw(
    db, uid, password,
    'x_custom_model', 'create',
    [{'x_custom_field': 'Test Value'}]
)
```

## 9. Error Handling and Best Practices

### 9.1 Error Handling

```python
import xmlrpc.client
from xmlrpc.client import Fault

try:
    result = models.execute_kw(
        db, uid, password,
        'res.partner', 'read',
        [[invalid_id]]
    )
except Fault as e:
    print(f"XML-RPC Fault: {e.faultCode} - {e.faultString}")
except Exception as e:
    print(f"Connection error: {e}")
```

### 9.2 Performance Best Practices

```python
# 1. Use search_read instead of separate search + read
# Bad:
ids = models.execute_kw(db, uid, password, 'res.partner', 'search', [[]])
records = models.execute_kw(db, uid, password, 'res.partner', 'read', [ids])

# Good:
records = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[]])

# 2. Limit fields to what you need
records = models.execute_kw(
    db, uid, password, 'res.partner', 'search_read',
    [[]],
    {'fields': ['name', 'email'], 'limit': 100}
)

# 3. Use pagination for large datasets
offset = 0
limit = 100
while True:
    records = models.execute_kw(
        db, uid, password, 'res.partner', 'search_read',
        [[]],
        {'offset': offset, 'limit': limit}
    )
    if not records:
        break
    
    # Process records
    for record in records:
        print(record['name'])
    
    offset += limit
```

## 10. Common Use Cases and Examples

### 10.1 Customer Management

```python
class OdooCustomerAPI:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        
        # Establish connections
        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.uid = self.common.authenticate(db, username, password, {})
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    def create_customer(self, name, email, phone=None):
        """Create a new customer"""
        customer_data = {
            'name': name,
            'email': email,
            'is_company': False,
            'customer_rank': 1,
        }
        if phone:
            customer_data['phone'] = phone
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.partner', 'create', [customer_data]
        )
    
    def find_customers(self, search_term):
        """Search customers by name or email"""
        domain = [
            '|',
            ['name', 'ilike', search_term],
            ['email', 'ilike', search_term],
            ['customer_rank', '>', 0]
        ]
        
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.partner', 'search_read',
            [domain],
            {'fields': ['name', 'email', 'phone', 'create_date']}
        )
    
    def update_customer(self, customer_id, **updates):
        """Update customer information"""
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.partner', 'write',
            [[customer_id], updates]
        )
```

### 10.2 Sales Order Processing

```python
def create_sales_order(models, db, uid, password, customer_id, order_lines):
    """Create a sales order with order lines"""
    
    # Create order header
    order_data = {
        'partner_id': customer_id,
        'order_line': []
    }
    
    # Add order lines
    for line in order_lines:
        order_line = (0, 0, {
            'product_id': line['product_id'],
            'product_uom_qty': line['quantity'],
            'price_unit': line['price'],
        })
        order_data['order_line'].append(order_line)
    
    # Create the order
    order_id = models.execute_kw(
        db, uid, password,
        'sale.order', 'create',
        [order_data]
    )
    
    return order_id

# Example usage
order_lines = [
    {'product_id': 1, 'quantity': 5, 'price': 100.0},
    {'product_id': 2, 'quantity': 2, 'price': 50.0},
]
order_id = create_sales_order(models, db, uid, password, customer_id, order_lines)
```

### 10.3 Inventory Management

```python
def check_product_stock(models, db, uid, password, product_id, location_id=None):
    """Check product stock levels"""
    domain = [['product_id', '=', product_id]]
    if location_id:
        domain.append(['location_id', '=', location_id])
    
    stock_quants = models.execute_kw(
        db, uid, password,
        'stock.quant', 'search_read',
        [domain],
        {'fields': ['location_id', 'quantity', 'reserved_quantity']}
    )
    
    total_available = sum(q['quantity'] - q['reserved_quantity'] for q in stock_quants)
    return total_available, stock_quants

def create_stock_move(models, db, uid, password, product_id, quantity, source_location, dest_location):
    """Create a stock movement"""
    move_data = {
        'name': f'Stock Move - Product {product_id}',
        'product_id': product_id,
        'product_uom_qty': quantity,
        'location_id': source_location,
        'location_dest_id': dest_location,
        'state': 'draft',
    }
    
    move_id = models.execute_kw(
        db, uid, password,
        'stock.move', 'create',
        [move_data]
    )
    
    # Confirm the move
    models.execute_kw(
        db, uid, password,
        'stock.move', 'action_confirm',
        [[move_id]]
    )
    
    return move_id
```

## 11. Data Types and Field Types

### 11.1 Field Type Mapping

| Odoo Field Type | Python Type | Notes |
|----------------|-------------|-------|
| `char` | `str` | Text field |
| `text` | `str` | Multi-line text |
| `integer` | `int` | Integer number |
| `float` | `float` | Decimal number |
| `boolean` | `bool` | True/False |
| `date` | `str` | Format: 'YYYY-MM-DD' |
| `datetime` | `str` | Format: 'YYYY-MM-DD HH:MM:SS' |
| `binary` | `str` | Base64 encoded |
| `selection` | `str` | One of predefined values |
| `many2one` | `int` or `[int, str]` | ID or [ID, display_name] |
| `one2many` | `list` | List of IDs |
| `many2many` | `list` | List of IDs |

### 11.2 Special Value Handling

```python
# Date and DateTime
from datetime import datetime, date

# Date field
date_value = date.today().strftime('%Y-%m-%d')
record_data = {'date_field': date_value}

# DateTime field  
datetime_value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
record_data = {'datetime_field': datetime_value}

# Binary field (file upload)
import base64
with open('file.pdf', 'rb') as f:
    file_content = base64.b64encode(f.read()).decode('utf-8')
record_data = {'attachment': file_content}

# Many2one field
record_data = {'partner_id': customer_id}

# Many2many field (using command protocol)
record_data = {
    'category_ids': [(6, 0, [cat1_id, cat2_id])]  # Replace all
}
```

## 12. Advanced Topics

### 12.1 Working with Workflows

```python
# Confirm a sales order
models.execute_kw(
    db, uid, password,
    'sale.order', 'action_confirm',
    [[order_id]]
)

# Cancel an order
models.execute_kw(
    db, uid, password,
    'sale.order', 'action_cancel',
    [[order_id]]
)

# Custom workflow methods
models.execute_kw(
    db, uid, password,
    'account.move', 'action_post',
    [[invoice_id]]
)
```

### 12.2 Calling Custom Methods

```python
# Call custom method defined in model
result = models.execute_kw(
    db, uid, password,
    'custom.model', 'custom_method_name',
    [arg1, arg2],  # positional arguments
    {'param1': value1, 'param2': value2}  # keyword arguments
)
```

### 12.3 Working with Attachments

```python
def upload_attachment(models, db, uid, password, model, res_id, filename, file_content):
    """Upload file attachment to record"""
    
    attachment_data = {
        'name': filename,
        'res_model': model,
        'res_id': res_id,
        'datas': base64.b64encode(file_content).decode('utf-8'),
        'type': 'binary',
    }
    
    return models.execute_kw(
        db, uid, password,
        'ir.attachment', 'create',
        [attachment_data]
    )

def download_attachment(models, db, uid, password, attachment_id):
    """Download attachment content"""
    
    attachment = models.execute_kw(
        db, uid, password,
        'ir.attachment', 'read',
        [[attachment_id]],
        {'fields': ['name', 'datas']}
    )[0]
    
    content = base64.b64decode(attachment['datas'])
    return attachment['name'], content
```

## 13. Security Considerations

### 13.1 API Key Management

```python
import os
from dotenv import load_dotenv

# Store credentials securely
load_dotenv()

url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USERNAME')
api_key = os.getenv('ODOO_API_KEY')
```

### 13.2 Access Control

```python
def safe_execute(models, db, uid, password, model, method, args=None, kwargs=None):
    """Execute with error handling and access control"""
    
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    
    try:
        # Check access rights first
        can_access = models.execute_kw(
            db, uid, password,
            model, 'check_access_rights',
            [method.split('_')[0] if '_' in method else 'read'],
            {'raise_exception': False}
        )
        
        if not can_access:
            raise PermissionError(f"No access to {method} on {model}")
        
        return models.execute_kw(db, uid, password, model, method, args, kwargs)
        
    except Exception as e:
        print(f"Error executing {method} on {model}: {e}")
        return None
```

## 14. Testing and Debugging

### 14.1 Connection Testing

```python
def test_connection(url, db, username, password):
    """Test Odoo connection and authentication"""
    
    try:
        # Test common endpoint
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        version = common.version()
        print(f"✓ Connected to Odoo {version['server_version']}")
        
        # Test authentication
        uid = common.authenticate(db, username, password, {})
        if uid:
            print(f"✓ Authenticated as user ID {uid}")
            
            # Test model access
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            partner_count = models.execute_kw(
                db, uid, password,
                'res.partner', 'search_count', [[]]
            )
            print(f"✓ Can access partners ({partner_count} records)")
            
            return True
        else:
            print("✗ Authentication failed")
            return False
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

# Usage
if test_connection(url, db, username, password):
    print("Connection successful!")
```

### 14.2 Debugging API Calls

```python
import json

def debug_execute_kw(models, db, uid, password, model, method, args=None, kwargs=None):
    """Execute with detailed logging"""
    
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    
    print(f"🔍 Calling {model}.{method}")
    print(f"   Args: {json.dumps(args, indent=2, default=str)}")
    print(f"   Kwargs: {json.dumps(kwargs, indent=2, default=str)}")
    
    try:
        result = models.execute_kw(db, uid, password, model, method, args, kwargs)
        print(f"✓ Success: {type(result)} with {len(result) if isinstance(result, list) else 1} item(s)")
        return result
    except Exception as e:
        print(f"✗ Error: {e}")
        raise
```

## 15. Conclusion

This comprehensive guide covers the essential aspects of working with Odoo v17's Python External API. Key takeaways:

1. **Always use API keys** instead of passwords for production environments
2. **Handle errors gracefully** with proper exception handling
3. **Optimize performance** by using `search_read` and limiting fields
4. **Respect access controls** and check permissions before operations
5. **Use pagination** for large datasets
6. **Store credentials securely** using environment variables

The External API provides powerful integration capabilities, enabling you to build robust applications that interact seamlessly with your Odoo instance.

For more advanced usage and model-specific operations, refer to the official Odoo documentation and explore the available models and methods through the introspection features described in this guide.
