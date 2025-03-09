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
    location = request.args.get("location")

    params = {}
    if name:
        params["name"] = name
    if school:
        params["school"] = school
    if years_attended:
        params["years_attended"] = years_attended
    if workplace:
        params["workplace"] = workplace
    if location:
        params["location"] = location

    #     """Search for people using multiple criteria."""
    # query_params = {}
    # if request.args.get("name"):
    #     query_params["full_name"] = request.args.get("name") 
    # if request.args.get("school"):
    #     query_params["education.school.name"] = request.args.get("school")
    # if request.args.get("years_attended"):
    #     query_params["education.years_attended"] = request.args.get("years_attended")
    # if request.args.get("workplace"):
    #     query_params["experience.company.name"] = request.args.get("workplace")
    # if request.args.get("languages"):
    #     query_params["languages"] = request.args.get("languages")
    # if request.args.get("industry"):
    #     query_params["experience.company.industry"] = request.args.get("industry")
    # if request.args.get("region"):
    #     query_params["location_region"] = request.args.get("region")
    # if request.args.get("role"):
    #     query_params["experience.title.role"] = request.args.get("role")
    # if request.args.get("sex"):
    #     query_params["sex"] = request.args.get("sex")
    
    linkedin_results = search_linkedin(params)
    facebook_results = search_facebook(params)
    
    return jsonify({
        "linkedin": linkedin_results,
        "facebook": facebook_results
    })


if __name__ == "__main__":
    app.run(debug=True)