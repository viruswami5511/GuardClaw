"""
GuardClaw - Secure AI Agent Runtime
Setup configuration for pip installation.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = (this_directory / "requirements.txt").read_text().strip().split('\n')

setup(
    name="guardclaw",
    version="0.2.0",
    author="GuardClaw Team",
    author_email="hello@guardclaw.ai",
    description="Secure AI Agent Runtime - OpenClaw alternative with encrypted credentials",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/guardclaw",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "guardclaw=guardclaw:cli",
            "guardclaw-scanner=scanner.scanner:main",
        ],
    },
    include_package_data=True,
    keywords="ai agent security openclaw credentials encryption audit",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/guardclaw/issues",
        "Source": "https://github.com/yourusername/guardclaw",
        "Documentation": "https://guardclaw.ai/docs",
    },
)
