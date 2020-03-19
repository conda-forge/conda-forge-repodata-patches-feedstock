import license_expression

mapping = {
    "AGPL-3.0-or-later": "AGPL",
    "AGPL-3.0-only": "AGPL",
    "AGPL-2.0-or-later": "AGPL",
    "AGPL-2.0-only": "AGPL",
    "GPL-3.0-or-later": "GPL",
    "GPL-3.0-only": "GPL",
    "GPL-2.0-or-later": "GPL",
    "GPL-2.0-only": "GPL",
    "LGPL-3.0-or-later": "LGPL",
    "LGPL-3.0-only": "LGPL",
    "LGPL-2.0-or-later": "LGPL",
    "LGPL-2.0-only": "LGPL",
    "BSD-3-Clause": "BSD",
    "BSD-2-Clause": "BSD",
    "MIT": "MIT",
    "Apache-2.0": "APACHE",
    "PSF-2.0": "PSF",
    "MPL-1.0": "MOZILLA",
    "MPL-1.1": "MOZILLA",
    "MPL-2.0": "MOZILLA",
    "MPL-2.0-no-copyleft-exception": "MOZILLA",
    "LicenseRef-Proprietary": "PROPRIETARY",
}

precedence = {
    ("BSD", "GPL"): "GPL",
    ("GPL", "MIT"): "GPL",
}

def get_license_family(license):
    licensing = license_expression.Licensing()
    family = None
    try:
        parsed_licenses_with_exception = licensing.license_symbols(
            license.strip(), decompose=False
        )
        for l in parsed_licenses_with_exception:
            if isinstance(l, license_expression.LicenseWithExceptionSymbol):
                license = l.license_symbol.key
            else:
                license = l.key
            family_new = mapping.get(license, None)
            if not family_new:
                return None
            if family is None:
                family = family_new
                continue
            pair = tuple(sorted([family_new, family]))
            family = precendence.get(pair, None)
            if not family:
                return None
    except license_expression.ExpressionError:
        return None
    return family
