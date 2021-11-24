from setuptools import setup
import io as m_io

with m_io.open('README.md', mode='r', encoding='utf-8') as v_fl:
    v_long_description = v_fl.read()

setup(
    name='conflex',
    keywords='configuration parser development',
    version='0.0.0a3',
    packages=['conflex'],
    url='https://github.com/TEH30P/conflex',
    license='MIT',
    author='TEH3OP',
    author_email='TEH3OP@gmail.com',
    description='Flexible and extensible configuration reader for python.',
    long_description=v_long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.6.0',
    extras_require={
        'testing': [
            'pytest >= 5.3.5',
            'pytest-cov >= 2.8.1',
            'mypy',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Intended Audience :: Education',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',

        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
