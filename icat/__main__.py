import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Union

from traitlets.config import Config
from traitlets.config.loader import PyFileConfigLoader


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Setup IPython with icat integration")
    subparsers = parser.add_subparsers(dest="command")

    setup_parser = subparsers.add_parser("setup", help="Configure IPython to use icat")
    setup_parser.add_argument(
        "--profile", default="default", help="IPython profile name"
    )
    setup_parser.add_argument(
        "--ipython-path", default=None, help="Custom path to .ipython directory"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "setup":
        try:
            success = setup_ipython_profile(args.ipython_path, args.profile)
            if not success:
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


def setup_ipython_profile(
    ipython_path: Optional[str] = None, profile_name: str = "default"
) -> bool:
    """Update or create an IPython profile to use the icat backend."""
    profile_path = get_profile_path(profile_name, ipython_path)

    extensions_line, exec_lines_line = dynamic_update_config(profile_path)
    lines = dynamic_update_file(profile_path, extensions_line, exec_lines_line)

    try:
        with profile_path.open("w") as f:
            f.writelines(lines)
    except IOError as e:
        raise RuntimeError(f"Failed to write to config file {profile_path}: {e}")

    print(f"Successfully updated IPython config at {profile_path}")
    return True


def sanitize_profile_name(profile_name: str) -> str:
    """Sanitize profile name to prevent command injection"""
    # Allow only alphanumeric characters, dashes and underscores
    if not profile_name or not re.match(r"^[a-zA-Z0-9_-]+$", profile_name):
        raise ValueError(
            "Profile name must contain only alphanumeric characters, underscores, or dashes"
        )
    return profile_name


def get_profile_path(
    profile_name: str, ipython_path: Optional[Union[str, Path]] = None
) -> Path:
    """Silently create a default profile if it doesn't exist"""
    profile_name = sanitize_profile_name(profile_name)

    try:
        if ipython_path is None:
            ipython_path = Path.home() / ".ipython"
        else:
            ipython_path = Path(ipython_path).expanduser().resolve()

        if not ipython_path.exists():
            raise FileNotFoundError(f"IPython path {ipython_path} does not exist")

        profile_dir = ipython_path / f"profile_{profile_name}"
        if not profile_dir.exists():
            try:
                _ = subprocess.run(
                    ["ipython", "profile", "create", profile_name], check=True
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to create IPython profile: {e.stderr}")

        profile_path = profile_dir / "ipython_config.py"
        return profile_path
    except (PermissionError, OSError) as e:
        raise RuntimeError(f"Error accessing IPython paths: {e}")


def dynamic_update_config(profile_path: Path) -> Tuple[str, str]:
    """Returns updated extensions and exec_lines"""
    profile_path = Path(profile_path)

    config = Config()
    if profile_path.exists():
        try:
            config_loader = PyFileConfigLoader(
                filename=profile_path.name, path=str(profile_path.parent)
            )
            config = config_loader.load_config()
        except Exception as e:
            raise RuntimeError(f"Error loading IPython config: {e}")

    # Ensure extensions and exec_lines are lists
    extensions = config.get("InteractiveShellApp", {}).get("extensions", [])
    exec_lines = config.get("InteractiveShellApp", {}).get("exec_lines", [])

    if "icat" not in extensions:
        extensions.append("icat")

    if "%icat on" not in exec_lines and "%icat" not in exec_lines:
        exec_lines.append("%icat on")

    extensions_line = f"c.InteractiveShellApp.extensions = {extensions}\n"
    exec_lines_line = f"c.InteractiveShellApp.exec_lines = {exec_lines}\n"

    return extensions_line, exec_lines_line


def dynamic_update_file(
    profile_path: Path, extensions_line: str, exec_lines_line: str
) -> List[str]:
    """Write updated configuration to the file"""
    profile_path = Path(profile_path)

    # Read and modify only the necessary lines
    if profile_path.exists():
        try:
            with open(profile_path, "r") as f:
                lines = f.readlines()
        except IOError as e:
            raise RuntimeError(f"Could not read config file {profile_path}: {e}")

        # Modify lines if they exist; otherwise, add them
        found_extensions = False
        found_exec_lines = False

        for i, line in enumerate(lines):
            if line.startswith("c.InteractiveShellApp.extensions ="):
                lines[i] = extensions_line
                found_extensions = True
            elif line.startswith("c.InteractiveShellApp.exec_lines ="):
                lines[i] = exec_lines_line
                found_exec_lines = True

        if not found_extensions:
            lines.append(extensions_line)
        if not found_exec_lines:
            lines.append(exec_lines_line)

        return lines
    else:
        return [extensions_line, exec_lines_line]


if __name__ == "__main__":
    main()
