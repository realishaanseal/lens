from lens.prompts import build_prompts, prompt_id


def test_expands_services_and_languages(client):
    prompts = build_prompts(client)
    langs = {p.language for p in prompts}
    assert {"en", "bn", "banglish"} <= langs
    assert any("কিডনি" in p.text for p in prompts)
    assert any(p.service == "Cardiology" for p in prompts)


def test_cap_keeps_language_mix(client):
    client.max_prompts = 6
    prompts = build_prompts(client)
    assert len(prompts) == 6
    assert len({p.language for p in prompts}) >= 2


def test_extra_prompts_come_first_and_ids_are_stable(client):
    client.extra_prompts = ["Best kidney doctor in Krishnanagar?"]
    first = build_prompts(client)[0]
    assert first.language == "custom"
    assert first.id == prompt_id("best kidney doctor in krishnanagar?  ")
