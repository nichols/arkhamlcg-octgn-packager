#!/usr/bin/env python3

import os
import re
import requests
import shutil
import arkham_lib

class CardImageDownloadError(Exception):
    """Exception when trying to download a card image from cardgamedb."""
    pass

def get_extension_from_url(url):
    ext = os.path.splitext(url)[1]
    if not re.match('^\.\w+$', ext):
        raise ValueError
    return ext

def download_img(url, dest):
    response = requests.get(
        url, stream=True, headers={'User-agent': 'Mozilla/5.0'})
    if not response:
        raise CardImageDownloadError(url)
    with open(dest, 'wb') as f:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, f)

# Create properly-labeled image files in ImageDatabase directory for all cards
# in this set.
def create_card_image_files(arkhamset, path):
    num = 0
    for card in arkhamset.cards:
        url_front = card.front.image_url
        dest_front = os.path.join(
            path, card.id + get_extension_from_url(url_front))
        download_img(url_front, dest_front)
        num += 1

        if card.is_double_sided:
            url_back = card.back.image_url
            dest_back = os.path.join(
                path, card.id + '.b' + get_extension_from_url(url_back))
            download_img(url_back, dest_back)
            num += 1

    return num

def create_image_pack(arkhamset, prefix=None):
    # create image files for cards
    imagedb_path = os.path.join(["ImageDatabase", constants.octgn_game_id,
        "Sets", arkhamset['id'], "Cards"])
    if prefix is not None:
        imagedb_path = os.path.join([prefix, imagedb_path])
    try:
      os.makedirs(imagedb_path)
    except FileExistsError:
      pass
    num = create_card_image_files(arkhamset, imagedb_path)
    return imagedb_path, num
