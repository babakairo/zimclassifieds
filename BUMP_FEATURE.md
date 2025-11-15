# Bump Feature Documentation

## Overview
The **Bump Feature** allows sellers to move their listings to the top of search results and the home page, similar to Instagram and Facebook. Every time a listing is bumped, its visibility is refreshed by updating the `bumped_at` timestamp.

## How It Works

### Database Schema
- **New Column**: `bumped_at` (TIMESTAMP) added to the `listings` table
- **Default Value**: Automatically set to `CURRENT_TIMESTAMP` when listing is created
- **Updates**: Set to `CURRENT_TIMESTAMP` whenever a listing is bumped

### Sorting Strategy
Listings are now sorted by `bumped_at DESC` instead of `created_at DESC`:
- Home page (`/`) - Shows 12 most recently bumped listings
- Search results (`/search`) - Sorted by most recent bump date
- Browse results - Sorted by most recent bump date

### API Endpoint

**Route**: `POST /api/bump-listing/<listing_id>`

**Authorization**: Required (Login required)

**Ownership Check**: Only the listing owner can bump their own listing

**Response**:
```json
{
  "success": true,
  "message": "Listing bumped to top!"
}
```

**Error Responses**:
- 404: Listing not found
- 403: Unauthorized (not the listing owner)

## User Interface

### Bump Button Locations

#### 1. **Listing Detail Page** (`/listing/<id>`)
- Location: Owner-only action buttons
- Label: "⬆️ Bump to Top"
- Color: Amber (#f59e0b)
- Position: Between Edit and Delete buttons

#### 2. **User Dashboard** (`/dashboard`)
- Location: Action buttons on each listing card
- Label: "⬆️ Bump"
- Color: Amber (#f59e0b)
- Position: Left button in action buttons group

### User Flow
1. User logs into their account
2. Opens listing detail page OR dashboard
3. Clicks "⬆️ Bump to Top" button
4. System updates `bumped_at` to current timestamp
5. Listing immediately moves to top of feed
6. Success alert message is displayed
7. Page automatically refreshes (optional)

## Technical Implementation

### Backend Changes (`app.py`)

#### 1. Database Schema Update
```python
bumped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
```
Added to listings table initialization.

#### 2. New API Endpoint
```python
@app.route('/api/bump-listing/<listing_id>', methods=['POST'])
@login_required
def bump_listing(listing_id):
    # Validates ownership
    # Updates bumped_at timestamp
    # Returns JSON response
```

#### 3. Modified Routes
- `/` (index) - Now sorts by `bumped_at DESC`
- `/search` - Now sorts by `bumped_at DESC`

### Frontend Changes

#### 1. Listing Detail Template (`templates/listing_detail.html`)
- Added "⬆️ Bump to Top" button for listing owners
- Added `bumpListing()` JavaScript function
- Shows "Last Bumped" date in listing info

#### 2. Dashboard Template (`templates/dashboard.html`)
- Added action buttons to each listing card
- "⬆️ Bump" button with amber color
- Added `bumpListingFromDash()` JavaScript function
- Added `deleteListingFromDash()` JavaScript function

### JavaScript Functions

#### `bumpListing(listingId)` (Listing Detail)
```javascript
function bumpListing(listingId) {
    fetch(`/api/bump-listing/${listingId}`, {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message);
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert(data.message || 'Error bumping listing');
        }
    });
}
```

#### `bumpListingFromDash(listingId)` (Dashboard)
```javascript
function bumpListingFromDash(listingId) {
    fetch(`/api/bump-listing/${listingId}`, {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message);
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert(data.message || 'Error bumping listing');
        }
    });
}
```

## Features

### ✅ Implemented
- [x] Bump button on listing detail page (owner only)
- [x] Bump button on dashboard (for each listing)
- [x] API endpoint for bumping listings
- [x] Ownership validation
- [x] Sorting by bump date on home page
- [x] Sorting by bump date on search results
- [x] Display "Last Bumped" date on listing detail
- [x] Success notifications
- [x] Automatic page refresh after bump

### 🔄 Future Enhancements
- Bump frequency limits (e.g., 1 bump per 24 hours)
- Premium bump feature (paid bumps)
- Bump statistics (how many times bumped)
- Bump history/audit log
- Scheduled bumps (auto-bump at specific times)
- Email notifications when listing is bumped
- Estimated value increase indicator after bump

## Usage Examples

### For Sellers
1. **Daily Usage**: Open dashboard and bump listings every morning
2. **Before Event**: Bump listing before scheduled meeting time
3. **Low Traffic**: Bump listing when not getting views
4. **Special Occasion**: Bump before weekend buyers check listings

### System Behavior
- **First Created**: `bumped_at` = `created_at`
- **After Bump**: `bumped_at` = current time (moves to top)
- **Multiple Bumps**: Each bump updates timestamp (list refresh)
- **No Limit**: Users can bump unlimited times (consider adding limits)

## Testing

### Manual Testing
1. Create a listing
2. View listing detail → Verify bump button is visible
3. Click bump → Verify success message
4. Check home page → Verify listing moved to top
5. Verify in dashboard → Listing updates immediately

### Edge Cases
- Bump while listing is sold/inactive
- Bump non-existent listing
- Bump another user's listing (should be denied)
- Rapid successive bumps

## Database Migration

### For Existing Databases
If upgrading from version without bump feature:

```sql
ALTER TABLE listings ADD COLUMN bumped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
UPDATE listings SET bumped_at = updated_at WHERE bumped_at IS NULL;
```

The app will automatically handle this on first run since `CREATE TABLE IF NOT EXISTS` checks.

## Performance Considerations

- **Indexing**: Consider adding index on `bumped_at` for large datasets
- **Sorting**: Efficient TIMESTAMP sorting (no regex needed)
- **Updates**: Single-row update is fast
- **Caching**: May need to clear cache after bump if implemented

## API Response Examples

### Success
```json
{
  "success": true,
  "message": "Listing bumped to top!"
}
```

### Error - Not Found
```json
{
  "success": false,
  "message": "Listing not found"
}
```

### Error - Unauthorized
```json
{
  "success": false,
  "message": "Unauthorized"
}
```

## Security Considerations

✅ **Implemented**:
- Login required for bump action
- Ownership validation before bump
- CSRF protection via Flask session

⚠️ **Consider**:
- Rate limiting per user (prevent abuse)
- Cooldown timer between bumps
- Spam prevention for rapid bumping
- Admin controls to revert/manage bumps

## Troubleshooting

### Listing not moving to top after bump
- Verify `bumped_at` column was added to database
- Check that search/index routes are sorting by `bumped_at DESC`
- Clear browser cache

### Bump button not showing
- Verify user is logged in
- Verify user is listing owner (`session['user_id'] == listing.user_id`)
- Check template rendering

### JavaScript error when bumping
- Check browser console for errors
- Verify `/api/bump-listing/<id>` endpoint exists
- Check network tab for 404/500 responses

## Related Features
- **Image Upload**: Users can upload images when creating/editing
- **Favorites**: Users can favorite listings (not affected by bumps)
- **Search**: Filters work independently of bump sorting
- **Messages**: Messaging system unaffected by bumps

## Files Modified
- `app.py` - Added bump endpoint, updated sorting
- `templates/listing_detail.html` - Added bump button
- `templates/dashboard.html` - Added bump button to listing cards
- Database schema - Added `bumped_at` column

## Summary
The bump feature successfully enables sellers to refresh their listings' visibility, keeping their ads at the top of the feed like modern social platforms. This encourages engagement and provides sellers with a tool to improve their listing's exposure.
