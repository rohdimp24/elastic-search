POST my_library
{
  "settings": {
    "analysis": {
      "analyzer": {
        "standard_clone": {
          "tokenizer": "standard",
          "filter": [
            "standard",
            "lowercase",
            "stop"]}}}}}