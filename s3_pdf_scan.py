from filetype import filetype
import sys

import click
from commons import parse_aws_param, parse_bucket_key
import boto3, json
from botocore.config import Config
import fitz





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
        file_content = res["Body"].read(50)
        ext = filetype.guess_extension(file_content)
        print(f"{s3_pdf_path}.{ext}")
    except Exception as e:
        print(f"ERROR: {s3_pdf_path}, {e}", file=sys.stderr)


if __name__ == '__main__':
    main()
    
