"""
seleneko
--------

Selenium-based automation toolkit.
"""
from .core import config, encrypter
from .automation import SeleniumClient, DriverSettings

__all__ = [
    "config",
    "encrypter",
    "SeleniumClient",
    "DriverSettings",
]

__version__ = "0.1.0"
__author__ = "Nico"
__license__ = "Apache-2.0"
__copyright__ = "2025 Nico"
__url__ = "https://github.com/ardnico/seleneko"
__description__ = "Selenium-based automation toolkit."
__long_description__ = __doc__
__email__ = "leaf.sun2@gmail.com"
__keywords__ = ["selenium", "automation", "browser", "testing"]
__classifiers__ = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Testing",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
__install_requires__ = [
    "selenium>=4.35.0,<5.0",
]
__extras_require__ = {
    "dev": [
        "pytest>=7.0",
        "flake8>=3.9.0",
    ],
}
__python_requires__ = ">=3.9,<4.0"

