from setuptools import setup, find_packages
with open('README.md', 'r') as fh:
    long_description = fh.read()
setup(
    name='dicee',
    description='Dice embedding is an hardware-agnostic framework for large-scale knowledge graph embedding applications',
    version='0.0.4',
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "pandas>=1.5.1",
        "polars>=0.16.14",
        "scikit-learn>=1.2.2",
        "pyarrow>=11.0.0",
        "pytorch-lightning==1.6.4",
        "pykeen==1.10.1",
        "zstandard>=0.21.0",
        "pytest>=7.2.2",
        "psutil>=5.9.4",
        "gradio>=3.23.0",
        "rdflib>=7.0.0"],
    author='Caglar Demir',
    author_email='caglardemir8@gmail.com',
    url='https://github.com/dice-group/dice-embeddings',
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License"],
    python_requires='>=3.10',
    long_description=long_description,
    long_description_content_type="text/markdown",
)
