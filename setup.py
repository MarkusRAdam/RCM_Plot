   
import os
import sys
from setuptools import setup, find_packages

directory = os.path.abspath(os.path.dirname(__file__))
if sys.version_info >= (3, 0):
    with open(os.path.join(directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
else:
    with open(os.path.join(directory, 'README.md')) as f:
        long_description = f.read()

if not os.path.exists("requirements.txt"):
    print("Make sure that the requirements.txt is located in the working directory.")
    sys.exit()
else:
    with open("requirements.txt", "r") as req:
        requires = []
        for line in req:
            requires.append(line.strip())

setup(name="RCM_Plot",
      packages=find_packages(),
      include_package_data=True,
      description="Python tool for displaying time series of Radar backscatter and NDVI values in a web app.",
      version="0.1",
      keywords="remote-sensing, streamlit-webapp, crop-monitoring",
      python_requires=">=3.8.0",
      setup_requires=[""],
      install_requires=requires,
      extras_require={
          "docs": ["sphinx==4.0.1"],
      },
      classifiers=[
          "Programming Language :: Python",
          "Operating System :: OS Independent",
          "Topic :: Utilities",
      ],
      url="https://github.com/MarkusRAdam/RCM_Plot",
      author="Markus Adam and Laura Walder",  
      author_email="markus.adam@uni-jena.de",
      license="GPL-3",
      zip_safe=False,
      long_description=long_description,
      long_description_content_type="text/markdown")
