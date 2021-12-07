from github import Github

g = Github()
repositories = g.search_repositories(query='android f-droid stars:>1000')
for repo in repositories:
    print(repo.clone_url)