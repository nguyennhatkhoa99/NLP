from datasets import load_dataset
from transformers import AutoTokenizer
from transformers import DebertaV2Config, DebertaV2Model
from transformers import DefaultDataCollator


def load_dataset(dataset_name, split_ratio):
    dataset = load_dataset(dataset_name, split="train[:5000]")
    X_train, Y_train, X_test, Y_test = dataset.train_test_split(test_size=split_ratio)
    return dataset, X_train, Y_train, X_test, Y_test


def load_tokenizer(model_version):
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    return tokenizer

def dataset_tokenizer(dataset):
    tokenized_squad = dataset.map(preprocess_function, batched=True, remove_columns=squad["train"].column_names)
    return tokenized_squad

def preprocess_function(tokenizer, examples):
    questions = [q.strip() for q in examples["question"]]
    inputs = tokenizer(
        questions,
        examples["context"],
        max_length=384,
        truncation="only_second",
        return_offsets_mapping=True,
        padding="max_length",
    )

    offset_mapping = inputs.pop("offset_mapping")
    answers = examples["answers"]
    start_positions = []
    end_positions = []

    for i, offset in enumerate(offset_mapping):
        answer = answers[i]
        start_char = answer["answer_start"][0]
        end_char = answer["answer_start"][0] + len(answer["text"][0])
        sequence_ids = inputs.sequence_ids(i)

        # Find the start and end of the context
        idx = 0
        while sequence_ids[idx] != 1:
            idx += 1
        context_start = idx
        while sequence_ids[idx] == 1:
            idx += 1
        context_end = idx - 1

        # If the answer is not fully inside the context, label it (0, 0)
        if offset[context_start][0] > end_char or offset[context_end][1] < start_char:
            start_positions.append(0)
            end_positions.append(0)
        else:
            # Otherwise it's the start and end token positions
            idx = context_start
            while idx <= context_end and offset[idx][0] <= start_char:
                idx += 1
            start_positions.append(idx - 1)

            idx = context_end
            while idx >= context_start and offset[idx][1] >= end_char:
                idx -= 1
            end_positions.append(idx + 1)

    inputs["start_positions"] = start_positions
    inputs["end_positions"] = end_positions
    return inputs