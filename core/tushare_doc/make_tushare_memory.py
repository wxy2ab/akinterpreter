import json




from ..rag.memeory import Memory  # Assuming the Memory class is in a file named memory.py

def process_tushare_doc():
    # 1. Read the JSON file and generate the list
    with open('./json/tushare_docs.json', 'r', encoding='utf-8') as f:
        tushare_doc = json.load(f)

    doc_list = []
    for key, value in tushare_doc.items():
        description = value.split('\n')[0].replace('描述：', '').strip()
        doc_list.append(f"{key}:{description}")

    # 2. Save the list to Memory
    memory = Memory()
    memory.batch_save(doc_list)

    # 3. Save the Memory object to a new JSON file
    memory.save_to_file('./json/tushare_memory.json')

    print(f"Processed {len(doc_list)} items and saved to tushare_memory.json")

if __name__ == "__main__":
    process_tushare_doc()