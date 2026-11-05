# Demo video

Records a narrated walkthrough of Lens (about 2 minutes 10 seconds) and builds everything needed for a voice-over:

| File | What it is |
|---|---|
| `lens-demo.mp4` | clean 1920×1080 video |
| `lens-demo-captioned.mp4` | the same with the narration as subtitles, to rehearse against |
| `lens-demo.srt` | narration as subtitles, timed to the video |
| `lens-demo-script.md` | the voice-over script: timestamps, what is on screen, what to say |

Each scene lasts at least as long as its narration takes to read (2.5 words a second), and the real scene times are logged during recording, so the script always matches the video. Numbers in the narration (mention rate, change, top competitor, website score) are read off the screen while recording.

## Recording it again

Needs Playwright with Chromium and ffmpeg. From the repo root:

```bash
D=/tmp/lens-demo && rm -rf $D && mkdir -p $D
git archive HEAD | tar -x -C $D --one-top-level=app
sed -i 's#^website: https://example.com#website: http://meridianhospital.example#' $D/app/clients/meridian-hospital.yaml
echo "127.0.0.1 meridianhospital.example" | sudo tee -a /etc/hosts       # the stand-in client website
(cd demo/site && sudo python -m http.server 80 --bind 127.0.0.1 &)
(cd $D/app && LENS_DB=$D/demo.db python -c "from lens.config import load_client; from lens.store import Store; from lens.runner import seed_demo; seed_demo(load_client('clients/meridian-hospital.yaml'), Store(), months=4, end_period='2026-10')")
(cd $D/app && LENS_PASSWORD=demo-lens LENS_MOCK_DELAY=0.5 LENS_MOCK_RATE=0.62 LENS_DB=$D/demo.db streamlit run app.py --server.headless true --server.port 8620 &)
node demo/record_demo.js http://localhost:8620 $D/out
python demo/build_outputs.py $D/out
```

- `demo/site/` is a stand-in website for the sample hospital, with a realistic mix: business schema and a sitemap, but robots.txt blocks GPTBot and two service pages are missing.
- Sample history ends the month before the recording, so the live "Run check" adds the current month to the trend.
- `LENS_MOCK_DELAY` paces sample answers so the status lines are readable; `LENS_MOCK_RATE` sets how often sample answers name the client. Both only affect sample answers.
- Change the narration in `record_demo.js` (each `scene(...)`); `{name}` placeholders are filled from the screen.

## Voice-over (ElevenLabs)

`voiceover.py` voices the script with an ElevenLabs voice and lays it onto the video. The API key is read from `XI_API_KEY` and never stored. For the best sync, voice first and record to the voice:

```bash
XI_API_KEY=... python demo/voiceover.py $D/out NvA7c85NkZVpFBAHHQQ3 --clips-only   # clips + voice/durations.json
SCENE_SECONDS=$D/out/voice/durations.json node demo/record_demo.js http://localhost:8620 $D/out2
cp -r $D/out/voice $D/out2/ && python demo/build_outputs.py $D/out2
XI_API_KEY=... python demo/voiceover.py $D/out2                                     # lens-demo-voiced.mp4
```

Delivery uses `eleven_multilingual_v2` with settings tuned for a natural read (stability 0.38, style 0.32), and each clip is generated with the lines around it so the voice carries across scenes.
