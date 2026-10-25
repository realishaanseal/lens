from lens.providers import parse_gemini, parse_openai, parse_perplexity


def test_parse_openai_responses():
    data = {"model": "gpt-x", "output": [
        {"type": "web_search_call"},
        {"type": "message", "content": [{"type": "output_text", "text": "Try SSHRI Hospital.",
                                         "annotations": [{"url": "https://a"}, {"url": "https://a"}]}]}]}
    a = parse_openai(data, "fallback")
    assert a.text == "Try SSHRI Hospital." and a.model == "gpt-x" and a.citations == ["https://a"]


def test_parse_gemini():
    data = {"modelVersion": "gemini-x", "candidates": [{
        "content": {"parts": [{"text": "Hello "}, {"text": "world"}]},
        "groundingMetadata": {"groundingChunks": [{"web": {"uri": "https://b"}}]}}]}
    a = parse_gemini(data, "fallback")
    assert a.text == "Hello world" and a.citations == ["https://b"]


def test_parse_perplexity():
    data = {"model": "sonar", "choices": [{"message": {"content": "Hi"}}], "citations": ["https://c"]}
    a = parse_perplexity(data, "fallback")
    assert a.text == "Hi" and a.citations == ["https://c"]
