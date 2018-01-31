from setuptools import setup
import versioneer

setup(
        name='forget',
        description='A post-expiring service.',

        url='https://forget.codl.fr/',
        author='codl',
        author_email='codl@codl.fr',

        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
)


