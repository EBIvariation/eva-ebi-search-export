import glob
from distutils.core import setup
from os.path import join, abspath, dirname

base_dir = abspath(dirname(__file__))
requirements_txt = join(base_dir, 'requirements.txt')
requirements = [l.strip() for l in open(requirements_txt) if l and not l.startswith('#')]

version = open(join(base_dir,  'VERSION')).read().strip()

setup(
    name='eva-ebi-search-export',
    packages=[],
    package_data={},
    version=version,
    license='Apache',
    description='EBI EVA - export to EBI search scripts',
    url='https://github.com/tcezard/eva-ebi-search-export',
    keywords=['ebi', 'eva', 'python', 'ebi-search'],
    install_requires=requirements,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.8'
    ],
    scripts=['study_export.py']
)
