from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='graphWriter',
    version='0.2.0',
    author='Nicolas STAS',
    author_email='nicolas.jan.stas@gmail.com',
    description='A wrapper for TensorBoard SummaryWriter with real-time terminal visualization using the Rich library.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/COLVERTYETY/GraphWriter',
    packages=find_packages(),
    install_requires=required,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Visualization'
    ],
    python_requires='>=3.6',
)