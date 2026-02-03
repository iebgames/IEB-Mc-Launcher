import requests
import json

class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"

    @staticmethod
    def search_mods(query, limit=20, index="relevance", project_type="mod", versions=None, loaders=None):
        # project_type: mod, resourcepack, shader, modpack
        url = f"{ModrinthAPI.BASE_URL}/search"
        
        facets = []
        facets.append(f"project_type:{project_type}")
        
        if versions and len(versions) > 0:
             # OR logic for versions: ["versions:1.20.1", "versions:1.20"]
             v_facet = [f"versions:{v}" for v in versions]
             facets.append(v_facet)
             
        if loaders and len(loaders) > 0:
             # OR logic for loaders: ["categories:fabric", "categories:forge"]
             l_facet = [f"categories:{l.lower()}" for l in loaders]
             facets.append(l_facet)
             
        # Modrinth facets structure is List[List[str]] (AND of ORs)
        # If we have single string in list it's treated correctly? 
        # Actually structure is [[A, B], [C]] -> (A OR B) AND C
        
        final_facets = []
        final_facets.append([f"project_type:{project_type}"])
        if versions: final_facets.append([f"versions:{v}" for v in versions])
        if loaders: final_facets.append([f"categories:{l.lower()}" for l in loaders])
        
        params = {
            "query": query,
            "limit": limit,
            "index": index,
            "facets": json.dumps(final_facets)
        }
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()["hits"]
            return []
        except Exception as e:
            print(f"Modrinth Search Error: {e}")
            return []

    @staticmethod
    def get_project(project_id):
        url = f"{ModrinthAPI.BASE_URL}/project/{project_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Modrinth Project Error: {e}")
            return None

    @staticmethod
    def get_project_versions(project_id, loaders=None, game_versions=None):
        url = f"{ModrinthAPI.BASE_URL}/project/{project_id}/version"
        params = {}
        if loaders:
             params["loaders"] = json.dumps(loaders)
        if game_versions:
             params["game_versions"] = json.dumps(game_versions)
             
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Modrinth Version Error: {e}")
            return []
            
    @staticmethod
    def get_version_file(version_data):
        # Return the primary file URL and filename
        for file in version_data["files"]:
            if file["primary"]:
                return file["url"], file["filename"]
        # Fallback
        if version_data["files"]:
            return version_data["files"][0]["url"], version_data["files"][0]["filename"]
        return None, None
