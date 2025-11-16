# ZimClassifieds Pre-Launch Manual Testing Checklist

## 🔧 Automated Tests Status
Run `python test_functionality.py` - **All tests should PASS**

---

## 1. User Registration & Authentication

### Regular User Registration (http://localhost:5001/register)
- [ ] Form loads without errors
- [ ] Email validation works
- [ ] Password confirmation validation works
- [ ] Successful registration redirects to login
- [ ] Error messages display correctly for:
  - [ ] Missing fields
  - [ ] Password mismatch
  - [ ] Duplicate email

### User Login (http://localhost:5001/login)
- [ ] Login form loads
- [ ] Valid credentials log in successfully
- [ ] Invalid credentials show error
- [ ] Session persists after login
- [ ] Logout works properly

---

## 2. Seller Registration & Dashboard

### Seller Registration (http://localhost:5001/sellers/register)
- [ ] Registration form loads
- [ ] All required fields validated:
  - [ ] Store name
  - [ ] Email
  - [ ] Password
  - [ ] Full name
- [ ] Store slug generated correctly
- [ ] Duplicate store name shows error
- [ ] Successful registration creates both user and seller

### Seller Login (http://localhost:5001/sellers/login)
- [ ] Login works with seller credentials
- [ ] Redirects to seller dashboard

### Seller Dashboard (http://localhost:5001/sellers/dashboard)
- [ ] Dashboard loads after login
- [ ] Statistics display correctly:
  - [ ] Total products
  - [ ] Total orders
  - [ ] Pending orders
  - [ ] Total sales
- [ ] Recent orders table displays
- [ ] Quick actions work (Products, Orders, etc.)

---

## 3. Product Management

### Create Product (http://localhost:5001/sellers/product/new)
- [ ] Form loads for logged-in seller
- [ ] All fields present:
  - [ ] Name (required)
  - [ ] Description
  - [ ] Category (required, dropdown)
  - [ ] Price (required, > 0)
  - [ ] SKU (optional, must be unique)
  - [ ] Stock quantity (required, >= 0)
  - [ ] Images (multiple upload)
- [ ] Image upload validation:
  - [ ] Can upload up to 10 images
  - [ ] Only jpg, jpeg, png, gif allowed
  - [ ] File size limit enforced (5MB)
  - [ ] Image preview shows before upload
  - [ ] First image automatically set as primary
- [ ] Form validation works:
  - [ ] Required fields checked
  - [ ] Price must be > 0
  - [ ] Stock must be >= 0
  - [ ] Duplicate SKU rejected
- [ ] Successful creation redirects to products list

### Edit Product (http://localhost:5001/sellers/product/edit/<id>)
- [ ] Edit form loads with existing data
- [ ] Can update all fields
- [ ] Existing images display
- [ ] Can delete existing images
- [ ] Can set different image as primary
- [ ] Can upload additional images (respects 10 limit)
- [ ] Save updates product successfully

### Product List (http://localhost:5001/sellers/products)
- [ ] Shows all seller's products
- [ ] Edit button works
- [ ] Delete button works (with confirmation)
- [ ] Stock status visible

---

## 4. Product Browsing (Customer View)

### Product Listing (http://localhost:5001/products)
- [ ] Page loads without errors
- [ ] Products display in grid
- [ ] Each product shows:
  - [ ] Primary image (or placeholder)
  - [ ] Name
  - [ ] Price
  - [ ] Seller name
  - [ ] Rating (if available)
  - [ ] In stock status
- [ ] Search box works
- [ ] Category filter works
- [ ] Sort options work:
  - [ ] Newest
  - [ ] Price (low to high)
  - [ ] Price (high to low)
  - [ ] Rating
- [ ] Clicking product goes to detail page

### Product Detail (http://localhost:5001/product/<id>)
- [ ] Page loads without errors
- [ ] Product information displays:
  - [ ] Name
  - [ ] Price
  - [ ] Description
  - [ ] Category
  - [ ] Stock quantity
  - [ ] SKU (if available)
- [ ] Image gallery works:
  - [ ] Main image displays
  - [ ] Thumbnails show if multiple images
  - [ ] Clicking thumbnail changes main image
  - [ ] Placeholder shows if no images
- [ ] Seller information displays:
  - [ ] Store name
  - [ ] Seller rating
  - [ ] Link to seller store
- [ ] Add to cart button works
- [ ] Reviews section displays (if any)

### Search (http://localhost:5001/products?search=<term>)
- [ ] Search results display
- [ ] Results match search term
- [ ] No results message shows appropriately

---

## 5. Shopping Cart & Checkout

### Shopping Cart (http://localhost:5001/cart/)
- [ ] Cart page loads
- [ ] Cart items display correctly
- [ ] Quantity can be updated
- [ ] Remove item works
- [ ] Subtotal calculates correctly
- [ ] Empty cart shows message
- [ ] "Continue Shopping" button works
- [ ] "Proceed to Checkout" button works

### Checkout (http://localhost:5001/checkout/)
- [ ] Checkout form loads
- [ ] Shipping address fields present
- [ ] Payment options available
- [ ] Order summary displays correctly
- [ ] Total amount correct
- [ ] Place order button works
- [ ] Validation on required fields

### Order Confirmation (http://localhost:5001/checkout/confirmation/<order_id>)
- [ ] Confirmation page displays
- [ ] Order ID shown
- [ ] Order details correct
- [ ] Shipping address correct
- [ ] Payment status shown
- [ ] "Continue Shopping" link works

---

## 6. Transporter Registration & Dashboard

### Transporter Registration (http://localhost:5001/transporters/register)
- [ ] Registration form loads
- [ ] All required fields present:
  - [ ] Full name
  - [ ] Email
  - [ ] Password
  - [ ] Phone
  - [ ] Transport type (dropdown: Motorcycle, Car, Van, Truck)
  - [ ] Vehicle registration
  - [ ] Vehicle make/model
  - [ ] Service type (Local, Regional, Both)
  - [ ] Primary city (dropdown)
  - [ ] Coverage areas (multiple checkboxes)
  - [ ] ID number
  - [ ] Driver's license
- [ ] Form validation works
- [ ] Primary city auto-selected in coverage
- [ ] Successful registration creates transporter account

### Transporter Login (http://localhost:5001/transporters/login)
- [ ] Login form loads
- [ ] Login works with transporter credentials
- [ ] Redirects to transporter dashboard

### Transporter Dashboard (http://localhost:5001/transporters/dashboard)
- [ ] Dashboard loads
- [ ] Statistics display:
  - [ ] Total deliveries
  - [ ] Completed deliveries
  - [ ] In transit
  - [ ] Total earnings
- [ ] Account status alert shows (if pending)
- [ ] Quick action cards work
- [ ] Recent deliveries table displays

### Available Jobs (http://localhost:5001/transporters/available-jobs)
- [ ] Jobs page loads
- [ ] Only shows jobs matching coverage area
- [ ] Job details display:
  - [ ] Delivery type (Local/Regional)
  - [ ] Route (from → to)
  - [ ] Delivery fee
  - [ ] Distance (if available)
- [ ] Accept button works
- [ ] Empty state shows if no jobs

### My Deliveries (http://localhost:5001/transporters/my-deliveries)
- [ ] Deliveries list loads
- [ ] Status filter works
- [ ] Table shows all assigned deliveries
- [ ] Status badges display correctly
- [ ] "Manage" button goes to detail page

### Delivery Detail (http://localhost:5001/transporters/delivery/<id>)
- [ ] Detail page loads
- [ ] Pickup information displays
- [ ] Delivery information displays
- [ ] Order items list shows
- [ ] Status update form works
- [ ] Timeline shows all status changes

---

## 7. Static Pages

### Home Page (http://localhost:5001/)
- [ ] Page loads without errors
- [ ] Hero section displays
- [ ] Search box works
- [ ] Category cards display
- [ ] Featured products show
- [ ] Call-to-action buttons work:
  - [ ] Browse Products
  - [ ] Become a Seller
  - [ ] Become a Transporter

### About Page (http://localhost:5001/about)
- [ ] Page loads
- [ ] "For Buyers" section displays (6 steps)
- [ ] "For Sellers" section displays (6 steps)
- [ ] "For Transporters" section displays (6 steps)
- [ ] "Why Choose Us" section displays
- [ ] All CTA buttons work

### Terms & Conditions (http://localhost:5001/terms)
- [ ] Page loads
- [ ] Content displays properly

### Privacy Policy (http://localhost:5001/privacy)
- [ ] Page loads
- [ ] Content displays properly

---

## 8. Navigation & UI

### Header Navigation
- [ ] Logo/brand link goes to home
- [ ] Browse Products link works
- [ ] User menu displays when logged in
- [ ] Seller menu displays when logged in as seller
- [ ] Transporter menu displays when logged in as transporter
- [ ] Logout works from all user types

### Footer
- [ ] All footer links work
- [ ] Social media links present
- [ ] Category links work
- [ ] Company info links work

---

## 9. Error Handling

### 404 Pages
- [ ] Non-existent product shows 404
- [ ] Non-existent seller shows 404
- [ ] Non-existent routes show 404

### Form Validation
- [ ] Required field validation works
- [ ] Email format validation works
- [ ] Password length validation works
- [ ] Numeric field validation works
- [ ] File upload validation works

### Database Constraints
- [ ] Duplicate email rejected
- [ ] Duplicate SKU rejected
- [ ] Duplicate store name rejected
- [ ] Foreign key constraints enforced

---

## 10. Security Checks

### Authentication
- [ ] Unauthenticated users redirected from protected pages
- [ ] Sellers can only edit their own products
- [ ] Sellers can only view their own orders
- [ ] Transporters can only view their assigned deliveries
- [ ] Session timeout works

### File Uploads
- [ ] Only allowed file types accepted
- [ ] File size limits enforced
- [ ] Uploaded files stored securely
- [ ] No script execution in upload directory

---

## 11. Performance & Data

### Database
- [ ] All tables created
- [ ] Indexes present on frequently queried columns
- [ ] Foreign keys properly set up
- [ ] Default values work correctly

### Images
- [ ] Images upload correctly
- [ ] Images display correctly
- [ ] Placeholder images work
- [ ] Image deletion works
- [ ] Primary image setting works

---

## ✅ Pre-Launch Checklist

Before going live, ensure:

1. [ ] All automated tests pass (`python test_functionality.py`)
2. [ ] All manual tests above completed successfully
3. [ ] Database backup taken
4. [ ] No critical errors in console/logs
5. [ ] No broken links found
6. [ ] No missing images (except intentional placeholders)
7. [ ] All routes return expected status codes
8. [ ] Forms validate correctly
9. [ ] Error messages are user-friendly
10. [ ] Navigation works across all pages
11. [ ] Mobile responsiveness checked
12. [ ] Browser compatibility tested
13. [ ] Security review completed
14. [ ] Environment variables set correctly
15. [ ] Production settings configured

---

## 🐛 Known Issues (If Any)

*Document any known issues here before launch*

---

## 📊 Test Results

**Date:** _________________
**Tester:** _________________
**Overall Status:** [ ] READY FOR LAUNCH [ ] NEEDS FIXES

**Notes:**
