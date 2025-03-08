from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Dummy API keys (Replace with actual keys)
LINKEDIN_ACCESS_TOKEN = "your_linkedin_access_token"
FACEBOOK_ACCESS_TOKEN = "your_facebook_access_token"


def search_linkedin(params):
    """Search for people on LinkedIn."""
    headers = {"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}"}
    url = "https://api.linkedin.com/v2/people-search"
    response = requests.get(url, headers=headers, params=params)
    return response.json() if response.status_code == 200 else {"error": "LinkedIn search failed"}


def search_facebook(params):
    """Search for people on Facebook."""
    url = "https://graph.facebook.com/v12.0/search"
    params["access_token"] = FACEBOOK_ACCESS_TOKEN
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else {"error": "Facebook search failed"}


@app.route("/search", methods=["GET"])
def search_people():
    """Search for people using multiple criteria."""
    name = request.args.get("name")
    school = request.args.get("school")
    years_attended = request.args.get("years_attended")
    workplace = request.args.get("workplace")
    languages = request.args.get("languages")

    params = {}
    if name:
        params["name"] = name
    if school:
        params["school"] = school
    if years_attended:
        params["years_attended"] = years_attended
    if workplace:
        params["workplace"] = workplace
    if languages:
        params["languages"] = languages
    
    linkedin_results = search_linkedin(params)
    facebook_results = search_facebook(params)
    
    return jsonify({
        "linkedin": linkedin_results,
        "facebook": facebook_results
    })


if __name__ == "__main__":
    app.run(debug=True)