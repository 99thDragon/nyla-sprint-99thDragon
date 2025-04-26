import argparse, os, sys, time, requests, json
from datetime import datetime

MODEL = "google/palm-2-chat-bison"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

def build_prompt(args):
    return f"Write five fundraising emails and four social captions for the {args.event} on {args.date} in a {args.tone} tone."

def chat_completion(prompt, model=MODEL):
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        sys.exit("Error: OPENROUTER_API_KEY environment variable is not set")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.7
    }
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/raybo/nyla-sprint-99thDragon",
        "X-Title": "Fundraising Email Generator"
    }
    
    try:
        print("\nSending request to OpenRouter API...", file=sys.stderr)
        print(f"Using model: {model}", file=sys.stderr)
        print(f"Request payload: {json.dumps(payload, indent=2)}", file=sys.stderr)
        
        t0 = time.time()
        r = requests.post(ENDPOINT, headers=headers, json=payload, timeout=60)
        dt = time.time() - t0
        
        print(f"Status code: {r.status_code}", file=sys.stderr)
        print(f"Response headers: {dict(r.headers)}", file=sys.stderr)
        
        try:
            response_json = r.json()
        except json.JSONDecodeError:
            print(f"Failed to decode JSON. Raw response: {r.text}", file=sys.stderr)
            sys.exit(1)
        
        if "error" in response_json:
            print(f"API Error: {response_json['error']['message']}", file=sys.stderr)
            sys.exit(1)
            
        if r.status_code != 200:
            print(f"Error response: {r.text}", file=sys.stderr)
            sys.exit(1)
            
        print(f"Request completed in {dt:.2f}s", file=sys.stderr)
        print(f"Full response: {json.dumps(response_json, indent=2)}", file=sys.stderr)
        
        try:
            return response_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            print(f"Failed to extract content from response: {e}", file=sys.stderr)
            print(f"Response structure: {response_json}", file=sys.stderr)
            sys.exit(1)
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to connect to OpenRouter API: {e}", file=sys.stderr)
        print(f"Exception details: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if 'r' in locals():
            print(f"Response text: {r.text}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Generate fundraising emails and social captions using OpenRouter AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --event "Annual Gala" --date "2024-03-15"
  python main.py --model "google/palm-2-chat-bison" --tone "professional"
  python main.py --output "marketing/campaign.md" --show-response
        """
    )
    
    # Required arguments
    parser.add_argument("--event", required=True,
                      help="Name of the event (e.g., 'Annual Charity Ball')")
    
    # Optional arguments
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                      help="Date of the event (default: today)")
    parser.add_argument("--tone", default="upbeat",
                      choices=["upbeat", "professional", "casual", "formal", "friendly"],
                      help="Tone of the writing")
    parser.add_argument("--model", default=MODEL,
                      help="OpenRouter model to use")
    parser.add_argument("--output", default="out/campaign.md",
                      help="Output file path")
    parser.add_argument("--dry-run", action="store_true",
                      help="Print the prompt and exit without making API call")
    parser.add_argument("--show-response", action="store_true",
                      help="Print the raw API response")
    parser.add_argument("--version", action="version",
                      version="%(prog)s 1.0.0")
    
    args = parser.parse_args()
    
    # Build and validate prompt
    prompt = build_prompt(args)
    if args.dry_run:
        print("\nGenerated Prompt:")
        print("-" * 50)
        print(prompt)
        print("-" * 50)
        return
    
    # Make API call
    print(f"\nGenerating content for {args.event}...", file=sys.stderr)
    response = chat_completion(prompt, args.model)
    
    if not response or not response.strip():
        print("Error: Received empty response from API", file=sys.stderr)
        sys.exit(1)
    
    # Save output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(response)
    
    print(f"\nContent saved to: {args.output}")
    
    if args.show_response:
        print("\nGenerated Content:")
        print("-" * 50)
        print(response)
        print("-" * 50)

if __name__ == "__main__":
    main()
