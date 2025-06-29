#!/usr/bin/env python3
"""
Fix metadata for article 2962 - direct WordPress API update
"""

import requests
import json

def fix_article_metadata():
    """Fix metadata for article 2962 directly via WordPress API"""
    
    post_id = 2962
    
    # WordPress API credentials
    wp_url = "https://mamatestuje.com/wp-json/wp/v2"
    username = "mama-testuje"
    password = "mPb9 R5bP jhVU 1FHv nLSN tF3u"
    auth = (username, password)
    
    print(f"🔧 Fixing metadata for post {post_id}...")
    
    # Get category ID for "Planowanie ciąży"
    categories_url = f"{wp_url}/categories?search=Planowanie"
    cat_response = requests.get(categories_url, auth=auth)
    
    if cat_response.status_code == 200:
        categories = cat_response.json()
        category_id = None
        for cat in categories:
            if 'planowanie' in cat['name'].lower():
                category_id = cat['id']
                break
        
        print(f"🏷️ Found category ID: {category_id}")
    else:
        category_id = 3  # fallback to known ID
        print(f"🏷️ Using fallback category ID: {category_id}")
    
    # Create tags
    tags_url = f"{wp_url}/tags"
    tag_names = ["planowanie ciąży", "płodność", "zdrowie", "rodzina", "styl życia"]
    tag_ids = []
    
    for tag_name in tag_names:
        # Try to create tag
        tag_data = {
            "name": tag_name,
            "slug": tag_name.replace(" ", "-").lower()
        }
        
        tag_response = requests.post(tags_url, auth=auth, json=tag_data)
        
        if tag_response.status_code in [200, 201]:
            tag = tag_response.json()
            tag_ids.append(tag['id'])
            print(f"✅ Created/found tag: {tag_name} (ID: {tag['id']})")
        else:
            print(f"⚠️ Failed to create tag: {tag_name}")
    
    # Update post with category and tags
    post_url = f"{wp_url}/posts/{post_id}"
    
    update_data = {
        "categories": [category_id],
        "tags": tag_ids
    }
    
    print(f"📤 Updating post with categories: {[category_id]} and tags: {tag_ids}")
    
    response = requests.post(post_url, auth=auth, json=update_data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Post metadata updated successfully!")
        print(f"📍 Post ID: {result.get('id')}")
        print(f"🏷️ Categories: {result.get('categories', [])}")
        print(f"🔖 Tags: {result.get('tags', [])}")
        print(f"🔗 URL: https://mamatestuje.com/?p={post_id}")
        
        # Verify the update
        verify_response = requests.get(f"{post_url}?_fields=id,categories,tags,title")
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            print("\n📊 Verification:")
            print(f"Title: {verify_data.get('title', {}).get('rendered', 'N/A')}")
            print(f"Categories: {verify_data.get('categories', [])}")
            print(f"Tags: {verify_data.get('tags', [])}")
            
        return True
    else:
        print(f"❌ Failed to update post: {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    success = fix_article_metadata()
    if success:
        print("\n🎉 Article metadata successfully updated!")
    else:
        print("\n❌ Failed to update article metadata")