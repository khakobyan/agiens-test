"""
Setup script for openclaw-deploy CLI tool.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text() if readme_file.exists() else ''

# Read requirements
requirements_file = Path(__file__).parent / 'requirements.txt'
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='openclaw-deploy',
    version='1.0.0',
    description='Production-ready automation tool for OpenClaw Docker deployments',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='OpenClaw DevOps Team',
    author_email='devops@openclaw.example',
    url='https://github.com/openclaw/openclaw-deploy',
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    install_requires=requirements,
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'openclaw-deploy=openclaw_deploy.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Systems Administration',
    ],
    keywords='openclaw docker deployment automation cli devops',
    project_urls={
        'Documentation': 'https://github.com/openclaw/openclaw-deploy#readme',
        'Source': 'https://github.com/openclaw/openclaw-deploy',
        'Tracker': 'https://github.com/openclaw/openclaw-deploy/issues',
    },
)
