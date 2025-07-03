from docx import Document
import json
import re
from datetime import datetime

def auto_chunk_docx(docx_path, output_json):
    doc = Document(docx_path)
    chunks = []
    current_section = ""
    current_subsection = ""
    current_item = ""
    chunk_text = []
    chunk_id = 1

    pattern_section = re.compile(r"^[IVXLCDM]+\.\s")
    pattern_subsection = re.compile(r"^\d+\.\s")
    pattern_item = re.compile(r"^[a-z]\.\s")
    pattern_bullet = re.compile(r"^[-*•]\s?")

    def flush_chunk():
        nonlocal chunk_id
        if chunk_text:
            text = " ".join(chunk_text).strip()
            if text:
                chunks.append({
                    "text": text,
                    "metadata": {
                        "section": current_section if current_section else None,
                        "subsection": current_subsection if current_subsection else None,
                        "item": current_item if current_item else None,
                        "source": "nội quy",
                        "updated_at": datetime.now().strftime("%Y-%m-%d"),
                        "id": f"chunk_{chunk_id}"
                    }
                })
                chunk_id += 1
        chunk_text.clear()

    # Thêm hàm lưu lại heading khi chuyển context
    def save_heading_chunk(text, section, subsection, item):
        nonlocal chunk_id
        if text and not any(x in text for x in ["...", "___", "—"]):
            chunks.append({
                "text": text,
                "metadata": {
                    "section": section if section else None,
                    "subsection": subsection if subsection else None,
                    "item": item if item else None,
                    "source": "nội quy",
                    "updated_at": datetime.now().strftime("%Y-%m-%d"),
                    "id": f"chunk_{chunk_id}"
                }
            })
            chunk_id += 1

    for para in doc.paragraphs:
        line = para.text.strip()
        if not line:
            continue

        # Section (heading mới)
        if pattern_section.match(line):
            flush_chunk()
            # Trước khi đổi section, lưu section cũ nếu chỉ là heading
            if (current_section and not current_subsection and not current_item):
                save_heading_chunk(current_section, current_section, None, None)
            current_section = line
            current_subsection = ""
            current_item = ""
            continue

        # Subsection
        if pattern_subsection.match(line):
            flush_chunk()
            if (current_subsection and not current_item):
                save_heading_chunk(current_subsection, current_section, current_subsection, None)
            current_subsection = line
            current_item = ""
            continue

        # Item
        if pattern_item.match(line):
            flush_chunk()
            if current_item:
                save_heading_chunk(current_item, current_section, current_subsection, current_item)
            current_item = line
            continue

        # Bullet
        if pattern_bullet.match(line):
            flush_chunk()
            text_clean = pattern_bullet.sub("", line)
            chunk_text.append(text_clean)
            flush_chunk()
            continue

       
        chunk_text.append(line)

    # Flush cuối cùng
    flush_chunk()
    # Lưu heading cuối nếu chưa từng có nội dung
    if current_section and not current_subsection and not current_item:
        save_heading_chunk(current_section, current_section, None, None)
    if current_subsection and not current_item:
        save_heading_chunk(current_subsection, current_section, current_subsection, None)
    if current_item:
        save_heading_chunk(current_item, current_section, current_subsection, current_item)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo {len(chunks)} chunk và lưu vào {output_json}")
def main():
 
    # input_docx = "data/raw/Noiquyhocsinh_NH_24_25_2.docx"
    # output_chunkjson = "data/processed/noiquy_chunks_rag.json"
    # if os.path.exists(input_docx):
    #     try:
    #         os.makedirs(os.path.dirname(output_chunkjson), exist_ok=True)
    #         sections = parse_noiquy_docx(input_docx)
    #         chunks = structured_to_chunks(sections, chunk_size=350, chunk_overlap=50)
    #         with open(output_chunkjson, "w", encoding="utf-8") as f:
    #             json.dump(chunks, f, ensure_ascii=False, indent=2)
    #         logging.info(f"Đã tạo {len(chunks)} chunks và lưu vào {output_chunkjson}")
    #         print(f"Đã lưu file chunk cho RAG tại: {output_chunkjson}")
    #     except Exception as e:
    #         print(f" Lỗi nội quy: {str(e)}")


   input_docx = "data/raw/Noiquyhocsinh_NH_24_25_2.docx"
   output_chunkjson = "data/processed/noiquy_chunks_rag.json"
   auto_chunk_docx(input_docx, output_chunkjson)

if __name__ == "__main__":
    main()
 
