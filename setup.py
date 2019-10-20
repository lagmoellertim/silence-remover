import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name='silence-remover',
    version='1.0.0',
    license='MIT License',
    author='Tim-Luca Lagmöller',
    author_email='hello@lagmoellertim.de',
    description='Remove silent parts from any media file',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/lagmoellertim/silence-remover',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)