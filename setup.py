"""
setuptools tabarnak packaging
"""
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tabarnak-desjare",  # Replace with your own username
    version="0.0.5",
    author="Eric Desjardins",
    author_email="desjare@gmail.com",
    description="transcoder FFmpeg based wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/desjare/tabarnak",
    packages=setuptools.find_packages(),
    install_requires=[
          "PyYAML",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console"
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'tabarnak = tabarnak.tabarnak:main',
        ],
    },
)
