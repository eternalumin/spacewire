"""SpaceWire/SpaceFibre Network Simulation Package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="spacewire-sim",
    version="1.0.0",
    author="SpaceWire Team",
    author_email="spacewire@example.com",
    description="SpaceWire/SpaceFibre Network Simulation for Spacecraft Communication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eternalumin/spacewire",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
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
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "spacewire-gui=spacewire.gui:main",
            "spacewire-sim=spacewire.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "spacewire": ["config/*.yaml", "config/*.json"],
    },
)
