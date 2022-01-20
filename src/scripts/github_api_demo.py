from github import Github
from getpass import getpass

passwd = getpass()
g = Github(login_or_token='pppppkun', password=passwd)
repositories = g.search_repositories(query='f-droid in:README stars:>100')
repos = set()
for repo in repositories:
    repos.add(repo)
print(repos)
