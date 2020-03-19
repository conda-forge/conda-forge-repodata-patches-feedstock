import license_expression

mapping = {
    "GPL-2.0-or-later": "GPL",
    "BSD-3-Clause": "BSD",
    "MIT": "MIT",
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
