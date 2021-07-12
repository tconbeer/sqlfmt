from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sqlfmt",
    version="0.1.0a1",
    author="Ted Conbeer",
    author_email="ted@shandy.io",
    description="sqlfmt is an opinionated CLI tool that formats your sql files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["sqlfmt"],
    package_dir={"": "src"},
    license="Apache-2.0",
    python_requires=">=3.7.0",
    install_requires=[
        "click>=7.1.2",
    ],
    entry_points={
        "console_scripts": [
            "sqlfmt = sqlfmt.cli:sqlfmt",
        ],
    },
)
