from pathlib import Path
from rules.rules_checker import main 

if __name__ == "__main__":
    main(document_path=Path("data/test_doc.txt"))
