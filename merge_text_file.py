import re
import os
import sys
import json
import yaml

from datetime import datetime
from typing import Callable
from pathlib import Path
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import Template
from pydantic import BaseModel
from loguru import logger

logger.remove()

logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    enqueue=True
)
logger.add(
    "./logs/merge_text_file_{time:YYYY-MM-DD_HH-mm-ss}.log",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    enqueue=True,
    delay=True,
)

class Guidance(BaseModel):
    index_file: str = "index.md"
    encoding: str = "utf-8"
    output_file: str = "output.md"

def safe_relative_to(path: Path, base: Path) -> Path:
    try:
        return path.relative_to(base)
    except ValueError:
        return path

class MergeTextFile:
    def __init__(self):
        self.guidance = Guidance()
    
    @staticmethod
    def wrap_file(text: str, file_path: Path) -> str:
        text_buffer: list[str] = []
        text_buffer.append(f"[file: \"./{file_path.as_posix()}\"]")
        text_buffer.append("[file content begin]")
        text_buffer.append(text)
        text_buffer.append("[file content end]")
        text_buffer.append("")
        return "\n".join(text_buffer)
    
    @staticmethod
    def get_markdown_code_block_wrap(code_type: str) -> Callable[[str, Path], str]:
        def wrap(text: str, file_path: Path) -> str:
            text_buffer: list[str] = []
            text_buffer.append(f"``` {code_type}")
            text_buffer.append(text)
            text_buffer.append("```")
            return "\n".join(text_buffer)
        return wrap
    
    @staticmethod
    def get_custom_wrap(template: str) -> Callable[[str, Path], str]:
        environment = SandboxedEnvironment()
        wrap_template = environment.from_string(template)
        def wrap(text: str, file_path: Path) -> str:
            return wrap_template.render(
                text=text,
                file_path=file_path
            )
        return wrap

    @classmethod
    def parse_file(cls, path: Path, base_path: Path, encoding: str = "utf-8", file_path_pattern: re.Pattern | None = None, wrap_file: Callable[[str, Path], str] | None = None) -> str:
        if path.is_file():
            try:
                with open(path, "r", encoding = encoding) as f:
                    file_content = f.read()
            except Exception as e:
                logger.error(
                    "Error when reading file: {path}",
                    path = path,
                    exc_info = e
                )
                return F"[File Read Error: {e}]"
            logger.info(
                "Read file: {path}",
                path = path.as_posix(),
            )
            if file_path_pattern is not None:
                if not file_path_pattern.match(path.absolute().as_posix()):
                    return ""

            relative_path = safe_relative_to(path, base_path)
            if callable(wrap_file):
                text = wrap_file(file_content, relative_path)
            else:
                text = cls.wrap_file(file_content, relative_path)
            return text
        else:
            raise ValueError(f"{path} is not a file")
    
    @classmethod
    def merge_text(cls, path: Path, base_path: Path = None, encoding: str = "utf-8", file_path_pattern: re.Pattern | None = None, wrap_file: Callable[[str, Path], str] | None = None) -> list[str]:
        text_buffer: list[str] = []
        if path.is_dir():
            if base_path is None:
                base_path = path
            
            for sub_path in path.iterdir():
                if sub_path.is_file():
                    text_buffer.append(cls.parse_file(sub_path, base_path, encoding, file_path_pattern, wrap_file))
                if sub_path.is_dir():
                    text_buffer.extend(cls.merge_text(sub_path, base_path, encoding, file_path_pattern, wrap_file))
            
        elif path.is_file():
            if base_path is None:
                base_path = path.parent

            text_buffer.append(cls.parse_file(path, base_path, encoding, file_path_pattern, wrap_file))
        return text_buffer
    
    @classmethod
    def tree(cls, path: Path, indent: int = 0):
        buffer: list[str] = []
        buffer.append(f"{' ' * max(indent - 2, 0)}- {path.name}")
        if path.is_dir():
            for sub_path in path.iterdir():
                if sub_path.is_file():
                    buffer.append(f"{' ' * indent}- {sub_path.name}")
                if sub_path.is_dir():
                    buffer.extend(cls.tree(sub_path, indent + 2))
        return buffer
    
    def load_guidance(self) -> None:
        json_guidance_path = Path("./guidance.json")
        yaml_guidance_path = Path("./guidance.yml")
        
        if json_guidance_path.exists():
            with open(json_guidance_path, "r", encoding="utf-8") as f:
                self.guidance = Guidance(
                    **json.load(f)
                )
        elif yaml_guidance_path.exists():
            with open(yaml_guidance_path, "r", encoding="utf-8") as f:
                self.guidance = Guidance(
                    **yaml.safe_load(f)
                )
        else:
            raise FileNotFoundError("Guidance file not found.")
    
    def render(self, file_path: str):
        with open(file_path, "r", encoding = self.guidance.encoding) as f:
            index_template = f.read()
        
        # Change directory to index file's directory.
        base_path = Path(file_path).parent
        environment = SandboxedEnvironment()
        template: Template = environment.from_string(index_template)

        def merge_text(path: str | os.PathLike, encoding: str = self.guidance.encoding, file_path_pattern: str | None = None, wrap_file: Callable[[str, Path], str] | None = None) -> str:
            path = Path(path)
            compiled_file_path_pattern = None
            if file_path_pattern is not None:
                compiled_file_path_pattern = re.compile(file_path_pattern)
            text = "\n".join(
                self.merge_text(
                    base_path / path,
                    base_path,
                    encoding = encoding,
                    file_path_pattern = compiled_file_path_pattern,
                    wrap_file = wrap_file
                )
            )
            if not text:
                logger.warning(
                    "{path} not loaded anything.",
                    path = path.as_posix()
                )
            return text
        
        def tree(path: str | os.PathLike):
            path = Path(path)
            path = safe_relative_to(path, base_path)
            text = "\n".join(
                self.tree(
                    path = base_path,
                )
            )
            if not text:
                logger.warning(
                    "{path} not found anything.",
                    path = base_path.as_posix()
                )
            return text

        rendered_template: str = template.render(
            merge_text = merge_text,
            wrap_file = self.wrap_file,
            tree = tree,
            get_markdown_code_block_wrap = self.get_markdown_code_block_wrap,
            get_custom_wrap = self.get_custom_wrap,
            console_input = input,
            now = datetime.now(),
            recursion_template = self.render,
            sub_template = self.render
        )

        return rendered_template
    
    def main_render(self) -> None:
        rendered_template = self.render(
            self.guidance.index_file,
        )

        with open(self.guidance.output_file, "w", encoding = self.guidance.encoding) as f:
            f.write(rendered_template)

def main():
    guidance = MergeTextFile()
    guidance.load_guidance()
    guidance.main_render()

if __name__ == "__main__":
    main()