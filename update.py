import requests
import os
import datetime
from dateutil import tz

token = ''
current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
top_repo_num = 10
recent_repo_num = 10

from_zone = tz.tzutc()
to_zone = tz.tzlocal()

# ----------------------------------------------------------------------------
# Profile content — edit these to customize your README.
# ----------------------------------------------------------------------------

TAGLINE = "Maker - Builder - Product Tinkerer"

ABOUT_BULLETS = [
    "Building small, focused tools — from browser extensions to LLM-powered bots.",
    "Currently exploring LLM tooling, vector databases, and AI-assisted developer workflows.",
    "Open to thoughtful collaborations at the intersection of AI, product, and UX.",
]

NO_DESCRIPTION = "—"


def fetcher(username: str):
    result = {
        'name': '',
        'public_repos': 0,
        'top_repos': [],
        'recent_repos': []
    }
    user_info_url = "https://api.github.com/users/{}".format(username)
    all_repos_url = "https://api.github.com/users/{}/repos?per_page=100".format(username)
    header = {} if token == "" else {"Authorization": "bearer {}".format(token)}
    res = requests.get(user_info_url, header)
    user = res.json()
    result['name'] = user['name']
    res = requests.get(all_repos_url, header)
    repos = res.json()
    processed_repos = []
    for repo in repos:
        if repo['fork']:
            continue
        processed_repo = {
            # Note: GitHub's `watchers_count` is an alias for `stargazers_count`,
            # so we intentionally only sum stars and forks here.
            'score': repo['stargazers_count'] + repo['forks_count'],
            'star': repo['stargazers_count'],
            'link': repo['html_url'],
            'created_at': repo['created_at'],
            'updated_at': repo['updated_at'],
            'pushed_at': repo['pushed_at'],
            'name': repo['name'],
            'description': repo['description'] or NO_DESCRIPTION
        }
        date = datetime.datetime.strptime(processed_repo['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
        date = date.replace(tzinfo=from_zone)
        date = date.astimezone(to_zone)
        processed_repo['pushed_at'] = date.strftime('%Y-%m-%d %H:%M:%S')
        processed_repos.append(processed_repo)
    top_repos = sorted(processed_repos, key=lambda x: x['score'], reverse=True)
    top_repos = top_repos[:top_repo_num]
    result['top_repos'] = top_repos
    recent_repos = sorted(processed_repos, key=lambda x: x['pushed_at'], reverse=True)
    recent_repos = recent_repos[:recent_repo_num]
    result['recent_repos'] = recent_repos
    return result


header_tpl = """<h1 align="center">{github_name}</h1>
<p align="center"><em>{tagline}</em></p>

<p align="center">
  <a href="https://github.com/{github_username}"><img src="https://img.shields.io/github/followers/{github_username}?label=Follow&style=flat-square&logo=github" alt="Follow on GitHub"/></a>
  <img src="https://img.shields.io/badge/Open%20to-Collaboration-success?style=flat-square" alt="Open to collaboration"/>
</p>

---

### About

{about_block}

### GitHub Stats

<p>
<img src="https://github-readme-stats.vercel.app/api?username={github_username}&show_icons=true&hide_border=true" alt="{github_name}'s GitHub Stats"/>
<img src="https://github-readme-stats.vercel.app/api/top-langs/?username={github_username}&layout=compact&hide_border=true&langs_count=10" alt="{github_name}'s Top Languages"/>
</p>
"""

zhihu_tpl = '\n<p><a href="https://www.zhihu.com/people/{zhihu_username}"><img src="https://stats.justsong.cn/api/zhihu?username={zhihu_username}" alt="{github_name}\'s Zhihu Stats"/></a></p>\n'

recent_repos_tpl = """
### Recent Activity

| Repository | Description | Last Updated |
|:--|:--|:--|
"""

top_repos_tpl = """
### Featured Projects

| Repository | Description | Stars |
|:--|:--|:--|
"""

footer_tpl = """
---

<sub>Profile auto-refreshed weekly via GitHub Actions. Last update: {}</sub>
""".format(current_time)


def render(github_username, github_data, zhihu_username='') -> str:
    github_name = github_data['name'] or github_username
    about_block = "\n".join("- {}".format(line) for line in ABOUT_BULLETS)

    markdown = header_tpl.format(
        github_username=github_username,
        github_name=github_name,
        tagline=TAGLINE,
        about_block=about_block,
    )

    if zhihu_username:
        markdown += zhihu_tpl.format(
            github_name=github_name,
            zhihu_username=zhihu_username,
        )

    recent_section = recent_repos_tpl
    for repo in github_data['recent_repos']:
        recent_section += "| [{name}]({link}) | {description} | `{pushed_at}` |\n".format(**repo)
    markdown += recent_section

    top_section = top_repos_tpl
    for repo in github_data['top_repos']:
        top_section += "| [{name}]({link}) | {description} | `{star}` |\n".format(**repo)
    markdown += top_section

    markdown += footer_tpl
    return markdown


def writer(markdown) -> bool:
    ok = True
    try:
        with open('./README.md', 'w') as f:
            f.write(markdown)
    except IOError:
        ok = False
        print('unable to write to file')
    return ok


def pusher():
    commit_message = ":pencil2: update on {}".format(current_time)
    os.system('git add ./README.md')
    if os.getenv('DEBUG'):
        return
    os.system('git commit -m "{}"'.format(commit_message))
    os.system('git push')


def main():
    global top_repo_num
    global recent_repo_num
    top_repo_num = 10
    recent_repo_num = 10
    github_username = os.getenv('GITHUB_USERNAME')
    if not github_username:
        cwd = os.getcwd()
        github_username = os.path.split(cwd)[-1]
    zhihu_username = os.getenv('ZHIHU_USERNAME')
    github_data = fetcher(github_username)
    markdown = render(github_username, github_data, zhihu_username)
    if writer(markdown):
        pass
        # pusher()


if __name__ == '__main__':
    main()
