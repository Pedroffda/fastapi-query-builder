"""
Setup script for FastAPI Query Builder Library
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fastapi-sqlalchemy-query-builder",
    version="1.0.1",
    author="Pedro",
    author_email="pedro@example.com",
    description="A library for building SQLAlchemy queries with support for advanced filtering, sorting, text search, field and relationship selection, pagination, and model to Pydantic schema mapping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pedroffda/fastapi-query-builder",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Framework :: FastAPI",
    ],
    python_requires=">=3.8",
    install_requires=[
        "sqlalchemy>=1.4.0",
        "fastapi>=0.68.0",
        "pydantic>=1.8.0",
        "starlette>=0.14.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0",
            "isort>=5.0",
            "flake8>=3.8",
            "mypy>=0.910",
        ],
    },
)
