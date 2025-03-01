import pandas as pd
from hypothesis import example, given, strategies
from hypothesis.extra.pandas import column, data_frames

from datto.CleanText import CleanText


ct = CleanText()

df = pd.DataFrame(
    [
        ["some text", 1, 1.2],
        ["some other text", 1, 1.4],
        ["i like bananas", 2, 6.5],
        ["i like apples", 2, 7.5],
        ["some text", 1, 1.2],
        ["some other text", 1, 1.4],
        ["i like bananas", 2, 6.5],
        ["i like apples", 2, 7.5],
        ["some text", 1, 1.2],
        ["some other text", 1, 1.4],
        ["i like bananas", 2, 6.5],
        ["i like apples", 2, 7.5],
    ],
    columns=["text", "int", "float"],
)


def replace_text_test(df):
    df["text"] = df["text"].apply(lambda x: x.replace("i like", "i love"))
    return df


def test_remove_names():
    text = "Hello John, how are you doing?"
    cleaned_text = ct.remove_names(text)
    assert "John" not in cleaned_text


@given(strategies.text())
@example("Here's a link: www.google.com Thanks!")
def test_remove_links(text):
    cleaned_text = ct.remove_links(text)
    assert ".com" not in cleaned_text


@given(strategies.text())
@example("I went running today.")
def test_lematize(text):
    spacy_tokens = ct.lematize(text)
    assert "ing " not in spacy_tokens


@given(strategies.text())
@example(
    """
    Hello Jane,

    My name is Kristie. I have a question for you.

    Thanks for your help,

    Kristie
    Head of PR at FakeCompany
    """
)
def test_remove_email_greetings_signatures(text):
    cleaned_body = ct.remove_email_greetings_signatures(text)
    assert "Hello" not in cleaned_body


@given(data_frames(columns=[column(dtype=str), column(dtype=int), column(dtype=bool),]))
@example(pd.DataFrame([["Kristie", "Smith"]], columns=["First Name", "Last Name"]))
def test_clean_column_names(df):
    cleaned_df = ct.clean_column_names(df)
    assert " " not in cleaned_df.columns


@given(data_frames(columns=[column(dtype=str), column(dtype=int), column(dtype=bool),]))
@example(
    pd.DataFrame(
        [["Kristie", "Smith", "Smith"]],
        columns=["First Name", "Last Name", "Last Name"],
    )
)
def test_remove_duplicate_columns(df):
    cleaned_df = ct.remove_duplicate_columns(df)
    assert cleaned_df.shape[1] <= df.shape[1]


@given(
    data_frames(
        columns=[
            column(name="to_number", dtype=str),
            column(name="to_datetime", dtype=str),
            column(name="to_str", dtype=int),
        ]
    )
)
@example(
    pd.DataFrame(
        [["12432", "2012-01-02", 14324]], columns=["to_number", "to_datetime", "to_str"]
    )
)
def test_fix_col_data_type(df):
    df = ct.fix_col_data_type(df, "to_number", "int")
    df = ct.fix_col_data_type(df, "to_datetime", "datetime")
    df = ct.fix_col_data_type(df, "to_str", "str")

    assert df.to_number.dtype == "int64" or df.to_number.dtype == "float64"
    assert df.to_datetime.dtype == "<M8[ns]"
    assert df.to_str.dtype == "O"


def test_compress_df():
    compressed_df = ct.compress_df(df)
    assert compressed_df["int"].dtype == "uint8"
    assert compressed_df["float"].dtype == "float32"
    assert compressed_df["text"].dtype == "category"


def test_make_uuid():
    id = "609390d88cff44269c2e293bd6b89a0b"
    uuid = ct.make_uuid(id)
    assert uuid == "609390d8-8cff-4426-9c2e-293bd6b89a0b"


def test_most_common_only():
    col = "text"
    num = 1

    df_cleaned = ct.df_most_common_only(df, col, num)
    assert df_cleaned.shape[0] < df.shape[0]


def test_batch_pandas_operation():
    num_splits = 2
    identifier_col = "int"
    new_df = ct.batch_pandas_operation(
        df, num_splits, identifier_col, replace_text_test
    )
    assert not new_df["text"].apply(lambda x: "i like" in x).max()


def test_batch_merge_operation():
    df_1 = df.copy()
    df_2 = df.copy()
    num_splits = 2
    identifier_col = "int"
    merge_col = "int"
    merged_df = ct.batch_merge_operation(
        df_1, df_2, num_splits, identifier_col, merge_col
    )
    assert merged_df.shape[1] == 5
