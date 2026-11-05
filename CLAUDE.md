# Notes for working on this repo

- Lens is a Varaxis product. Varaxis aims for national and international reach: do not tie the product,
  its copy, placeholders or docs to one town or region (e.g. Krishnanagar). Real client data under
  `clients/` may name its own city; product-level text should stay location-neutral.
- Commits and pushes go out as realishaanseal <ishaanseal@gmail.com>. No Claude attribution, co-author
  lines or session links in commits, PRs or code. Use plain branch names (no `claude/` prefix).
  Commit and push only; the owner opens and merges PRs.
- UI style: restrained and professional (neutral palette, hairlines, no gradients, emoji or decorative
  animation). Shared styles and components live in `ui/theme.py`.
- Hosting target is Streamlit Community Cloud (not Vercel). `LENS_PASSWORD` turns on the password screen.
- Sample clients in `clients/` are fictional and location-neutral in tone (different cities, English by default).
  Question languages are per client (`languages`); regional ones are opt-in.
- Brand: Lens's logo is in `brand/masters`, built by `brand/tools` on the Varaxis brand system (ink #0B1118,
  Lens amber #C9761A, Montserrat wordmark, "BY VARAXIS" endorsement). Never redraw it by hand: change
  `brand/tools/lens_geometry.py`, regenerate, and copy the app files into `ui/assets` (see brand/README.md).
