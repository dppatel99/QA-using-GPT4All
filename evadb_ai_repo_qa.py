import os
from time import perf_counter

from gpt4all import GPT4All
from unidecode import unidecode
from util import download_repo_content, read_repo_text_line
import sys
import evadb

def ask_question(notes_path: str, model, question):
    # Initialize early to exclude download time.

    llm = GPT4All(model)
    path = os.path.dirname(os.getcwd())
    cursor = evadb.connect().cursor()

    notes_table = "TablePPText"
    notes_feat_table = "FeatTablePPText"
    index_table = "IndexTable"

    timestamps = {}
    t_i = 0

    timestamps[t_i] = perf_counter()
    print("Setup Function")

    Text_feat_function_query = f"""CREATE UDF IF NOT EXISTS SentenceFeatureExtractor
            IMPL  './sentence_feature_extractor.py';
            """

    cursor.query("DROP UDF IF EXISTS SentenceFeatureExtractor;").execute()
    cursor.query(Text_feat_function_query).execute()

    cursor.query("DROP UDF IF EXISTS Similarity;").execute()
    Similarity_function_query = """CREATE UDF Similarity
                    INPUT (Frame_Array_Open NDARRAY UINT8(3, ANYDIM, ANYDIM),
                           Frame_Array_Base NDARRAY UINT8(3, ANYDIM, ANYDIM),
                           Feature_Extractor_Name TEXT(100))
                    OUTPUT (distance FLOAT(32, 7))
                    TYPE NdarrayFunction
                    IMPL './similarity.py'"""
    
    cursor.query(Similarity_function_query).execute()

    cursor.query(f"DROP TABLE IF EXISTS {notes_table};").execute()
    cursor.query(f"DROP TABLE IF EXISTS {notes_feat_table};").execute()

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("Create table")

    cursor.query(f"CREATE TABLE {notes_table} (id INTEGER, data TEXT(1000));").execute()

    # Insert text chunk by chunk.
    for i, text in enumerate(read_repo_text_line(notes_path)):
        print("text: --" + text + "--")
        ascii_text = unidecode(text)
        cursor.query(
            f"""INSERT INTO {notes_table} (id, data)
                VALUES ({i}, '{ascii_text}');"""
        ).execute()

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("Extract features")

    # Extract features from text.
    cursor.query(
        f"""CREATE TABLE {notes_feat_table} AS
        SELECT SentenceFeatureExtractor(data), data FROM {notes_table};"""
    ).execute()

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("Create index")

    # Create search index on extracted features.
    cursor.query(
        f"CREATE INDEX {index_table} ON {notes_feat_table} (features) USING QDRANT;"
    ).execute()

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("Query")

    # Search similar text as the asked question.
    ascii_question = unidecode(question)

    # Instead of passing all the information to the LLM, we extract the 5 topmost similar sentences
    # and use them as context for the LLM to answer.
    res_batch = cursor.query(
        f"""SELECT data FROM {notes_feat_table}
        ORDER BY Similarity(SentenceFeatureExtractor('{ascii_question}'),features)
        LIMIT 5;"""
    ).execute()

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("Merge")

    # Merge all context information.
    context_list = []
    for i in range(len(res_batch)):
        context_list.append(res_batch.frames[f"{notes_feat_table.lower()}.data"][i])
    context = "\n".join(context_list)

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("LLM")

    # LLM
    query = f"""If the context is not relevant, please answer the question by using your own knowledge about the topic.
    
    {context}
    
    Question : {question}"""

    full_response = llm.generate(query)

    print(full_response)

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print(f"Total Time: {(timestamps[t_i] - timestamps[0]) * 1000:.3f} ms")

def main():
    repo_content_path = download_repo_content()

    if len(sys.argv)!=3:
        print("pass sufficient args")
    ask_question(repo_content_path, sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
