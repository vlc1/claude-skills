# Display equations of the deck: id -> LaTeX (display style); scale in px per TeX pt (build.py default 4.4).
# Colours: \cb bleu, \crs rose, \cv vert, \cvi violet; default ink is noir.

EQS = {
    "cont_c": r"\frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \mathbf{u}) = 0",
    "cont_nc": r"\frac{D\rho}{Dt} + \rho \, \nabla \cdot \mathbf{u} = 0",
    "incomp": r"\frac{D\rho}{Dt} = 0 \quad \Longleftrightarrow \quad \nabla \cdot \mathbf{u} = 0",
}

# One size per role. H key result, D standard display, C display in a column,
# T text size (3.2 / 2.8 / 2.4 for 32 / 28 / 24 px text), L label pinned in a diagram (2.8).
LEVELS = {
    5.0: "",
    4.4: "",
    4.0: "cont_c cont_nc",
    3.2: "incomp",
    2.8: "",
    2.4: "",
}

SCALE = {}
for _s, _ids in LEVELS.items():
    for _e in _ids.split():
        SCALE[_e] = _s
assert set(SCALE) <= set(EQS), set(SCALE) - set(EQS)
