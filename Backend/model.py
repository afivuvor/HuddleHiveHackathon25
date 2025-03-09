from flask import Flask, request, jsonify
import requests
import os
from deepface import DeepFace
import cv2
import numpy as np
from PIL import Image

app = Flask(__name__)

# API Keys
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAOtIzwEAAAAAmCq1Y%2BtO8lhJIA8yNCZxnaa6I8s%3DLrwnjOM5RhtdP2I9BIwAeGv9PaMY6D0chStdHBxoWhpn48vJVQ"  # Replace with a valid token
GITHUB_SEARCH_URL = "https://api.github.com/search/users"

def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        print(f"Downloaded Image: {image_url}")
        with open("debug_image.jpg", "wb") as f:
            f.write(response.content)  # Save for debugging
        img_arr = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            print("Image successfully converted to RGB")
        return img
    print(f"Failed to download image from {image_url}")
    return None

def match_faces(uploaded_image, profile_image_url):
    profile_img = download_image(profile_image_url)
    if profile_img is None:
        print(f"Failed to download image: {profile_image_url}")
        return False
    try:
        print(f"Comparing uploaded image: {uploaded_image} with {profile_image_url}")
        result = DeepFace.verify(uploaded_image, "debug_image.jpg", model_name="Facenet512", enforce_detection=False)
        print(f"Face Match Result: {result}")
        return result.get("verified", False)
    except Exception as e:
        print(f"Error comparing faces: {e}")
        return False

def search_github_profiles(name):
    params = {"q": name, "per_page": 5}
    response = requests.get(GITHUB_SEARCH_URL, params=params)
    print("GitHub API Response:", response.json())
    if response.status_code == 200:
        return response.json().get("items", [])
    return []

def search_twitter_profiles(name):
    url = f"https://api.twitter.com/2/users/by?usernames={name}&user.fields=profile_image_url"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    print(f"Twitter API Headers: {headers}")
    response = requests.get(url, headers=headers)
    print("Twitter API Response Code:", response.status_code)
    print("Twitter API Response:", response.json())
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

@app.route("/search_by_image", methods=["POST"])
def search_by_image():
    if "file" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    image_file = request.files["file"]
    image_path = "temp.jpg"
    image_file.save(image_path)
    img = Image.open(image_path).convert("RGB")
    img.save(image_path)
    
    possible_matches = []
    
    try:
        face_analysis = DeepFace.analyze(image_path, actions=["age", "gender"], enforce_detection=False)
        if not face_analysis:
            return jsonify({"error": "Could not detect face"}), 400
        
        estimated_age = face_analysis[0].get("age", "Unknown")
        gender = face_analysis[0].get("dominant_gender", "Unknown")
        print(f"Detected Age: {estimated_age}, Gender: {gender}")
    except Exception as e:
        print(f"Face detection error: {e}")
        return jsonify({"error": "Face analysis failed"}), 500

    github_profiles = search_github_profiles(request.args.get("name", ""))
    print("GitHub Users:", github_profiles)
    for user in github_profiles:
        username = user["login"]
        avatar_url = user["avatar_url"]
        if match_faces(image_path, avatar_url):
            possible_matches.append({"platform": "GitHub", "username": username, "profile_image": avatar_url})

    twitter_profiles = search_twitter_profiles(request.args.get("name", ""))
    print("Twitter Users:", twitter_profiles)
    for user in twitter_profiles:
        username = user["username"]
        profile_image = user["profile_image_url"]
        if match_faces(image_path, profile_image):
            possible_matches.append({"platform": "Twitter", "username": username, "profile_image": profile_image})

    if possible_matches:
        return jsonify({"matches": possible_matches})
    return jsonify({"message": "No matches found"})


GITHUB_API_URL = "https://api.github.com/search/users"
def search_github_users(query):
    """Search for users on GitHub using multiple criteria."""
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(GITHUB_API_URL, headers=headers, params={"q": query})
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "GitHub search failed", "status": response.status_code}

@app.route("/search", methods=["GET"])
def search_people():
    """Search GitHub users by name, location, company, followers, or a combination."""
    search_query = []
    
    if request.args.get("name"):
        search_query.append(f"{request.args.get('name')} in:name")
    if request.args.get("location"):
        search_query.append(f"location:{request.args.get('location')}")
    if request.args.get("company"):
        search_query.append(f"company:{request.args.get('company')}")
    if request.args.get("followers"):
        search_query.append(f"followers:>{request.args.get('followers')}")
    
    if not search_query:
        return jsonify({"error": "At least one search parameter is required"}), 400

    final_query = " ".join(search_query)
    github_results = search_github_users(final_query)

    return jsonify(github_results)

if __name__ == "__main__":
    app.run(debug=True)
