"""
分类条件：
1. 页面大小不一致，波动
2. 图片占比太大
3. 文字过于稀疏，比如ppt
4. 图片大小都基本一样，也就是方差很小：具体做法是每一page最大图片的方差小于1.5个标准差。
"""
import click
import json
import sys
from loguru import logger

def classify_by_area(page_width, page_height, img_sz_list):
    total_pg = len(img_sz_list)
    img_page_cnt = 0
    for img_sz in img_sz_list:
        for w, h in img_sz:
            if w * h > page_width * page_height * 0.8:
                img_page_cnt += 1
                break
    if total_pg==0 or img_page_cnt / total_pg > 0.8:
        return 0
    else:
        return 1


@click.command()
@click.option("--json_file", type=str, help="pdf信息")
def main(json_file):
    if json_file is None:
        print("json_file is None", file=sys.stderr)
        exit(0)
    try:
        with open(json_file, "r") as f:
            for l in f:
                if l.strip() == "":
                    continue
                o = json.loads(l)
                page_width = o["page_width_inch"]
                page_height = o["page_height_inch"]
                img_sz_list = o["image_area_pix_every_page"]
                tag = classify_by_area(page_width, page_height, img_sz_list)
                o['is_text_pdf'] = tag
                print(json.dumps(o, ensure_ascii=False))
    except Exception as e:
        print("ERROR: ", e, file=sys.stderr)


if __name__ == "__main__":
    main()
