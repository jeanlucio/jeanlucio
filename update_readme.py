import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# Configurações
USERNAME = "jeanlucio"
EXCLUDE_REPOS = [
    "jeanlucio.github.io",
    "moodle-dev-tools",
    "awesome-moodle",
    "jeanlucio",
    "files",
    "moodle-format_trail"
]
MAX_REPOS = 5

def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt_utc = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        dt_brt = dt_utc - timedelta(hours=3)
        return dt_brt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return date_str

def get_latest_release(repo_name, token):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            release = json.loads(response.read().decode("utf-8"))
            return release.get("tag_name"), release.get("published_at")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"Erro {e.code} ao obter release para {repo_name}")
    except Exception as e:
        print(f"Erro ao obter release para {repo_name}: {e}")
    return None, None

def get_latest_commit(repo_name, token):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?per_page=1"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            commits = json.loads(response.read().decode("utf-8"))
            if commits:
                commit = commits[0]
                return commit.get("sha"), commit["commit"]["committer"]["date"]
    except Exception as e:
        print(f"Erro ao obter commit para {repo_name}: {e}")
    return None, None

def get_repos(token):
    url = f"https://api.github.com/users/{USERNAME}/repos?sort=pushed&per_page=100"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Erro ao buscar repositórios: {e}")
        return []

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Aviso: GITHUB_TOKEN não definido. Pode haver limite de requisições na API.")

    repos = get_repos(token)
    filtered_repos = []
    
    for repo in repos:
        # Filtra repos privados e os da lista de exceção
        if not repo.get("private") and repo.get("name") not in EXCLUDE_REPOS:
            filtered_repos.append(repo)
        
        if len(filtered_repos) >= MAX_REPOS:
            break

    # Criação da tabela Markdown
    markdown = "| Plugin | Description / Descrição | Latest Release / Última Release | Latest Commit / Último Commit |\n"
    markdown += "|--------|-------------------------|---------------------------------|-------------------------------|\n"
    
    for repo in filtered_repos:
        name = repo.get("name")
        url = repo.get("html_url")
        desc = repo.get("description") or "No description / Sem descrição"
        
        rel_tag, rel_date = get_latest_release(name, token)
        commit_sha, commit_date = get_latest_commit(name, token)
        
        if rel_tag and rel_date:
            rel_str = f"[{rel_tag}]({url}/releases/tag/{rel_tag})<br>{format_date(rel_date)}"
        else:
            rel_str = "-"
            
        if commit_sha and commit_date:
            short_sha = commit_sha[:7]
            commit_str = f"[{short_sha}]({url}/commit/{commit_sha})<br>{format_date(commit_date)}"
        else:
            commit_str = "-"
        
        markdown += f"| [{name}]({url}) | {desc} | {rel_str} | {commit_str} |\n"

    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()

        # Substituir o conteúdo entre os marcadores
        pattern = r"(<!-- START_LATEST_REPOS -->\n).*?(\n<!-- END_LATEST_REPOS -->)"
        new_readme = re.sub(pattern, rf"\1{markdown}\2", readme, flags=re.DOTALL)
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_readme)
            
        print("README.md atualizado com sucesso!")
    except Exception as e:
        print(f"Erro ao atualizar README.md: {e}")

if __name__ == "__main__":
    main()

