import os
import re
import json
import urllib.request
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

def get_latest_tag(repo_name, token):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/tags"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            tags = json.loads(response.read().decode("utf-8"))
            if tags:
                return tags[0]["name"]
    except Exception as e:
        print(f"Não foi possível obter a tag para {repo_name}: {e}")
    return "-"

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
    markdown = "| Plugin | Descrição | Última Tag | Data/Hora (BRT) |\n"
    markdown += "|--------|-----------|------------|-----------------|\n"
    
    for repo in filtered_repos:
        name = repo.get("name")
        url = repo.get("html_url")
        desc = repo.get("description") or "Sem descrição"
        
        tag = get_latest_tag(name, token)
        
        # Converter a data para o fuso horário de Brasília (BRT: UTC-3)
        updated_at_raw = repo.get("pushed_at") or repo.get("updated_at")
        try:
            dt_utc = datetime.strptime(updated_at_raw, "%Y-%m-%dT%H:%M:%SZ")
            dt_brt = dt_utc - timedelta(hours=3)
            date_str = dt_brt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            date_str = updated_at_raw
        
        markdown += f"| [{name}]({url}) | {desc} | {tag} | {date_str} |\n"

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
