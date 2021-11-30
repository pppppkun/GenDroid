from github import Github

g = Github()
repositories = g.search_repositories(query='android stars:>1000')
for repo in repositories:
    print(repo)