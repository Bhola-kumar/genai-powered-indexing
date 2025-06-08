from .chapter_parser.chapter_parser import convert_chapters_to_single_json
from .chapter_parser.paragraph_json3 import full_metadata_to_paragraphs
from .index_parser.parse_index import build_index_terms
from .searching.index_searching2 import generate_search_report


# === CONFIGURATION ===
PATH_TO_LIBREOFFICE = r"C:\Users\bhola\Downloads\LibreOfficePortable\App\libreoffice\program\soffice.exe"
TEMPORARY_DIRECTORY = r"C:\Users\bhola\Desktop\ddmo\backend\temp"
AZURE_ENDPOINT = "https://llmfoundry.straive.com/azureformrecognizer/analyze"
AZURE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImJob2xhLmt1bWFyQHN0cmFpdmUuY29tIn0.jq66OE-OrTGreCoN6-ED8LqO5qVo0g4qRWm5S2SG8UE"
AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL = "prebuilt-document"

# def audit_index_document_for_given_chapter(CHAPTER_DOCUMENT_PATH,INDEX_DOCUMENT_PATH):
#     path_to_chapter_to_json_document = convert_chapter_to_json(CHAPTER_DOCUMENT_PATH,PATH_TO_LIBREOFFICE,TEMPORARY_DIRECTORY,AZURE_API_KEY,AZURE_ENDPOINT,AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL)
#     if(path_to_chapter_to_json_document == None):
#         return print("error in parsing the chapter itself.")
#     path_to_preprocessed_chapter_json = nested_json_to_paragraphs(path_to_chapter_to_json_document,TEMPORARY_DIRECTORY)
#     print(path_to_preprocessed_chapter_json)
#     path_to_preprocessed_index_json = build_index_terms(INDEX_DOCUMENT_PATH,TEMPORARY_DIRECTORY)
#     print(path_to_preprocessed_index_json)
#     path_to_audited_index_document_json = generate_search_report(path_to_preprocessed_chapter_json,path_to_preprocessed_index_json,TEMPORARY_DIRECTORY)
#     print(path_to_audited_index_document_json)
#     return path_to_audited_index_document_json



def audit_index_document_for_given_chapter(CHAPTER_DOCUMENT_LIST,INDEX_DOCUMENT_PATH):
    path_to_chapter_to_json_document = convert_chapters_to_single_json(CHAPTER_DOCUMENT_LIST,PATH_TO_LIBREOFFICE = PATH_TO_LIBREOFFICE,TEMPORARY_DIRECTORY = TEMPORARY_DIRECTORY,AZURE_API_KEY = AZURE_API_KEY,AZURE_ENDPOINT = AZURE_ENDPOINT,AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL = AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL)
    if(path_to_chapter_to_json_document == None):
        return print("error in parsing the chapter itself.")
    path_to_preprocessed_chapter_json = full_metadata_to_paragraphs(path_to_chapter_to_json_document,TEMPORARY_DIRECTORY)
    print(path_to_preprocessed_chapter_json)
    path_to_preprocessed_index_json = build_index_terms(INDEX_DOCUMENT_PATH,TEMPORARY_DIRECTORY)
    print(path_to_preprocessed_index_json)
    path_to_audited_index_document_json = generate_search_report(path_to_preprocessed_chapter_json,path_to_preprocessed_index_json,TEMPORARY_DIRECTORY)
    print(path_to_audited_index_document_json)
    return path_to_audited_index_document_json

if __name__ == "__main__":
    audit_index_document_for_given_chapter(
       [ r"C:\Users\bhola\Desktop\ddmo\input\manuscriptPdf\01744-ch0002_Release_2024_Jun-28-24-0931 - checked.pdf"],
        r"C:\Users\bhola\Desktop\ddmo\input\indexPage\1744r2024.docx"
    )