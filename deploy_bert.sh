docker run -p 8501:8501 \
  --mount type=bind,source=/Users/pkun/PycharmProjects/ui_api_automated_test/output_model/,target=/models/bert \
  -e MODEL_NAME=bert -t tensorflow/serving