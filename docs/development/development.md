## Quick Start (Recommended)

For most users, this is all you need:

```bash
# First time setup (creates venv, installs deps, builds CSS, initializes DB)
./setup_dev.sh

# Start the development server
./run_dev.sh
```

Application runs at **http://127.0.0.1:5000**

**Demo Login Credentials:**
- Admin: `steward1@uni.lu` / `steward1`
- Data Provider: `submitter1@some.edu` / `submitter1`

### Daily Development

**Starting the server:**
```bash
./run_dev.sh
```

**Auto-compile SCSS on file changes (optional, in a separate terminal):**
```bash
cd elixir_dss/static/vendor && npm run watch:css
```

Edit `.scss` files → auto-recompiles → refresh browser to see changes!

## Technical Implementation Notes

### Authorization Decorator

The system uses `@app_authorization` decorator for access control:

```python
@app_authorization(
    allowed_roles=['admin', 'data_provider'],
    record_authorization={
        'entity': 'Submission',
        'entity_id_key': 'sub_id',
        'entity_ac_attribute': 'id'
    }
)
```

**Logic:**
1. Check if user is authenticated
2. Check if user has one of the allowed roles
3. If not admin + record_authorization specified:
   - Fetch the entity (e.g., Submission)
   - Check if user has `SubmissionAccess` for that entity
   - Deny access if no access record found

### Service Layer Functions

Key service functions in `models/services.py`:

- `create_sub()`: Creates new submission with auto-generated ref_name
- `delete_sub()`: Deletes submission (only if deletable)
- `steer_sub()`: Moves submission to next state + sends notifications
- `revert_sub()`: Moves submission to previous state
- `has_access()`: Checks if user has access to submission
- `get_in_progress_submissions_shared_with_user()`: Returns visible submissions for data provider
- `assign_role_to_user()`: Assigns role to user
- `register_new_user()`: Creates new user account

