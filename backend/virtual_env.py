import os
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import json
import shutil

class VirtualEnvironmentManager:
    def __init__(self, safe_name: str, folder_path: str = ""):
        self.safe_name = safe_name
        self.data_path = Path(os.getenv("PYSCHED_DATA_PATH", "./data"))
        
        # Build script path using safe name and folder structure
        if folder_path:
            self.script_path = self.data_path / "scripts" / folder_path / safe_name
        else:
            self.script_path = self.data_path / "scripts" / safe_name
            
        self.venv_path = self.script_path / ".venv"
        self.script_file = self.script_path / f"{safe_name}.py"
        self.requirements_file = self.script_path / "requirements.txt"
    
    async def create_environment(self, python_version: str = "3.12") -> Dict[str, Any]:
        """Create virtual environment"""
        try:
            # Create directory structure
            self.script_path.mkdir(parents=True, exist_ok=True)
            
            # Determine Python executable
            python_executable = f"python{python_version}"
            
            # Try to find the Python executable
            try:
                result = await asyncio.create_subprocess_exec(
                    "which", python_executable,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode != 0:
                    # Fallback to python3 if specific version not found
                    python_executable = "python3"
            except:
                python_executable = "python3"
            
            # Create virtual environment
            process = await asyncio.create_subprocess_exec(
                python_executable, "-m", "venv", str(self.venv_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to create venv: {stderr.decode()}"
                }
            
            # Upgrade pip
            pip_path = self.venv_path / "bin" / "pip"
            if not pip_path.exists():
                pip_path = self.venv_path / "Scripts" / "pip.exe"  # Windows
            
            if pip_path.exists():
                process = await asyncio.create_subprocess_exec(
                    str(pip_path), "install", "--upgrade", "pip",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
            
            return {"success": True, "message": "Virtual environment created"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def install_requirements(self, requirements: str) -> Dict[str, Any]:
        """Install requirements in virtual environment"""
        if not requirements.strip():
            return {"success": True, "message": "No requirements to install"}
        
        try:
            # Write requirements file
            self.requirements_file.write_text(requirements)
            
            # Install requirements
            pip_path = self.venv_path / "bin" / "pip"
            if not pip_path.exists():
                pip_path = self.venv_path / "Scripts" / "pip.exe"  # Windows
            
            if not pip_path.exists():
                return {"success": False, "error": "pip not found in virtual environment"}
            
            process = await asyncio.create_subprocess_exec(
                str(pip_path), "install", "-r", str(self.requirements_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "exit_code": process.returncode
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_script(self, content: str, environment_variables: str = "{}") -> Dict[str, Any]:
        """Execute script in virtual environment with custom env vars"""
        try:
            # Write script file
            self.script_file.write_text(content)
            
            # Prepare environment variables
            env = os.environ.copy()
            try:
                custom_env = json.loads(environment_variables)
                env.update(custom_env)
            except (json.JSONDecodeError, TypeError):
                pass  # Use default environment if JSON is invalid
            
            # Execute script
            python_path = self.venv_path / "bin" / "python"
            if not python_path.exists():
                python_path = self.venv_path / "Scripts" / "python.exe"  # Windows
            
            if not python_path.exists():
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": "Python executable not found in virtual environment",
                    "duration_ms": 0
                }
            
            start_time = asyncio.get_event_loop().time()
            
            process = await asyncio.create_subprocess_exec(
                str(python_path), str(self.script_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.script_path),
                env=env
            )
            
            stdout, stderr = await process.communicate()
            end_time = asyncio.get_event_loop().time()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "duration_ms": int((end_time - start_time) * 1000)
            }
            
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration_ms": 0
            }
    
    def cleanup(self):
        """Remove virtual environment and files"""
        if self.script_path.exists():
            shutil.rmtree(self.script_path)
    
    def exists(self) -> bool:
        """Check if virtual environment exists"""
        return self.venv_path.exists()
    
    def get_script_path(self) -> Path:
        """Get the script directory path"""
        return self.script_path
    
    def get_venv_path(self) -> Path:
        """Get the virtual environment path"""
        return self.venv_path