function searchFriends() {
    let query = document.getElementById("search-bar").value;
    document.getElementById("search-results").innerHTML = `<p>Searching for: ${query}</p>`;
}