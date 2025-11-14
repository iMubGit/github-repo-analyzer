import requests
import json
import csv
from datetime import datetime
from time import sleep

import requests
import json
import csv
from datetime import datetime
from time import sleep

class GitHubAnalyzer:
    def __init__(self, username):
        self.username = username
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        # TODO: Add environment variables for auth tokens
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RepoAnalyzer/1.0"
        })
   
    def get_repositories(self, min_stars=0):
        """Fetch repos with optional star filtering"""
        repos = []
        page = 1
       
        print(f"🔍 Fetching repos for {self.username} (min {min_stars} stars)...")
       
        while True:
            url = f"{self.base_url}/users/{self.username}/repos"
            params = {
                "page": page,
                "per_page": 50,  # Increased from 30 for faster loading
                "sort": "updated",
                "direction": "desc"
            }
           
            try:
                response = self.session.get(url, params=params, timeout=15)
                print(f"   Page {page} status: {response.status_code}")  # Debug line
               
                if response.status_code == 404:
                    print(f"❌ User '{self.username}' not found")
                    return []
               
                if response.status_code == 403:
                    print("⏳ Rate limit hit, waiting 60s...")
                    sleep(60)
                    continue
               
                if response.status_code != 200:
                    print(f"⚠️  Unexpected status: {response.status_code}")
                    # FIXME: Add better retry logic here
                    break
               
                data = response.json()
               
                if not data:
                    print("   No more repos found")
                    break
               
                # Apply star filter immediately to save API calls
                filtered_repos = [repo for repo in data if repo["stargazers_count"] >= min_stars]
                repos.extend(filtered_repos)
               
                print(f"   Page {page}: {len(data)} repos, {len(filtered_repos)} meet {min_stars}+ stars")
               
                # Stop early if we have enough data for demo
                if len(repos) >= 20 and min_stars > 0:  # Practical limit
                    print("   Reached practical limit, stopping pagination")
                    break
                   
                page += 1
                sleep(0.3)  # Be nice to GitHub
               
            except requests.exceptions.Timeout:
                print("❌ Request timeout - skipping page")
                break
            except requests.exceptions.RequestException as e:
                print(f"❌ Network error: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                break
       
        print(f"✅ Found {len(repos)} repos with {min_stars}+ stars")
        return repos
   
    def get_repo_languages(self, owner, repo_name):
        """Get language breakdown - useful for tech stack analysis"""
        url = f"{self.base_url}/repos/{owner}/{repo_name}/languages"
       
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"    Language fetch failed for {repo_name}: {e}")  # Debug
        return {}
   
    def analyze_repository(self, repo):
        """Extract key metrics I actually care about"""
        # Debug: print(f"Analyzing {repo['name']}")  # Uncomment for troubleshooting
       
        languages = self.get_repo_languages(self.username, repo["name"])
        primary_language = max(languages.items(), key=lambda x: x[1])[0] if languages else "Unknown"
       
        return {
            "name": repo["name"],
            "description": (repo["description"] or "No description")[:100],  # Truncate long desc
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "open_issues": repo["open_issues_count"],
            "language": primary_language,
            "created": repo["created_at"][:10],
            "updated": repo["updated_at"][:10],
            "size_mb": round(repo["size"] / 1024, 1),  # More readable than KB
            "private": repo["private"],
            "url": repo["html_url"],
            "watchers": repo["watchers_count"],
            "topics": ", ".join(repo.get("topics", [])[:3])  # Added this for better analysis
        }
   
    def generate_report(self, repos):
        """Generate insights I actually use"""
        if not repos:
            return {"error": "No repositories to analyze"}
       
        total_stars = sum(r["stars"] for r in repos)
        total_forks = sum(r["forks"] for r in repos)
       
        # Language analysis - useful for skills assessment
        languages = {}
        for repo in repos:
            lang = repo["language"]
            if lang != "Unknown":
                languages[lang] = languages.get(lang, 0) + 1
       
        # Find most popular repos (my custom metric)
        popular_repos = sorted(repos, key=lambda x: x["stars"], reverse=True)[:3]
       
        return {
            "total_repos": len(repos),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "avg_stars_per_repo": round(total_stars / len(repos), 1),
            "languages": dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)[:8]),
            "most_starred": popular_repos[0]["name"] if popular_repos else "None",
            "most_recent": max(repos, key=lambda x: x["updated"])["name"],
            "popular_repos": [r["name"] for r in popular_repos]
        }
   
    def export_to_csv(self, repos, filename=None):
        """Export to CSV for spreadsheet analysis"""
        if not repos:
            print("❌ No data to export")
            return False
           
        if not filename:
            filename = f"github_repos_{self.username}_{datetime.now().strftime('%Y%m%d')}.csv"
       
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=repos[0].keys())
                writer.writeheader()
                writer.writerows(repos)
           
            print(f"📊 Exported {len(repos)} repositories to {filename}")
            return True
        except Exception as e:
            print(f"❌ CSV export failed: {e}")
            return False
   
    def export_to_json(self, data, filename=None):
        """Export full dataset for later analysis"""
        if not filename:
            filename = f"github_data_{self.username}_{datetime.now().strftime('%H%M')}.json"
       
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
           
            print(f"💾 Full data exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ JSON export failed: {e}")
            return False

def main():
    print("=" * 60)
    print("GitHub Repository Analyzer")
    print("Built for project tracking and skills assessment")
    print("=" * 60)
   
    # TODO: Add command-line argument parsing
    username = input("Enter GitHub username [torvalds]: ").strip() or "torvalds"
    min_stars = input("Minimum stars filter [0]: ").strip()
    min_stars = int(min_stars) if min_stars.isdigit() else 0
   
    print()
   
    analyzer = GitHubAnalyzer(username)
   
    # Fetch with filtering
    raw_repos = analyzer.get_repositories(min_stars=min_stars)
   
    if not raw_repos:
        print("\n❌ No repositories found matching criteria.")
        print("   Try different username or lower star filter")
        return
   
    # Analyze each repository
    print(f"\n📈 Analyzing {len(raw_repos)} repositories...")
    analyzed_repos = []
   
    for i, repo in enumerate(raw_repos):
        analyzed = analyzer.analyze_repository(repo)
        analyzed_repos.append(analyzed)
       
        # Show progress for first few
        if i < 5:  # Only show details for first 5 to avoid spam
            print(f"   {i+1}. {analyzed['name']} - ⭐{analyzed['stars']} - {analyzed['language']}")
       
        sleep(0.2)  # Conservative rate limiting
   
    # Generate and display report
    print("\n" + "=" * 50)
    print("ANALYSIS REPORT")
    print("=" * 50)
   
    report = analyzer.generate_report(analyzed_repos)
   
    print(f"\n📊 Repository Analysis for @{username}:")
    print(f"   Total repos: {report['total_repos']}")
    print(f"   Total stars: {report['total_stars']} (avg: {report['avg_stars_per_repo']}/repo)")
    print(f"   Total forks: {report['total_forks']}")
   
    if report['popular_repos']:
        print(f"   Most popular: {', '.join(report['popular_repos'][:2])}")
   
    print(f"\n💻 Top Languages:")
    for lang, count in list(report['languages'].items())[:5]:
        print(f"   {lang}: {count} repos")
   
    # Export data
    print("\n" + "=" * 50)
    csv_success = analyzer.export_to_csv(analyzed_repos)
    json_success = analyzer.export_to_json({
        "analyzed_at": datetime.now().isoformat(),
        "username": username,
        "filters": {"min_stars": min_stars},
        "summary": report,
        "repositories": analyzed_repos
    })
   
    if csv_success and json_success:
        print("\n✅ Analysis complete! Check the generated files.")
    else:
        print("\n⚠️  Analysis completed with some export issues")

# Quick test function I used during development
def test_small_dataset():
    """Test with a known small account"""
    print("\n🧪 Running quick test...")
    analyzer = GitHubAnalyzer("octocat")  # GitHub's test account
    repos = analyzer.get_repositories(min_stars=0)
    print(f"Test found {len(repos)} repos")
    return len(repos) > 0

if __name__ == "__main__":
    # Uncomment for quick testing during development:
    # if test_small_dataset():
    #     print("Quick test passed!")
   
    main()
   
    print("\n" + "=" * 60)
    print("Next improvements:")
    print("  - Add GitHub auth for higher rate limits")
    print("  - Add repository topic analysis")
    print("  - Add commit frequency tracking")
    print("  - Add command-line interface")