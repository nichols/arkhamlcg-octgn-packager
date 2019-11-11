#!/usr/bin/env python3

import os
import re
import requests
import shutil
import arkham_common


def get_extension_from_url(url):
  ext = os.path.splitext(url)[1]
  if not re.match('^\.\w+$', ext):
    raise ValueError
  return ext


def download_img(url, dest):
  r = requests.get(url, stream=True, headers={'User-agent': 'Mozilla/5.0'})
  if r.status_code == 200:
    with open(dest, 'wb') as f:
      r.raw.decode_content = True
      shutil.copyfileobj(r.raw, f)
    return True
  else:
    print("WARNING: couldn't download image URL: {}, destination: {}".format(url, dest))
    return False


# download all card images, set filename = GUID, put in correct directory
def create_card_image_files(arkhamset, path):
  num = 0
  for card in arkhamset['cards']:
    url_front = card['front'].get('image_url', '')
    dest_front = os.path.join(
        path, card['id'] + get_extension_from_url(url_front))
    if download_img(url_front, dest_front):
      num += 1

    if arkham_common.is_double_sided(card):
      url_back = card['back']['image_url']
      dest_back = os.path.join(
        path, card['id'] + '.b' + get_extension_from_url(url_back))
      if download_img(url_back, dest_back):
        num += 1

  return num


def create_image_pack(arkhamset):
    # create image files for cards
    imagedb_path = os.path.join(
        "ImageDatabase", arkham_common.octgn_game_id, "Sets",
        arkhamset['id'], "Cards")
    try:
      os.makedirs(imagedb_path)
    except FileExistsError:
      pass
    num = create_card_image_files(arkhamset, imagedb_path)
    print("created {} card image files in {}.".format(num, imagedb_path))
    # TODO: zip images into o8c file
    return imagedb_path


def create_image_pack_for_set_from_json_file(json_file_path):
    arkhamset = arkham_common.load_set(json_file_path)
    return create_image_pack(arkhamset)


def main():
    if len(sys.argv) < 2:
        print("args: path to json file containing set data")
        return

    path = sys.argv[1]
    o8c_path = create_image_pack_for_set_from_json_file(path)
    print("created image pack {}".format(o8c_path))


if __name__ == '__main__':
    main()
