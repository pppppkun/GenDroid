import os
from run_classifier import DataProcessor, InputExample
import tokenization

class MyTaskProcessor(DataProcessor):
    """Processor for the News data set (GLUE version)."""

    def __init__(self):
        self.labels = ['yes', 'no']
        #self.labels = ['game', 'technology']

    def get_train_examples(self, data_dir):
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "input.tsv")), "train")

    def get_dev_examples(self, data_dir):
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "output.tsv")), "dev")

    def get_test_examples(self, data_dir):
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "output.tsv")), "test")

    def get_labels(self):
        return self.labels

    def _create_examples(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        examples = []
        for (i, line) in enumerate(lines):
            if line==[]:continue
            if len(line)==1:
                print(line[0])
                #exit()

            guid = "%s-%s" % (set_type, i)
            text_a = tokenization.convert_to_unicode(line[1].replace("_"," "))
            text_b = tokenization.convert_to_unicode(line[2])
            label = tokenization.convert_to_unicode(line[0])
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))

        return examples

if __name__ == "__main__":
    print(1)
