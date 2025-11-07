Instagram Profile Image Scraper

A Python script to scrape and download images from a public Instagram profile using Selenium.

Features

Logs into Instagram using credentials stored in a .env file.

Navigates to a target profile.

Scrolls through posts dynamically to load images.

Filters out small or icon-like images based on alt text length.

Downloads images to a local folder (images/<target_profile>).

Configurable number of images to download.

Requirements

Python 3.10+

Microsoft Edge (or another supported browser)

Python packages:

pip install selenium python-dotenv requests

Installation

Clone the repository:

git clone <your-repo-url>
cd <your-repo-folder>


Place a .env file in the root directory (one level above src/) with your Instagram credentials:

INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password


Make sure the images/ folder will be created automatically when the script runs.

Usage

Configure the target profile and number of images in instagram_profile_image_scraper.py:

TARGET_PROFILE = "barbaralennie"  # Instagram username of the target profile
NUM_IMAGES = 5                     # Number of images to download


Run the script:

python src/instagram_profile_image_scraper.py


The images will be saved in:

images/<target_profile>/

Notes

The script uses InPrivate mode in Edge to avoid cookie issues.

Optionally, you can enable headless mode:

edge_options.add_argument("--headless=new")


Images with short alt text (usually icons or small UI images) are ignored.

If the profile has fewer images than requested, the script will notify you.

License

This project is licensed under the MIT License.
