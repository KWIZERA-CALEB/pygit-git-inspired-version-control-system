import os
import hashlib
import json
import datetime
import shutil
from pathlib import Path
import requests
import base64
import getpass
from urllib.parse import urlparse

class PyGit:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.git_dir = self.repo_path / ".pygit"
        self.objects_dir = self.git_dir / "objects"
        self.config_path = self.git_dir / 'config.json'
        self.commits_dir = self.git_dir / "commits"
        self.index_file = self.git_dir / "index.json"
        self.ignore_file = self.repo_path / ".pygitignore"

    def is_initialized(self):
        """Check if repository is initialized"""
        return self.git_dir.exists()

    def init(self):
        """Initialize a new PyGit repository"""
        if self.is_initialized():
            print("Repository already exists!")
            return
        
        self.git_dir.mkdir()
        self.objects_dir.mkdir()
        self.commits_dir.mkdir()
        
        with open(self.index_file, 'w') as f:
            json.dump({
                "staged": {},
                "head": None,
                "branches": {"main": None},
                "current_branch": "main"
            }, f)
        
        if not self.ignore_file.exists():
            with open(self.ignore_file, 'w') as f:
                f.write(".pygit\n")
        
        print("Initialized empty PyGit repository")

    def _ensure_branch_structure(self, index):
        """Ensure index has branch structure for backward compatibility"""
        if "branches" not in index:
            index["branches"] = {"main": index.get("head")}
            index["current_branch"] = "main"
        return index

    def hash_object(self, content):
        """Create a hash of content similar to Git's blob objects"""
        return hashlib.sha1(content.encode()).hexdigest()

    def add(self, file_path):
        """Add a file or all files to staging area"""
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)

        if file_path == ".":
            files_added = False
            for item in self.repo_path.glob("*"):
                if (item.is_file() and 
                    item.name != ".pygit" and 
                    item.name != ".pygitignore"):
                    self._add_single_file(item)
                    files_added = True
            if not files_added:
                print("No files to add")
            return

        file_path = Path(file_path)
        if not file_path.exists():
            print(f"File {file_path} does not exist!")
            return
        if file_path.name == ".pygit" or file_path.name == ".pygitignore":
            return
        
        self._add_single_file(file_path)

    def _add_single_file(self, file_path):
        """Helper method to add a single file"""
        with open(file_path, 'r') as f:
            content = f.read()

        obj_hash = self.hash_object(content)
        obj_path = self.objects_dir / obj_hash
        with open(obj_path, 'w') as f:
            f.write(content)

        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)
        
        index["staged"][str(file_path)] = obj_hash
        
        with open(self.index_file, 'w') as f:
            json.dump(index, f)
        
        print(f"Added {file_path} to staging area")

    def commit(self, message):
        """Create a commit with staged changes"""
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)

        if not index["staged"]:
            print("Nothing to commit!")
            return

        commit = {
            "timestamp": datetime.datetime.now().isoformat(),
            "message": message,
            "files": index["staged"],
            "parent": index["branches"][index["current_branch"]]
        }
        
        commit_hash = self.hash_object(json.dumps(commit))
        commit_path = self.commits_dir / commit_hash
        with open(commit_path, 'w') as f:
            json.dump(commit, f)

        index["branches"][index["current_branch"]] = commit_hash
        index["head"] = commit_hash
        index["staged"] = {}
        
        with open(self.index_file, 'w') as f:
            json.dump(index, f)
        
        print(f"Committed: {commit_hash[:7]} {message}")

    def log(self):
        """Show commit history"""
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)
        
        current_hash = index["branches"][index["current_branch"]]
        while current_hash:
            commit_path = self.commits_dir / current_hash
            with open(commit_path, 'r') as f:
                commit = json.load(f)
            
            print(f"commit {current_hash[:7]}")
            print(f"Date: {commit['timestamp']}")
            print(f"    {commit['message']}\n")
            
            current_hash = commit["parent"]
    
    def get_latest_commit_hash(self):
        try:
            commits = sorted(self.commits_dir.iterdir(), key=os.path.getmtime, reverse=True)
            if commits:
                return commits[0].name
        except Exception as e:
            print("Error getting latest commit:", e)
        return None


    def status(self):
        """Show working directory status"""
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)

        print(f"On branch {index['current_branch']}")
        
        committed_files = {}
        current_head = index["branches"][index["current_branch"]]
        if current_head:
            with open(self.commits_dir / current_head, 'r') as f:
                last_commit = json.load(f)
            committed_files = last_commit["files"]

        current_files = {}
        for file_path in self.repo_path.glob("*"):
            if (file_path.is_file() and 
                file_path.name != ".pygit" and 
                file_path.name != ".pygitignore"):
                with open(file_path, 'r') as f:
                    content = f.read()
                current_files[str(file_path)] = self.hash_object(content)

        staged = index["staged"]
        if staged:
            print("Changes staged for commit:")
            print("  (use 'commit' to commit these changes)")
            for file_path, hash_val in staged.items():
                print(f"    staged: {file_path}")
            print()

        modified = []
        for file_path, current_hash in current_files.items():
            committed_hash = committed_files.get(file_path)
            staged_hash = staged.get(file_path)
            if (committed_hash and committed_hash != current_hash and 
                not (staged_hash and staged_hash == current_hash)):
                modified.append(file_path)

        if modified:
            print("Changes not staged for commit:")
            print("  (use 'add' to stage these changes)")
            for file_path in modified:
                print(f"    modified: {file_path}")
            print()

        untracked = [fp for fp in current_files.keys() 
                    if fp not in committed_files and fp not in staged]
        if untracked:
            print("Untracked files:")
            print("  (use 'add' to track these files)")
            for file_path in untracked:
                print(f"    {file_path}")
            print()

        if not (staged or modified or untracked):
            print("Nothing to commit, working directory clean")

    def branch(self, *args):
        """Handle branch operations: create, delete, rename, list"""
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)

        if not args:
            for branch_name, commit_hash in index["branches"].items():
                prefix = "*" if branch_name == index["current_branch"] else " "
                commit_info = commit_hash[:7] if commit_hash else "no commits"
                print(f"{prefix} {branch_name} ({commit_info})")
            return

        if len(args) == 1 and args[0] != "-d" and args[0] != "-m":
            branch_name = args[0]
            if branch_name in index["branches"]:
                print(f"Branch '{branch_name}' already exists!")
                return
            index["branches"][branch_name] = index["branches"][index["current_branch"]]
            with open(self.index_file, 'w') as f:
                json.dump(index, f)
            print(f"Created branch '{branch_name}'")
        
        elif len(args) == 2 and args[0] == "-d":
            branch_name = args[1]
            if branch_name not in index["branches"]:
                print(f"Branch '{branch_name}' does not exist!")
                return
            if branch_name == index["current_branch"]:
                print("Cannot delete the current branch!")
                return
            del index["branches"][branch_name]
            with open(self.index_file, 'w') as f:
                json.dump(index, f)
            print(f"Deleted branch '{branch_name}'")
        
        elif len(args) == 3 and args[0] == "-m":
            old_name, new_name = args[1], args[2]
            if old_name not in index["branches"]:
                print(f"Branch '{old_name}' does not exist!")
                return
            if new_name in index["branches"]:
                print(f"Branch '{new_name}' already exists!")
                return
            index["branches"][new_name] = index["branches"][old_name]
            del index["branches"][old_name]
            if index["current_branch"] == old_name:
                index["current_branch"] = new_name
            with open(self.index_file, 'w') as f:
                json.dump(index, f)
            print(f"Renamed branch '{old_name}' to '{new_name}'")
        
        else:
            print("Invalid branch command usage")

    def _get_working_dir_changes(self):
        """Check for staged or unstaged changes in working directory"""
        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)

        committed_files = {}
        current_head = index["branches"][index["current_branch"]]
        if current_head:
            with open(self.commits_dir / current_head, 'r') as f:
                last_commit = json.load(f)
            committed_files = last_commit["files"]

        current_files = {}
        for file_path in self.repo_path.glob("*"):
            if (file_path.is_file() and 
                file_path.name != ".pygit" and 
                file_path.name != ".pygitignore"):
                with open(file_path, 'r') as f:
                    content = f.read()
                current_files[str(file_path)] = self.hash_object(content)

        has_staged = bool(index["staged"])
        has_modified = False
        for file_path, current_hash in current_files.items():
            committed_hash = committed_files.get(file_path)
            staged_hash = index["staged"].get(file_path)
            if (committed_hash and committed_hash != current_hash and 
                not (staged_hash and staged_hash == current_hash)):
                has_modified = True
                break

        return has_staged, has_modified

    def _restore_branch_state(self, branch_name):
        """Restore working directory to match branch state"""
        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)

        target_commit = index["branches"][branch_name]
        target_files = {}
        if target_commit:
            with open(self.commits_dir / target_commit, 'r') as f:
                commit = json.load(f)
            target_files = commit["files"]

        for file_path in self.repo_path.glob("*"):
            if (file_path.is_file() and 
                file_path.name != ".pygit" and 
                file_path.name != ".pygitignore"):
                file_str = str(file_path)
                if file_str not in target_files:
                    os.remove(file_path)

        for file_path, obj_hash in target_files.items():
            with open(self.objects_dir / obj_hash, 'r') as f:
                content = f.read()
            with open(file_path, 'w') as f:
                f.write(content)

    def checkout(self, branch_name):
        """Switch to a branch with warnings and file restoration"""
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)

        if branch_name not in index["branches"]:
            print(f"Branch '{branch_name}' does not exist!")
            return

        if branch_name == index["current_branch"]:
            print(f"Already on branch '{branch_name}'")
            return

        has_staged, has_modified = self._get_working_dir_changes()
        if has_staged or has_modified:
            print("Warning: You have uncommitted changes!")
            if has_staged:
                print("- Staged changes will be lost")
            if has_modified:
                print("- Unstaged modifications will be lost")
            print("Please commit or stash your changes before switching branches.")
            return

        index["current_branch"] = branch_name
        index["head"] = index["branches"][branch_name]
        self._restore_branch_state(branch_name)
        
        with open(self.index_file, 'w') as f:
            json.dump(index, f)
        
        print(f"Switched to branch '{branch_name}'")
    

    # Configure user details email and username
    def config(self, key, value):
        config_path = self.git_dir / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        config[key] = value

        with open(config_path, 'w') as f:
            json.dump(config, f)
            print(f"Configured {key} = {value}")


    def login(self, username, token):
        auth_path = self.git_dir / "auth.json"
        with open(auth_path, 'w') as f:
            json.dump({"username": username, "token": token}, f)
        print(f"Logged in as {username}")

    #push
    def push(self):
        commit_hash = self.get_latest_commit_hash()
        if not commit_hash:
            print("No commits to push.")
            return

        commit_file = self.commits_dir / commit_hash
        with open(commit_file, 'r') as f:
            commit_data = json.load(f)

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        password = getpass.getpass("Password: ")

        # Extract repo name from remote URL
        remote_url = config.get("remote", "")
        if not remote_url:
            print("No remote URL configured. Use 'remote add' first.")
            return

        try:
            repo_name = remote_url.rstrip("/").split("/")[-1]
        except:
            print("Invalid remote URL format.")
            return

        files_payload = []

        for file_path, obj_hash in commit_data["files"].items():
            obj_file = self.objects_dir / obj_hash
            if not obj_file.exists():
                print(f"Missing object file for: {file_path}")
                continue
            files_payload.append(('files', (file_path, open(obj_file, 'rb'))))


        if not files_payload:
            print("No files found to push.")
            return

        data = {
            "username": config["username"],
            "repoName": repo_name,
            "password": password, # If needed
            "commitMessage": commit_data["message"],  # assumed to be saved in commit file
            "commitHash": commit_hash
        }

        try:
            response = requests.post(
                "http://localhost:5000/api/push-repository",
                data=data,
                files=files_payload  # this triggers multipart/form-data
            )
            if response.status_code == 200:
                print("Push successful:", response.json())
            else:
                print("Push failed:", response.status_code, response.text)
        finally:
            # Close all file objects
            # for f in files_payload.values():
            #     f[1].close()
            for _, (_, file_obj) in files_payload:
                file_obj.close()



    # def push(self):
    #     if not self.is_initialized():
    #         print("Not a PyGit repository! Please run 'init' first.")
    #         return

    #     config_path = self.git_dir / "config.json"
    #     if not config_path.exists():
    #         print("No config found! Please run 'config --user' and 'remote add origin <url>' first.")
    #         return

    #     with open(config_path, 'r') as f:
    #         config = json.load(f)

    #     username = config.get("username")
    #     email = config.get("email")
    #     remote = config.get("remote")

    #     if not (username and email and remote):
    #         print("Missing username/email/remote config. Run 'config --user' and 'remote add origin <url>'")
    #         return

    #     password = getpass.getpass("Password: ")
    #     repo_name = remote.rstrip("/").split("/")[-1]

    #     # Get latest commit
    #     with open(self.index_file, 'r') as f:
    #         index = json.load(f)
    #     commit_hash = index["head"]
    #     if not commit_hash:
    #         print("Nothing to push!")
    #         return

    #     commit_path = self.commits_dir / commit_hash
    #     with open(commit_path, 'r') as f:
    #         commit_data = json.load(f)

    #     files_payload = {}
    #     for file_path, obj_hash in commit_data["files"].items():
    #         with open(self.objects_dir / obj_hash, 'r') as f:
    #             files_payload[file_path] = f.read()

    #     payload = {
    #         "username": username,
    #         "email": email,
    #         "repoName": repo_name,
    #         "commit": commit_data,
    #         "files": files_payload,
    #         "password": password
    #     }

    #     try:
    #         response = requests.post('http://localhost:5000/api/push-repository', json=payload)
    #         if response.status_code == 200:
    #             # print(f"payload: {payload}")
    #             print("Push successful!")
    #         else:
    #             # print(f"payload: {payload}")
    #             print(f"Push failed: {response.status_code} {response.text}")
    #     except Exception as e:
    #         # print(f"payload: {payload}")
    #         print("Push error:", e)


    def clone(self, repo_url):
        try:
            # Extract username and repoName from URL
            parsed = urlparse(repo_url)
            parts = parsed.path.strip("/").split("/")
            if len(parts) != 2:
                print("Invalid clone URL format. Use: http://host/username/repoName")
                return

            username, repo_name = parts
            api_url = f"{parsed.scheme}://{parsed.netloc}/api/repos/{username}/{repo_name}/clone"

            print(f"Cloning from {api_url}...")

            response = requests.get(api_url)
            if response.status_code != 200:
                print(f"Failed to clone: {response.status_code} {response.text}")
                return

            files = response.json().get("files", [])
            if not files:
                print("No files in repository.")
                return

            # Create repo directory
            os.makedirs(repo_name, exist_ok=True)

            for file in files:
                file_path = os.path.join(repo_name, file["path"])
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                content = file["content"]
                if file["isBinary"]:
                    with open(file_path, "wb") as f:
                        f.write(base64.b64decode(content))
                else:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

            print(f"Repository '{repo_name}' cloned successfully.")
        except Exception as e:
            print(f"Error during clone: {e}")

    # New code

    

    def merge(self, branch_name):
        """Merge another branch into current branch"""
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)

        if branch_name not in index["branches"]:
            print(f"Branch '{branch_name}' does not exist!")
            return

        has_staged, has_modified = self._get_working_dir_changes()
        if has_staged or has_modified:
            print("You have uncommitted changes. Please commit or discard them first.")
            return

        current_branch = index["current_branch"]
        if branch_name == current_branch:
            print("Cannot merge branch with itself!")
            return

        source_commit = index["branches"][branch_name]
        if not source_commit:
            print(f"Branch '{branch_name}' has no commits to merge!")
            return

        with open(self.commits_dir / source_commit, 'r') as f:
            source_data = json.load(f)

        commit = {
            "timestamp": datetime.datetime.now().isoformat(),
            "message": f"Merge branch '{branch_name}' into '{current_branch}'",
            "files": source_data["files"],
            "parent": index["branches"][current_branch],
            "merge_parent": source_commit
        }
        
        commit_hash = self.hash_object(json.dumps(commit))
        commit_path = self.commits_dir / commit_hash
        with open(commit_path, 'w') as f:
            json.dump(commit, f)

        index["branches"][current_branch] = commit_hash
        index["head"] = commit_hash
        self._restore_branch_state(current_branch)
        
        with open(self.index_file, 'w') as f:
            json.dump(index, f)
        
        print(f"Merged '{branch_name}' into '{current_branch}'")

    def help(self):
        """Display list of all available commands"""
        print("PyGit - A simple Git-like version control system")
        print("Usage: pygit <command> [<args>]")
        print("\nAvailable commands:")
        print("  init                    Initialize a new PyGit repository")
        print("  add <file|'.'>         Add file(s) to staging area")
        print("  commit <message>       Commit staged changes with a message")
        print("  log                    Show commit history of current branch")
        print("  status                 Show working directory status")
        print("  branch                 List all branches")
        print("  branch <name>          Create a new branch")
        print("  branch -d <name>       Delete a branch")
        print("  branch -m <old> <new>  Rename a branch")
        print("  checkout <name>        Switch to a branch")
        print("  merge <name>           Merge a branch into current branch")
        print("  help                   Show this help message")

def main():
    import sys
    if len(sys.argv) < 2:
        # Show help when no command is provided
        PyGit().help()
        return

    pygit = PyGit()
    command = sys.argv[1]

    if command == "init":
        pygit.init()
    elif command == "add" and len(sys.argv) == 3:
        pygit.add(sys.argv[2])
    elif command == "commit" and len(sys.argv) >= 3:
        message = " ".join(sys.argv[2:])
        pygit.commit(message)
    elif command == "log":
        pygit.log()
    elif command == "status":
        pygit.status()
    elif command == "branch":
        pygit.branch(*sys.argv[2:])
    elif command == "checkout" and len(sys.argv) == 3:
        pygit.checkout(sys.argv[2])
    elif command == "merge" and len(sys.argv) == 3:
        pygit.merge(sys.argv[2])
    elif command == "help":
        pygit.help()
    # elif command == "config" and len(sys.argv) == 4:
    #     pygit.config(sys.argv[2], sys.argv[3])
    elif command == "config" and len(sys.argv) == 4:
        pygit_config_path = Path(".pygit") / "config.json"
        if not pygit_config_path.exists():
            config = {}
        else:
            with open(pygit_config_path, 'r') as f:
                config = json.load(f)
        
        key, value = sys.argv[2], sys.argv[3]
        if key not in ["username", "email"]:
            print("Invalid config key. Use 'username' or 'email'")
        else:
            config[key] = value
            with open(pygit_config_path, 'w') as f:
                json.dump(config, f)
            print(f"Configured {key} as {value}")
    elif command == "remote":
        pygit_config_path = Path(".pygit") / "config.json"
        if not pygit_config_path.exists():
            config = {}
        else:
            with open(pygit_config_path, 'r') as f:
                config = json.load(f)

        if len(sys.argv) == 5 and sys.argv[2] == "add" and sys.argv[3] == "origin":
            config["remote"] = sys.argv[4]
            with open(pygit_config_path, 'w') as f:
                json.dump(config, f)
            print(f"Remote 'origin' set to {sys.argv[4]}")

    elif len(sys.argv) == 3 and sys.argv[2] == "-v":
        if "remote" in config:
            print(f"origin\t{config['remote']}")
        else:
            print("No remote configured.")

    elif len(sys.argv) == 4 and sys.argv[2] == "remove" and sys.argv[3] == "origin":
        if "remote" in config:
            del config["remote"]
            with open(pygit_config_path, 'w') as f:
                json.dump(config, f)
            print("Remote 'origin' removed.")
        else:
            print("No remote to remove.")
    elif command == "push":
        pygit.push()
    elif command == "clone":
        if len(sys.argv) != 3:
            print("Usage: pygit clone <repo_url>")
        else:
            pygit.clone(sys.argv[2])

    else:
        print("Unknown command or wrong arguments")
        print("Run 'pygit help' for a list of commands")

if __name__ == "__main__":
    main()