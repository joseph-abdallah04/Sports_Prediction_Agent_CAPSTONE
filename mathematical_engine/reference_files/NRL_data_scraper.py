import json
import os
import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Output")

def extract_nrl_match_data(url):
    """Fetches an NRL match center page, parses the embedded data layer,

    and returns the structured data dictionary.
    """
    # Desktop headers to avoid basic bot blocking
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print(f"\n[1/3] Connecting to NRL Servers...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Network request failed: {e}"}

    print(f"[2/3] Analyzing page document tree...")
    soup = BeautifulSoup(response.text, "html.parser")

    # Locate the state-hydration container
    match_centre_div = soup.find("div", id="vue-match-centre")

    if not match_centre_div or not match_centre_div.has_attr("q-data"):
        return {
            "error": "Target data container not found. Verify this is an accurate NRL Match Centre page link."
        }

    print(f"[3/3] Parsing embedded JSON payload...")
    try:
        raw_json_string = match_centre_div["q-data"]
        match_data = json.loads(raw_json_string)
        return match_data
    except json.JSONDecodeError:
        return {"error": "Failed to cleanly decode the embedded data attribute string."}


if __name__ == "__main__":
    print("=" * 60)
    print("        DYNAMIC NRL MATCH DATA INGESTION ENGINE        ")
    print("=" * 60)

    # Prompt user for input dynamically
    target_url = input("\nPaste NRL Match Centre Link here:\n> ").strip()

    # Fallback to defaults if user accidentally hits enter without pasting
    if not target_url:
        print(
            "\n[!] No link provided. Defaulting to fallback test match (Sharks v Bulldogs)..."
        )
        target_url = "https://www.nrl.com/draw/nrl-premiership/2026/round-11/sharks-v-bulldogs/"

    # Execute pipeline
    payload = extract_nrl_match_data(target_url)

    if "error" in payload:
        print(f"\n[!] PIPELINE FAILURE: {payload['error']}")
    else:
        # Extract metadata blocks from your newly won data structure
        match_details = payload.get("match", {})
        home_team = match_details.get("homeTeam", {}).get("name", "Unknown")
        away_team = match_details.get("awayTeam", {}).get("name", "Unknown")
        venue = match_details.get("venue", "Unknown Ground")
        match_id = match_details.get("matchId", "unknown_id")

        print("\n" + "=" * 50)
        print(f" EXTRACTION SUCCESS: {home_team} vs {away_team}")
        print(f" Venue: {venue} | Match ID: {match_id}")
        print("=" * 50)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_filename = os.path.join(OUTPUT_DIR, f"nrl_match_{match_id}.json")

        with open(output_filename, "w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=4)

        print(
            f"\n[+] Success! Full data block written to: {os.path.abspath(output_filename)}"
        )