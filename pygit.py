import os
import hashlib
import json
import datetime
import shutil
import sys
import readline  # For command history and arrow key support
from pathlib import Path
from subprocess import call

class PyGit:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.git_dir = self.repo_path / ".pygit"
        self.objects_dir = self.git_dir / "objects"
        self.commits_dir = self.git_dir / "commits"
        self.index_file = self.git_dir / "index.json"
        self.ignore_file = self.repo_path / ".pygitignore"

    def is_initialized(self):
        return self.git_dir.exists()

    def init(self):
        if self.is_initialized():
            print("Repository already exists!")
            return
        self.git_dir.mkdir()
        self.objects_dir.mkdir()
        self.commits_dir.mkdir()
        with open(self.index_file, 'w') as f:
            json.dump({"staged": {}, "head": None, "branches": {"main": None}, "current_branch": "main"}, f)
        if not self.ignore_file.exists():
            with open(self.ignore_file, 'w') as f:
                f.write(".pygit\n")
        print("Initialized empty PyGit repository")

    def _ensure_branch_structure(self, index):
        if "branches" not in index:
            index["branches"] = {"main": index.get("head")}
            index["current_branch"] = "main"
        return index

    def hash_object(self, content):
        return hashlib.sha1(content.encode()).hexdigest()

    def add(self, file_path):
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return
        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)
        if file_path == ".":
            files_added = False
            for item in self.repo_path.glob("*"):
                if item.is_file() and item.name not in {".pygit", ".pygitignore"}:
                    self._add_single_file(item)
                    files_added = True
            if not files_added:
                print("No files to add")
            return
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"File {file_path} does not exist!")
            return
        if file_path.name in {".pygit", ".pygitignore"}:
            return
        self._add_single_file(file_path)

    def _add_single_file(self, file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        obj_hash = self.hash_object(content)
        with open(self.objects_dir / obj_hash, 'w') as f:
            f.write(content)
        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index["staged"][str(file_path)] = obj_hash
        with open(self.index_file, 'w') as f:
            json.dump(index, f)
        print(f"Added {file_path} to staging area")

    def commit(self, message):
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
        with open(self.commits_dir / commit_hash, 'w') as f:
            json.dump(commit, f)
        index["branches"][index["current_branch"]] = commit_hash
        index["head"] = commit_hash
        index["staged"] = {}
        with open(self.index_file, 'w') as f:
            json.dump(index, f)
        print(f"Committed: {commit_hash[:7]} {message}")

    def log(self):
        if not self.is_initialized():
            print("Not a PyGit repository! Please run 'init' first.")
            return
        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)
        current_hash = index["branches"][index["current_branch"]]
        while current_hash:
            with open(self.commits_dir / current_hash, 'r') as f:
                commit = json.load(f)
            print(f"commit {current_hash[:7]}\nDate: {commit['timestamp']}\n    {commit['message']}\n")
            current_hash = commit["parent"]

    def status(self):
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
        current_files = {str(fp): self.hash_object(open(fp, 'r').read()) 
                        for fp in self.repo_path.glob("*") 
                        if fp.is_file() and fp.name not in {".pygit", ".pygitignore"}}
        staged = index["staged"]
        if staged:
            print("Changes staged for commit:\n  (use 'commit' to commit these changes)")
            for file_path in staged:
                print(f"    staged: {file_path}")
            print()
        modified = [fp for fp, ch in current_files.items() 
                   if fp in committed_files and ch != committed_files[fp] and fp not in staged]
        if modified:
            print("Changes not staged for commit:\n  (use 'add' to stage these changes)")
            for file_path in modified:
                print(f"    modified: {file_path}")
            print()
        untracked = [fp for fp in current_files if fp not in committed_files and fp not in staged]
        if untracked:
            print("Untracked files:\n  (use 'add' to track these files)")
            for file_path in untracked:
                print(f"    {file_path}")
            print()
        if not (staged or modified or untracked):
            print("Nothing to commit, working directory clean")

    def branch(self, *args):
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
        if len(args) == 1 and args[0] not in {"-d", "-m"}:
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
        with open(self.index_file, 'r') as f:
            index = json.load(f)
        index = self._ensure_branch_structure(index)
        committed_files = {}
        current_head = index["branches"][index["current_branch"]]
        if current_head:
            with open(self.commits_dir / current_head, 'r') as f:
                last_commit = json.load(f)
            committed_files = last_commit["files"]
        current_files = {str(fp): self.hash_object(open(fp, 'r').read()) 
                        for fp in self.repo_path.glob("*") 
                        if fp.is_file() and fp.name not in {".pygit", ".pygitignore"}}
        has_staged = bool(index["staged"])
        has_modified = any(fp in committed_files and ch != committed_files[fp] and fp not in index["staged"] 
                          for fp, ch in current_files.items())
        return has_staged, has_modified

    def _restore_branch_state(self, branch_name):
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
            if file_path.is_file() and file_path.name not in {".pygit", ".pygitignore"}:
                if str(file_path) not in target_files:
                    os.remove(file_path)
        for file_path, obj_hash in target_files.items():
            with open(self.objects_dir / obj_hash, 'r') as f:
                content = f.read()
            with open(file_path, 'w') as f:
                f.write(content)

    def checkout(self, branch_name):
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

    def merge(self, branch_name):
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
        with open(self.commits_dir / commit_hash, 'w') as f:
            json.dump(commit, f)
        index["branches"][current_branch] = commit_hash
        index["head"] = commit_hash
        self._restore_branch_state(current_branch)
        with open(self.index_file, 'w') as f:
            json.dump(index, f)
        print(f"Merged '{branch_name}' into '{current_branch}'")

    def help(self):
        print("PyGit Terminal - Commands:")
        print("  PyGit Commands:")
        print("    init                    Initialize a new PyGit repository")
        print("    add <file|'.'>         Add file(s) to staging area")
        print("    commit <message>       Commit staged changes")
        print("    log                    Show commit history")
        print("    status                 Show working directory status")
        print("    branch                 List all branches")
        print("    branch <name>          Create a new branch")
        print("    branch -d <name>       Delete a branch")
        print("    branch -m <old> <new>  Rename a branch")
        print("    checkout <name>        Switch to a branch")
        print("    merge <name>           Merge a branch into current")
        print("    help                   Show this help message")
        print("  Basic Terminal Commands:")
        print("    cd <dir>               Change directory")
        print("    ls/dir                 List directory contents")
        print("    pwd                    Print working directory")
        print("    cls/clear              Clear the screen")
        print("    exit                   Exit the terminal")

    def interactive_terminal(self):
        """Enhanced terminal-like interface with history and basic commands"""
        print("Welcome to PyGit Terminal! Type 'help' for commands, 'exit' to quit.")
        readline.set_history_length(1000)  # Store up to 1000 commands
        while True:
            try:
                command = input(f"pygit [{os.path.basename(os.getcwd())}]> ").strip()
                if not command:
                    continue
                args = command.split()
                cmd = args[0].lower()
                rest = args[1:]

                # PyGit Commands
                if cmd == "init":
                    self.init()
                elif cmd == "add" and rest:
                    self.add(rest[0])
                elif cmd == "commit" and rest:
                    self.commit(" ".join(rest))
                elif cmd == "log":
                    self.log()
                elif cmd == "status":
                    self.status()
                elif cmd == "branch":
                    self.branch(*rest)
                elif cmd == "checkout" and rest:
                    self.checkout(rest[0])
                elif cmd == "merge" and rest:
                    self.merge(rest[0])
                elif cmd == "help":
                    self.help()
                # Basic Terminal Commands
                elif cmd == "cd" and rest:
                    try:
                        os.chdir(rest[0])
                        self.repo_path = Path(os.getcwd())  # Update repo path
                        self.git_dir = self.repo_path / ".pygit"
                        self.objects_dir = self.git_dir / "objects"
                        self.commits_dir = self.git_dir / "commits"
                        self.index_file = self.git_dir / "index.json"
                        self.ignore_file = self.repo_path / ".pygitignore"
                    except Exception as e:
                        print(f"Error changing directory: {e}")
                elif cmd in {"ls", "dir"}:
                    files = [f.name for f in self.repo_path.glob("*")]
                    print(" ".join(files) if files else "Directory is empty")
                elif cmd == "pwd":
                    print(os.getcwd())
                elif cmd in {"cls", "clear"}:
                    os.system("cls" if os.name == "nt" else "clear")
                elif cmd == "exit":
                    print("Exiting PyGit Terminal.")
                    break
                else:
                    print(f"Unknown command: {cmd}. Type 'help' for available commands.")
            except Exception as e:
                print(f"Error: {e}")

def main():
    pygit = PyGit()
    if len(sys.argv) < 2 or sys.argv[1].lower() == "--terminal":
        pygit.interactive_terminal()
        return
    command = sys.argv[1].lower()
    if command == "init":
        pygit.init()
    elif command == "add" and len(sys.argv) == 3:
        pygit.add(sys.argv[2])
    elif command == "commit" and len(sys.argv) >= 3:
        pygit.commit(" ".join(sys.argv[2:]))
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
    else:
        print("Unknown command or wrong arguments")
        print("Run 'pygit help' for a list of commands")

if __name__ == "__main__":
    main()