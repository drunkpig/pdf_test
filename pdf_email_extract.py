import sys
import re
import click
from commons import parse_aws_param, parse_bucket_key
import boto3, json
# from boto3.s3.transfer import TransferConfig
from botocore.config import Config
import fitz

def extract_emails(text):
    email_list = []
    # 匹配普通电子邮件
    pattern_normal = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    matches_normal = re.findall(pattern_normal, text)
    email_list.extend(matches_normal)

    # 匹配上述形式的电子邮件
    pattern_special = r'{([^}]*)}@([A-Za-z0-9.-]+\.[A-Za-z]{2,6})'
    matches_special = re.findall(pattern_special, text)
    
    for match in matches_special:
        names = re.split(';|,', match[0])
        domain = match[1]
        
        for name in names:
            email_list.append(f'{name}@{domain}')
    
    return email_list

def extract_pdf_email(s3_path, pdf_file_content):
    # 读取PDF文件
    doc = fitz.open(stream=pdf_file_content, filetype="pdf")
    # 获取PDF文件的页数
    first_page = doc[0]
    # 解析其中的文字
    text = first_page.get_text()
    
    emails = extract_emails(text)
    if len(emails)>0:
        emails = [e.strip() for e in emails]
        print('\n'.join(emails))
    
    return 0

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
        extract_pdf_email(s3_pdf_path, file_content)
    except Exception as e:
        print(f"ERROR: {s3_pdf_path}, {e}", file=sys.stderr)


if __name__ == '__main__':
    main()
