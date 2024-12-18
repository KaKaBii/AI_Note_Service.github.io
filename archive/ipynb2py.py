import os
import nbformat
from nbconvert import PythonExporter

def convert_ipynb_to_py(ipynb_path, py_path):
    # 檢查檔案是否存在
    if not os.path.exists(ipynb_path):
        print(f"檔案不存在：{os.path.abspath(ipynb_path)}")
        return
    
    try:
        # 讀取 .ipynb 檔案
        with open(ipynb_path, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)

        # 轉換為 Python 程式碼
        python_exporter = PythonExporter()
        python_code, _ = python_exporter.from_notebook_node(notebook)

        # 移除 `# In[...]` 或類似註解
        filtered_code = '\n'.join(
            line for line in python_code.splitlines()
            if not line.strip().startswith('# In[')
        )

        # 寫入 .py 檔案
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(filtered_code)
        print(f"轉換完成：{os.path.abspath(py_path)}")

    except Exception as e:
        print(f"轉換過程中發生錯誤：{e}")
        
# 使用範例
convert_ipynb_to_py('./APP1/Flask.ipynb', './APP1/Flask.py')
