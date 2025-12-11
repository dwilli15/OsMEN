---
language:
- ru
size_categories:
- 10K<n<100K
dataset_info:
  features:
  - name: audio
    dtype: audio
  - name: id
    dtype: string
  - name: label
    dtype:
      class_label:
        names:
          '0': Мужской
          '1': Женский
  splits:
  - name: train
    num_bytes: 2283481092.048
    num_examples: 13936
  - name: test
    num_bytes: 565904905.76
    num_examples: 3413
  download_size: 2114690824
  dataset_size: 2849385997.8079996
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: test
    path: data/test-*
---
