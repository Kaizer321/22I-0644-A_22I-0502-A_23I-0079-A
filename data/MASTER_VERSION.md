# Master dataset version

- Release: `master_release_v1`, dated 2026-11-12 (from the dataset README)
- Contents: 75 groups, 3,622 cases (tier S 1,429, M 1,461, L 440, X 292)
- Location: `Master Dataset/archive/` (CSV tables, `CHECKSUMS.txt`, `README.md`)
- Not committed (see .gitignore)
- Our sample rule: s = 69, positions 6, 13, 20, ... (s mod 7 + 7k) in master file order of each tier
- Sample sizes from `sample()`: S 204, M 208, L 62, X 41

## SHA-256 (output of `verify_checksums()`, equals CHECKSUMS.txt)

| File | SHA-256 |
|---|---|
| cases.csv | `9cd8989098ccac9c16d4f8031217fd298f88b9ca6dbb8c473e4a4b4c906038c4` |
| claims.csv | `e27c6a547ef08540c7505cf2d83a6504dd7892b0ea0fe7065e35a1ff33cd417b` |
| crates.csv | `bfd3b9906dda0a2cf8ca86bf393def994ac711448cda4af10898010139cf0af5` |
| drum_prices.csv | `1a19567a1954e78953f6a8db054c68920fb865aaf5d0beb06e5dd2959ec16b78` |
| incidents.csv | `a7b54bb8e0788f62b8adac3016dc9c6145d90d6f77a0dfa7f6ac0d1202239f8a` |
| locations.csv | `cf31a489b612347488dc3228681bff78e9b8ebccad40c95fac3b9bf9e3b2b1db` |
| pipeline_dims.csv | `a77d0c6ded563d1de37ccaf46957ae3f8f10a83bb0f62d8166beabb7c2c7bf43` |
| radio_log.csv | `711e9a203f1f59ca68150c21aefeb8d0d72abf76a4d73a29d9f15a768418399b` |
| radio_patterns.csv | `5f932b9d3a26a66cf80dd07ddec88a4da02d9d52cbcc449622f1baae084c6695` |
| radio_reports.csv | `b1d15499ef0d2c4a37b96a17a159fd382da170857986448183ba836e89253cb6` |
| rations.csv | `5b9efc02e0a7fd837dc692e96292ec027dbe6fbd29fc2b25c1f8e23019642990` |
| roads.csv | `e4fd1f44e82624db8f9f9fca6174ab12e0c968b77cebb25a9485359923f4ee0e` |
| safety_planted.csv | `7c99286b9dcb18d91bd3eeda6ad9cdeb2c6d5fd7245c70deb2d77dfd8c3402ff` |
| safety_rules.csv | `b4bde6a7da3ed5238ab7497a8550b604d999c5e8b4768ca4a11905974a3aab50` |
| sensor_cover.csv | `d35a7048f38263ac3e033dc4b1af465a6a4ae9432f57f6e6cb9d0f7ee32a06be` |
| sensor_edges.csv | `618f2b1729d28fc1b0cc6be48f2751647a0b952824ac7c3c6f1cb78b827f6a11` |
| sites.csv | `10216b7a961677203f450739008bfeb88bfdddadc520f34205024c3258868377` |
| tour.csv | `800954977ad88aaea46436508b8fc6a5e661864e06006432eb80aee1a3ffdcd2` |
| waves.csv | `6f1eca9277b3e0f6d23f9a284dccc50cea471c731d2ddfdeca2c296cf2f47646` |
| windows.csv | `b39320b612279c1b3e09ac68a7191a12b33dadb0682135b72b3334bdcc24f935` |
