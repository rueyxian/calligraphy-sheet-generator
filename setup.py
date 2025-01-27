from setuptools import setup, find_packages

setup(
    name="cgsg",
    version="0.0.0",
    description="calligraphy sheet generator",
    author="rueyxian",
    email="yrueyxian@gmail.com",
    install_requires=[
        "pillow",
    ],
    packages=find_packages(),
    entry_points={
        "console_scripts": ["cgsg=script.main:main"],
    },
)
