import os
import hashlib
import json
import datetime
import shutil
from pathlib import Path

class PyGit:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.git_dir = self.repo_path / ".pygit"
        self.objects_dir = self.git_dir / "objects"
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
            json.dump({"staged": {}, "head": None}, f)
        
        if not self.ignore_file.exists():
            with open(self.ignore_file, 'w') as f:
                f.write(".pygit\n")
        
        print("Initialized empty PyGit repository")

    def hash_object(self, content):
        """Create a hash of content similar to Git's blob objects"""
        return hashlib.sha1(content.encode()).hexdigest()

    def add(self, file_path):
        """Add a file or all files to staging area"""
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return

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

        if not index["staged"]:
            print("Nothing to commit!")
            return

        commit = {
            "timestamp": datetime.datetime.now().isoformat(),
            "message": message,
            "files": index["staged"],
            "parent": index["head"]
        }
        
        commit_hash = self.hash_object(json.dumps(commit))
        commit_path = self.commits_dir / commit_hash
        with open(commit_path, 'w') as f:
            json.dump(commit, f)

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
        
        current_hash = index["head"]
        while current_hash:
            commit_path = self.commits_dir / current_hash
            with open(commit_path, 'r') as f:
                commit = json.load(f)
            
            print(f"commit {current_hash[:7]}")
            print(f"Date: {commit['timestamp']}")
            print(f"    {commit['message']}\n")
            
            current_hash = commit["parent"]

    def status(self):
        """Show working directory status"""
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return

        with open(self.index_file, 'r') as f:
            index = json.load(f)

        committed_files = {}
        if index["head"]:
            with open(self.commits_dir / index["head"], 'r') as f:
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

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: pygit <command> [<args>]")
        print("Commands: init, add <file|'.'>, commit <message>, log, status")
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
    else:
        print("Unknown command or wrong arguments")

if __name__ == "__main__":
    main()