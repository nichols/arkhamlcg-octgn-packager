from setuptools import setup

setup(name='arkhamlcg-octgn-packager',
      version='0.1',
      description='Tools to create OCTGN packages for Arkham Horror LCG sets based on scraped data from cardgamedb.',
      url='http://github.com/nichols/arkhamlcg-octgn-packager',
      author='Daniel Nichols',
      author_email='daniel.g.nichols@gmail.com',
      license='GPL v3',
      packages=['arkhamlcg_octgn_packager'],
      scripts=['bin/arkhamlcg_octgn_packager'],
      zip_safe=True)
