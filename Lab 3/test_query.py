import os
from dotenv import load_dotenv
import requests

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

query = """
query {
  search(query: "stars:>100 sort:stars-desc", type: REPOSITORY, first: 1) {
    nodes {
      ... on Repository {
        nameWithOwner
        mergedPullRequests: pullRequests(states: MERGED) {
          totalCount
        }
      }
    }
  }
}
"""

headers = {"Authorization": f"Bearer {TOKEN}"}
res = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)
print(res.json())
