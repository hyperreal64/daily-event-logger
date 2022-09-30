from setuptools import setup, find_packages


setup(
    name="elog",
    version="0.0.2",
    license="GPL-3.0",
    author="Jeffrey Serio",
    author_email="hyperreal@fedoraproject.org",
    packages=find_packages("src"),
    package_dir={"": "src"},
    url="https://github.com/hyperreal64/elog",
    keywords="elog",
    install_requires=[
        "jsonschema",
        "rich",
    ],
)