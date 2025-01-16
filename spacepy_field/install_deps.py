import os
import site
import shutil
import tarfile
import logging
import urllib.request

url_ts07 = "http://mag.gmu.edu/git-data/spacepy-fields/all.tgz"
url_omni = "https://spp-isois.sr.unh.edu/data_public/omni/"

logger = logging.getLogger(__name__)

def download(url, dest):
  # Note that SpacePy has a download function in spacepy/util.py
  dest_dir = os.path.dirname(dest)
  if not os.path.exists(dest_dir):
    logger.info(f"Creating directory {dest_dir}")
    os.makedirs(dest_dir)

  if os.path.exists(dest):
    logger.info(f"{dest} already exists. Skipping download from {url}")
    return

  logger.info(f"Downloading {url} to {dest}")
  urllib.request.urlretrieve(url, dest)
  logger.info(f"Downloaded {url} to {dest}")

def ts07(year, doy, url=url_ts07):

  # Downloads ~1.7 GB
  #  http://mag.gmu.edu/git-data/spacepy-fields/all.tgz
  # and installs files needed for TS07 magnetic field model. Performs operation
  # similar to
  #  https://github.com/PRBEM/IRBEM/blob/main/setup_ts07d_files.sh
  # Note that SpacePy has TAIL_PAR in install package, but not Coeffs directory.

  # TODO:
  #   1. Ask SPDF to host all.tgz files.
  #   2. Determine if TAL_PAR directory in SpacePy is up-to-date and complete.
  #   3. Only extract files needed for a given date? Extracting all files from all.tgz
  #      takes ~5 minutes.
  #   4. Suggest SpacePy model notes "TS07" in IRBEM means "TS07D" (based on directory
  #      name data files in SpacePy installation, e.g.,
  #      /opt/miniconda3/lib/python3.12/site-packages/spacepy/data/TS07D/)

  def extract_year_doy_tgz(year, doy):

    year_doy_file = f"{year}/{year}_{doy:03d}.tgz"
    year_doy_tgz = os.path.join(all_tgz_dir, year_doy_file)
    logger.info(f"Looking for {year_doy_tgz} in {all_tgz}")
    if os.path.exists(year_doy_tgz):
      logger.info(f"{year_doy_tgz} already extracted from {all_tgz}. Skipping extraction.")
    else:
      with tarfile.open(all_tgz, 'r:*') as tar:
        for member in tar.getmembers():
          if member.name == year_doy_file:
            logger.info(f"Extracting {year_doy_tgz} to {all_tgz_dir}")
            tar.extract(member, path=all_tgz_dir)
    return year_doy_tgz

  def extract_year_doy_coeffs(year, doy):
    year_doy_tgz = extract_year_doy_tgz(year, doy)
    path = os.path.join(year_doy_tgz.replace(".tgz", ""))
    if os.path.exists(path):
      logger.info(f"{path} already exists. Skipping extraction from {year_doy_tgz}")
    else:
      with tarfile.open(year_doy_tgz, 'r:*') as tar:
        logger.info(f"Extracting {year_doy_tgz} to {path}")
        tar.extractall(path=path)
        # Move the extracted directory one directory up
        extracted_dir = os.path.join(all_tgz_dir, f"{year}_{doy:03d}")
        if os.path.exists(extracted_dir):
            logger.info(f"{extracted_dir} already exists. Skipping move.")
        else:
            logger.info(f"Moving {path} to {extracted_dir}")
            shutil.move(path, extracted_dir)

  all_tgz = os.path.join(site.getsitepackages()[0], "spacepy", "data", "TS07D", "Coeffs", "all.tgz")
  all_tgz_dir = os.path.dirname(all_tgz)

  download(url, all_tgz)
  extract_year_doy_coeffs(year, doy)

def omni(url=url_omni):
  download(url + "omnidata.h5", os.path.expanduser("~/.spacepy/data/omnidata.h5"))
  download(url + "omni2data.h5", os.path.expanduser("~/.spacepy/data/omni2data.h5"))

if __name__ == "__main__":
  ts07(year=1995, doy=1)
  omni()
