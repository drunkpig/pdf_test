import os.path

import fitz  # PyMuPDF
import json


def get_info(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf = fitz.open(file)
        info = pdf.metadata
        info = json.dumps(info, ensure_ascii=False)
        info = json.loads(info)
        info['_pdf_file'] = pdf_path
        print(json.dumps(info, indent=1, ensure_ascii=False))
        return info


def scan_pdf_in_a_dir(dir_name: str):
    import os
    pdf_files = [f for f in os.listdir(dir_name) if f.endswith('.pdf')]
    return pdf_files


if __name__ == '__main__':
    path = 'D:\pdf_files\mass'
    all_pdf_files = scan_pdf_in_a_dir(path)
    for pdf_file in all_pdf_files:
        info = get_info(os.path.join(path, pdf_file))# TODO

