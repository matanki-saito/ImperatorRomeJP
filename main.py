#!/usr/bin/env python
# -*- coding:utf-8 -*-

import hashlib
import json
import os
import shutil
import urllib.request
import zipfile
from os.path import join

from boto3.session import Session

_ = join


def download_trans_zip_from_paratranz(project_id,
                                      secret,
                                      out_file_path,
                                      base_url="https://paratranz.cn"):
    """
    paratranzからzipをダウンロードする
    :param project_id:
    :param secret:
    :param base_url:
    :param out_file_path:
    :return:
    """

    request_url = "{}/api/projects/{}/artifacts/download".format(base_url, project_id)
    req = urllib.request.Request(request_url)
    req.add_header("Authorization", secret)

    with open(out_file_path, "wb") as my_file:
        my_file.write(urllib.request.urlopen(req).read())

    return out_file_path


def assembly_mod(mod_file_name,
                 resource_dir_path,
                 resource_paratranz_main_zip_file_path,
                 resource_paratranz_sub_zip_file_path,
                 out_dir_path):
    """
    Appモッドを作成
    :param mod_file_name: Modファイル名
    :param resource_paratranz_main_zip_file_path: ParatranzからダウンロードできるMain Mod zipファイルのパス
    :param resource_paratranz_sub_zip_file_path: ParatranzからダウンロードできるSub Mod zipファイルのパス
    :param resource_dir_path: リソースディレクトリパス
    :param out_dir_path: 出力フォルダ
    :return:
    """

    # TODO パス修正する
    ext_paratranz_main_dir_path = _(".", "tmp", "paratranz_ext_main")
    ext_paratranz_sub_dir_path = _(".", "tmp", "paratranz_ext_sub")
    mod_dir_path = _(out_dir_path, mod_file_name)
    mod_loc_dir_path = _(mod_dir_path, "localization", "replace")
    mod_gui_dir_path = _(mod_dir_path, "gui")

    # 初期化（AzureDevでは必要ない）
    if os.path.exists(ext_paratranz_main_dir_path):
        shutil.rmtree(ext_paratranz_main_dir_path)
    if os.path.exists(ext_paratranz_sub_dir_path):
        shutil.rmtree(ext_paratranz_sub_dir_path)
    if os.path.exists(mod_dir_path):
        shutil.rmtree(mod_dir_path)
    os.makedirs(mod_dir_path, exist_ok=True)
    os.makedirs(mod_loc_dir_path, exist_ok=True)

    # zip展開する
    with zipfile.ZipFile(resource_paratranz_main_zip_file_path) as existing_zip:
        existing_zip.extractall(ext_paratranz_main_dir_path)

    with zipfile.ZipFile(resource_paratranz_sub_zip_file_path) as existing_zip:
        existing_zip.extractall(ext_paratranz_sub_dir_path)

    # 画像ファイルを入れる
    shutil.copy(_(resource_dir_path, "title.jpg"), mod_dir_path)

    # フォントフォルダを入れる
    shutil.copytree(_(resource_dir_path, "fonts"),
                    _(mod_dir_path, "fonts"))

    # clausewitzを移す
    shutil.copytree(_(ext_paratranz_main_dir_path, "utf8", "clausewitz", "localization"),
                    _(mod_loc_dir_path, "clausewitz"))

    # jominiを移す
    shutil.copytree(_(ext_paratranz_main_dir_path, "utf8", "jomini", "localization"),
                    _(mod_loc_dir_path, "jomini"))

    # gameを移す
    shutil.copytree(src=_(ext_paratranz_main_dir_path, "utf8", "game", "localization", "english"),
                    dst=_(mod_loc_dir_path, "english"),
                    ignore=shutil.ignore_patterns("character_names_l_english.yml",
                                                  "countries_l_english.yml",
                                                  "cultures_l_english.yml",
                                                  "god_names_l_english.yml",
                                                  "macroregions_l_english.yml",
                                                  "nicknames_l_english.yml",
                                                  "provincenames_l_english.yml"
                                                  "regionnames_l_english.yml",
                                                  "wonders_l_english.yml"
                                                  ))

    # ダウンロードしたファイルから
    shutil.copytree(_(ext_paratranz_main_dir_path, "utf8", "game", "localization", "gui"),
                    _(mod_loc_dir_path, "gui"))

    shutil.copytree(_(ext_paratranz_main_dir_path, "utf8", "game", "localization", "load_tips"),
                    _(mod_loc_dir_path, "load_tips"))

    # リソースから
    shutil.copytree(_(resource_dir_path, "game", "gui"),
                    mod_gui_dir_path)

    # SubModからファイルを移す
    shutil.move(_(ext_paratranz_main_dir_path,
                  "utf8", "game", "localization", "english", "god_names_l_english.yml"),
                _(mod_loc_dir_path, "english", "god_names_l_english.yml"))
    shutil.move(_(ext_paratranz_main_dir_path,
                  "utf8", "game", "localization", "english", "wonders_l_english.yml"),
                _(mod_loc_dir_path, "english", "wonders_l_english.yml"))

    return mod_dir_path


def generate_dot_mod_file(mod_title_name,
                          mod_dir_name,
                          mod_tags,
                          mod_image_file_path,
                          mod_supported_version,
                          out_dir_path):
    """
    .modファイルを作る
    :param mod_title_name:
    :param mod_dir_name: ディレクトリの名前
    :param mod_tags: Set<String>型
    :param mod_image_file_path:
    :param mod_supported_version:
    :param out_dir_path: 出力ディレクトリのパス
    :return: 出力ファイルパス
    """

    os.makedirs(out_dir_path, exist_ok=True)

    out_file_path = _(out_dir_path, "{}.mod".format(mod_dir_name))

    with open(out_file_path, "w", encoding="utf-8") as fw:
        lines = [
            'name="{}"'.format(mod_title_name),
            'path="mod/{}"'.format(mod_dir_name),
            'tags={}'.format("{" + " ".join(map(lambda c: '"{}"'.format(c), mod_tags)) + "}"),
            'supported_version="{}"'.format(mod_supported_version),
            'picture="{}"'.format(mod_image_file_path)
        ]

        fw.write("\n".join(lines))

    return out_file_path


def generate_distribution_file(url,
                               mod_file_path,
                               out_file_path):
    """
    trielaで使用する配布用設定ファイルを作成する。
    :param url:
    :param mod_file_path:
    :param out_file_path:
    :return:
    """

    with open(mod_file_path, 'rb') as fr:
        md5 = hashlib.md5(fr.read()).hexdigest()

    d_new = {'file_md5': md5,
             'url': url,
             'file_size': os.path.getsize(mod_file_path)}

    with open(out_file_path, "w", encoding="utf-8") as fw:
        json.dump(d_new, fw, indent=2, ensure_ascii=False)


def upload_mod_to_s3(upload_dir_path,
                     name,
                     bucket_name,
                     access_key,
                     secret_access_key,
                     region):
    """
    S3にファイルをアップロードする
    :param upload_dir_path:
    :param name:
    :param bucket_name:
    :param access_key:
    :param secret_access_key:
    :param region:
    :return: CDNのURL
    """

    # ディレクトリをzip圧縮する
    out_zip_path = _(".", "tmp", "out.zip")
    tmp_zip_file_path = _(".", "tmp", "out")
    shutil.make_archive(tmp_zip_file_path, 'zip', root_dir=upload_dir_path)

    # セッション確立
    session = Session(aws_access_key_id=access_key,
                      aws_secret_access_key=secret_access_key,
                      region_name=region)

    s3 = session.resource('s3')
    s3.Bucket(bucket_name).upload_file(out_zip_path, name)

    return "{}/{}".format("https://d3fxmsw7mhzbqi.cloudfront.net", name), out_zip_path


def main():
    # 一時フォルダ用意
    os.makedirs(_(".", "tmp"), exist_ok=True)
    os.makedirs(_(".", "out"), exist_ok=True)
    out_dir_path = _(".", "out")

    # main name
    mod_file_name = "japanese"

    # 翻訳の最新版をダウンロードする project_id=335はI:R JPのプロジェクトID
    p_file_main_path = download_trans_zip_from_paratranz(
        project_id=335,
        secret=os.environ.get("PARATRANZ_SECRET"),
        out_file_path=_(".", "tmp", "paratranz_main.zip"))

    print("p_file_main_path:{}".format(p_file_main_path))

    # 翻訳の最新版をダウンロードする project_id=350はI:R JPのプロジェクトID
    p_file_sub_path = download_trans_zip_from_paratranz(
        project_id=350,
        secret=os.environ.get("PARATRANZ_SECRET"),
        out_file_path=_(".", "tmp", "paratranz_sub.zip"))

    print("p_file_sub_path:{}".format(p_file_sub_path))

    # Modを構築する（フォルダのまま）
    assembly_mod(
        mod_file_name=mod_file_name,
        resource_paratranz_main_zip_file_path=p_file_main_path,
        resource_paratranz_sub_zip_file_path=p_file_sub_path,
        resource_dir_path=_(".", "resource"),
        out_dir_path=out_dir_path)

    print("mod_dir_path:{}".format(out_dir_path))

    # .modファイルを作成する
    generate_dot_mod_file(
        mod_title_name="Japanese Language Mod",
        mod_dir_name=mod_file_name,
        mod_tags={"Translation", "Localisation"},
        mod_image_file_path="title.jpg",
        mod_supported_version="1.0.*",
        out_dir_path=out_dir_path)

    return;

    print("generate .mod file")

    # S3にアップロード from datetime import datetime as dt
    from datetime import datetime as dt
    cdn_url, mod_pack_file_path = upload_mod_to_s3(
        upload_dir_path=out_dir_path,
        name=dt.now().strftime('%Y-%m-%d_%H-%M-%S-{}.zip'.format("ir-ap1")),
        bucket_name="triela-file",
        access_key=os.environ.get("AWS_S3_ACCESS_KEY"),
        secret_access_key=os.environ.get("AWS_S3_SECRET_ACCESS_KEY"),
        region="ap-northeast-1")

    print("cdn_url:{}".format(cdn_url))

    # distributionファイルを生成する
    generate_distribution_file(url=cdn_url,
                               out_file_path=_(".", "out", "dist.v2.json"),
                               mod_file_path=mod_pack_file_path)


if __name__ == "__main__":
    main()
