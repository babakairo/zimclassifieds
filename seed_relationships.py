"""
Seed script to populate dummy 'relationship' users and listings with placeholder images.
Run: python seed_relationships.py
"""
import sqlite3
import uuid
import os
import base64
from datetime import datetime
from werkzeug.security import generate_password_hash

DB = 'zimclassifieds.db'
UPLOAD_DIR = os.path.join('static','uploads')

# Small base64 PNG placeholders (1x1 px transparent). We'll generate a few with slight variations by tinting.
# Using the same minimal PNG for simplicity.
PNG_BASE64 = (
    # 1x1 PNG (valid base64)
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAgMBgKX7nQAAAABJRU5ErkJggg=='
)

users = [
    { 'full_name': 'Anna M', 'email': 'anna.relationship@example.com', 'phone': '+263771111111', 'location': 'Harare', 'bio': 'Looking for new friends and meaningful connections in Harare.'},
    { 'full_name': 'Tendai K', 'email': 'tendai.relationship@example.com', 'phone': '+263772222222', 'location': 'Bulawayo', 'bio': 'Fun loving, coffee enthusiast. Let\'s chat!'},
    { 'full_name': 'Chipo Z', 'email': 'chipo.relationship@example.com', 'phone': '+263773333333', 'location': 'Mutare', 'bio': 'Here to meet interesting people in Mutare.'},
    { 'full_name': 'Peter N', 'email': 'peter.relationship@example.com', 'phone': '+263774444444', 'location': 'Gweru', 'bio': 'Single and ready to mingle. Into hiking and music.'},
    { 'full_name': 'Sandra L', 'email': 'sandra.relationship@example.com', 'phone': '+263775555555', 'location': 'Kwekwe', 'bio': 'Looking for friends and possibly more.'}
]

listings_templates = [
    'Looking for friends in {city}',
    'Seeking relationship in {city}',
    'Open for dating and friends - {city}',
    'Single in {city} - coffee and walks',
    'Friendly person seeking connection in {city}'
]

# Ensure upload dir exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Write a few placeholder files and return their paths (uploads/filename.png)
def write_placeholder_image(name_suffix):
    filename = f"seed_{name_suffix}_{uuid.uuid4().hex[:8]}.png"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, 'wb') as f:
        f.write(base64.b64decode(PNG_BASE64))
    return f"uploads/{filename}"


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    created_users = []
    created_listings = []

    for i, u in enumerate(users):
        email = u['email']
        # Check if user exists
        cur.execute('SELECT * FROM users WHERE email = ?', (email,))
        if cur.fetchone():
            print(f"User {email} already exists, skipping creation.")
            # fetch user_id to use for listings
            cur.execute('SELECT user_id FROM users WHERE email = ?', (email,))
            uid = cur.fetchone()[0]
            created_users.append(uid)
            continue

        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash('password123')
        profile_image = write_placeholder_image(f"profile_{i}")

        cur.execute('''
            INSERT INTO users (user_id, email, password_hash, full_name, phone, location, bio, profile_image, account_type, verification_status, email_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, email, password_hash, u['full_name'], u['phone'], u['location'], u['bio'], profile_image, 'personal', 'verified', 1))

        created_users.append(user_id)
        print(f"Created user {email} -> {user_id}")

    conn.commit()

    # Create listings in 'relationships' category for each user
    for idx, user_id in enumerate(created_users):
        # create 1-2 listings per user
        for j in range(1, 3):
            title = listings_templates[(idx + j) % len(listings_templates)].format(city=users[idx]['location'])
            listing_id = str(uuid.uuid4())
            category = 'relationships'
            subcategory = 'Making Friends' if j == 1 else 'Singles Events'
            description = users[idx]['bio'] + ' Message me if interested.'
            price = None
            currency = 'ZWL'
            location_city = users[idx]['location']
            location_suburb = location_city + ' CBD'

            img1 = write_placeholder_image(f"listing_{idx}_{j}_1")
            img2 = write_placeholder_image(f"listing_{idx}_{j}_2")
            images_csv = ','.join([img1, img2])

            now = datetime.utcnow().isoformat(sep=' ', timespec='seconds')

            # avoid duplicates by title+user
            cur.execute('SELECT * FROM listings WHERE user_id = ? AND title = ?', (user_id, title))
            if cur.fetchone():
                print(f"Listing '{title}' for user {user_id} already exists, skipping.")
                continue

            cur.execute('''
                INSERT INTO listings (listing_id, user_id, category, subcategory, title, description, price, currency, location_city, location_suburb, images, status, views, flags, created_at, updated_at, bumped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (listing_id, user_id, category, subcategory, title, description, price, currency, location_city, location_suburb, images_csv, 'active', 0, 0, now, now, now))

            created_listings.append(listing_id)
            print(f"Created listing {title} ({listing_id}) for user {user_id}")

    conn.commit()
    conn.close()

    print('\nDone. Created users:', len(created_users))
    print('Created listings:', len(created_listings))
    print('Images saved in', UPLOAD_DIR)

if __name__ == '__main__':
    main()
