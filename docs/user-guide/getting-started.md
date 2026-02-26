
TODO: DEMO vs Deployment

**Demo Accounts:**

| Email | Password | Role |
|-------|----------|------|
| `steward1@uni.lu` | `steward1` | Admin (Data Steward) |
| `submitter1@some.edu` | `submitter1` | Data Provider |
| `submitter2@some.edu` | `submitter2` | Data Provider |

**Configuration:**
```python
AUTHENTICATION_METHOD = 'CONFIG'
AUTHENTICATION_DICT = {
    'steward1@uni.lu': 'steward1',
    'submitter1@some.edu': 'submitter1',
    'submitter2@some.edu': 'submitter2'
}
```