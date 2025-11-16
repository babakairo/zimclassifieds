# Police Clearance Requirement - Implementation Summary

## Overview
Added mandatory police clearance certificate requirement for all transporter/driver registrations to ensure background checks are completed before drivers can access the delivery network.

## Changes Made

### 1. Database Schema Updates

#### SQLite (app.py)
Added three new columns to the `transporters` table:
- `police_clearance` (TEXT) - Certificate number **(REQUIRED)**
- `clearance_issue_date` (TEXT) - Issue date
- `clearance_expiry_date` (TEXT) - Expiry date

#### PostgreSQL (create_postgres_schema.py)
Added three new columns to the `transporters` table:
- `police_clearance` (VARCHAR(100)) - Certificate number **(REQUIRED)**
- `clearance_issue_date` (VARCHAR(20)) - Issue date
- `clearance_expiry_date` (VARCHAR(20)) - Expiry date

### 2. Backend Changes (transporters.py)

#### Registration Handler Updates:
- Added form fields to capture police clearance information
- Updated validation to require `police_clearance` field
- Modified INSERT statement to include all three police clearance fields
- Enhanced error message to mention police clearance requirement

### 3. Frontend Changes (templates/transporters/register.html)

#### New Form Section:
- Added warning alert explaining background check requirement
- Added required field for police clearance certificate number
- Added optional fields for issue and expiry dates
- Updated help text to explain verification process
- Enhanced note section to mention certificate verification

### 4. Migration Script (add_police_clearance_column.py)

Created automated migration script that:
- Adds police clearance columns to existing SQLite databases
- Adds police clearance columns to existing PostgreSQL databases
- Checks if columns already exist before adding
- Provides clear success/error messages
- Handles both database types automatically

## Migration Status

✅ **SQLite Migration Complete**
- Police clearance columns added successfully
- Existing database updated

⏳ **PostgreSQL Migration Pending**
- Will run automatically when `DATABASE_URL` is set
- No action needed - script handles it automatically

## Security Features

1. **Mandatory Requirement**: Registration form validation ensures police clearance certificate number is provided
2. **Verification Notice**: Clear messaging that certificates will be verified with authorities
3. **Pending Status**: All new transporter accounts start with `status='pending'` until verified
4. **24-Hour Review**: Admin verification required before account activation

## Testing Checklist

To test the new police clearance requirement:

- [ ] Navigate to http://127.0.0.1:5001/transporters/register
- [ ] Try submitting form without police clearance - should show error
- [ ] Fill in all required fields including police clearance certificate number
- [ ] Verify optional issue/expiry date fields work
- [ ] Confirm registration creates account with pending status
- [ ] Verify database stores all three police clearance fields
- [ ] Check that transporter cannot login until admin verifies and activates account

## Next Steps

### For Development:
- Test the registration form with police clearance requirement
- Verify validation works correctly
- Ensure data is stored properly in database

### For Production:
1. Run migration script before deploying: `python add_police_clearance_column.py`
2. Deploy updated code
3. Update admin verification process to include police clearance verification
4. Consider adding:
   - Document upload functionality (scan of certificate)
   - Automated expiry date alerts
   - Integration with Zimbabwe Republic Police API (if available)
   - Renewal reminder system for expiring clearances

## Admin Verification Process

When verifying transporter accounts, admins should:

1. Verify police clearance certificate number with Zimbabwe Republic Police
2. Check expiry date to ensure certificate is current
3. Confirm other documents (ID, driver's license)
4. Update transporter status from 'pending' to 'active'
5. Set `verified_at` timestamp

## Database Queries

### Check Transporter Police Clearance:
```sql
SELECT full_name, email, police_clearance, clearance_expiry_date, status
FROM transporters t
JOIN users u ON t.user_id = u.user_id
WHERE t.status = 'pending';
```

### Find Expiring Clearances:
```sql
SELECT full_name, email, police_clearance, clearance_expiry_date
FROM transporters t
JOIN users u ON t.user_id = u.user_id
WHERE t.status = 'active'
AND date(t.clearance_expiry_date) <= date('now', '+30 days');
```

## Files Modified

1. `app.py` - Updated transporters table schema
2. `transporters.py` - Updated registration logic and validation
3. `templates/transporters/register.html` - Added police clearance form fields
4. `create_postgres_schema.py` - Updated PostgreSQL schema
5. `add_police_clearance_column.py` - New migration script (created)

## Notes

- Police clearance is now a **mandatory requirement** for all new driver registrations
- Existing transporters (if any) will need to update their profiles with clearance information
- The system is designed to work with Zimbabwe Republic Police clearance certificates
- Certificates should be verified by admin before activating accounts
- Consider implementing automated expiry notifications in the future
