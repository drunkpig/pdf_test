"""
核心思想是接受一个pdf文件，判断其是否可提取，如果可提取则返回True，否则返回False
"""
import sys

import click
from commons import parse_aws_param, parse_bucket_key
import boto3, json
# from boto3.s3.transfer import TransferConfig
from botocore.config import Config
import fitz

# from PIL import Image
# import io

#
# def recoverpix(doc, item):
#     xref = item[0]  # xref of PDF image
#     smask = item[1]  # xref of its /SMask
#
#     # special case: /SMask or /Mask exists
#     if smask > 0:
#         pix0 = fitz.Pixmap(doc.extract_image(xref)["image"])
#         if pix0.alpha:  # catch irregular situation
#             pix0 = fitz.Pixmap(pix0, 0)  # remove alpha channel
#         mask = fitz.Pixmap(doc.extract_image(smask)["image"])
#
#         try:
#             pix = fitz.Pixmap(pix0, mask)
#         except:  # fallback to original base image in case of problems
#             pix = fitz.Pixmap(doc.extract_image(xref)["image"])
#
#         if pix0.n > 3:
#             ext = "pam"
#         else:
#             ext = "png"
#
#         return {  # create dictionary expected by caller
#             "ext": ext,
#             "colorspace": pix.colorspace.n,
#             "image": pix.tobytes(ext),
#         }
#
#     # special case: /ColorSpace definition exists
#     # to be sure, we convert these cases to RGB PNG images
#     if "/ColorSpace" in doc.xref_object(xref, compressed=True):
#         pix = fitz.Pixmap(doc, xref)
#         pix = fitz.Pixmap(fitz.csRGB, pix)
#         return {  # create dictionary expected by caller
#             "ext": "png",
#             "colorspace": 3,
#             "image": pix.tobytes("png"),
#         }
#     return doc.extract_image(xref)


# def get_image_dpi(image_bytes):
#     img = Image.open(io.BytesIO(image_bytes))
#     # 获取图片的dpi
#     dpi = img.info.get('dpi')
#     return dpi
#
#
# dimlimit = 200  # minimum dimension of a picture in pixels
# abssize = 10000  # minimum size of a picture in bytes
# relsize = 0.01  # minimum size of a picture relative to page area
#
#
# def _get_image_area(doc: fitz.Document, img_area_ratio: float) -> list:
#     """
#     :param page: fitz.Page
#     :param img_area_ratio: 图片面积占比
#     :return:
#     """
#     result = []
#
#     xreflist = []
#     imglist = []
#     for pno in range(len(doc)):
#         page_result = []
#         result.append(page_result)
#         il = doc.get_page_images(pno)
#         imglist.extend([x[0] for x in il])
#         for img in il:
#             xref = img[0]
#             if xref in xreflist:
#                 continue
#             width = img[2]
#             height = img[3]
#             if min(width, height) <= dimlimit:
#                 continue
#             image = recoverpix(doc, img)
#             n = image["colorspace"]
#             imgdata = image["image"]
#
#             if len(imgdata) <= abssize:
#                 continue
#             if len(imgdata) / (width * height * n) <= relsize:
#                 continue
#
#             dpi = get_image_dpi(imgdata)
#             page_result.append((width / dpi[0], height / dpi[1]))  # 把获取到的图片信息放入到page_result中, 单位是英寸inch
#             xreflist.append(xref)
#
#     return result


def get_image_info(doc: fitz.Document) -> list:
    result = []
    for page in doc:
        page_result = []
        result.append(page_result)
        il = page.get_image_info()
        for img in il:
            # color_space = img['colorspace']
            # if color_space == 0:
            #     continue
            width = img['width']
            height = img['height']
            dpi_x, dpi_y = img['xres'], img['yres']
            page_result.append((width // dpi_x, height // dpi_y))

    return result


def get_pdf_page_size_inch(doc):
    page_cnt = len(doc)
    l = min(page_cnt, 5)
    # 取页面最大的宽和高度
    page_width_inch = 0
    page_height_inch = 0
    for i in range(l):
        page = doc[i]
        page_rect = page.rect
        page_width_pts, page_height_pts = page_rect.width, page_rect.height
        page_width_inch, page_height_inch = page_width_pts // 72, page_height_pts // 72

    return page_width_inch, page_height_inch

def pdf_extractable_classfier(s3_pdf_path:str, pdf_bytes: bytes):
    """
    :param pdf_bytes: pdf文件的二进制数据
    几个维度来评价：是否加密，是否需要密码，纸张大小，总页数，是否文字可提取
    """
    doc = fitz.open("pdf", pdf_bytes)
    is_needs_password = doc.needs_pass
    is_encrypted = doc.is_encrypted
    total_page = len(doc)
    page_width_inch, page_height_inch = get_pdf_page_size_inch(doc)
    image_area_pix_every_page = get_image_info(doc)

    # 最后输出一条json
    res = {
        "pdf_path": s3_pdf_path,
        "is_needs_password": is_needs_password,
        "is_encrypted": is_encrypted,
        "total_page": total_page,
        "page_width_inch": int(page_width_inch),
        "page_height_inch": int(page_height_inch),
        "image_area_pix_every_page": image_area_pix_every_page,
        "metadata":doc.metadata
    }
    print(json.dumps(res, ensure_ascii=False))


@click.command()
@click.option('--s3-pdf-path', help='s3上pdf文件的路径')
@click.option('--s3-profile', help='s3上的profile')
def main(s3_pdf_path: str, s3_profile: str):
    """
    :param s3_pdf_path: s3上pdf文件的路径
    :param img_area_ratio: 图片面积占比
    :param img_page_ratio: 图片页数占比
    """
    try:
        ak, sk, end_point, addressing_style = parse_aws_param(s3_profile)
        cli = boto3.client(service_name="s3", aws_access_key_id=ak, aws_secret_access_key=sk, endpoint_url=end_point,
                           config=Config(s3={'addressing_style': addressing_style}))
        bucket_name, bucket_key = parse_bucket_key(s3_pdf_path)
        res = cli.get_object(Bucket=bucket_name, Key=bucket_key)
        file_content = res["Body"].read()
        pdf_extractable_classfier(s3_pdf_path, file_content)
    except Exception as e:
        print(f"ERROR: {s3_pdf_path}, {e}", file=sys.stderr)


if __name__ == '__main__':
    main()
