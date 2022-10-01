from setuptools import setup, find_packages


setup(
    name="daily-event-logger",
    version="0.0.8",
    license="GPL-3.0",
    author="Jeffrey Serio",
    author_email="hyperreal@fedoraproject.org",
    packages=find_packages("src"),
    package_dir={"": "src"},
    url="https://github.com/hyperreal64/daily-event-logger",
    keywords="daily-event-logger",
    install_requires=[
        "jsonschema",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "elog = elog.elog:main",
        ]
    },
)