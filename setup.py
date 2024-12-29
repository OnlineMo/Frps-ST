from setuptools import setup, find_packages

setup(
    name='frps_st',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'frps_st': ['frpc.exe'],
    },
    entry_points={
        'console_scripts': [
            'frps-st=frps_st.main:main',
        ],
    },
    install_requires=[
        'requests',
    ],
    author='Mzy',
    author_email='mzy.mail@qq.com',
    description='A library for testing download speed using frpc',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/OnlineMo/Frps-ST',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
